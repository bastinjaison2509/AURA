
import os
import json

from google import genai
from google.genai import types

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext

from ..config import config
from ..agent_utils import suppress_output_callback


# -------------------------------------------------------------------
# 1) Gemini client + config (API key based, NOT Vertex ADC)
# -------------------------------------------------------------------

# Use your existing GOOGLE_API_KEY from .env
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. "
        "Please add it to your .env or environment."
    )

# You can still reuse the same model name you stored in config.vision_model
VISION_MODEL = os.getenv("VERTEX_VISION_MODEL", config.vision_model)

client = genai.Client(
    api_key=GEMINI_API_KEY,
    # IMPORTANT: force non-Vertex mode even if GOOGLE_GENAI_USE_VERTEXAI is set
    vertexai=False,
)

# Default reference video: qsr_agent/data/assembly_reference.mp4
DEFAULT_VIDEO_PATH = os.getenv(
    "ASSEMBLY_REFERENCE_VIDEO",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # up from ai_checker_agent/
        "data",
        "assembly_reference.mp4",
    ),
)


# -------------------------------------------------------------------
# 2) Low-level helper that actually calls Gemini Vision
#    (keeps the tool signature simple for the LLM)
# -------------------------------------------------------------------
def _run_video_analysis(
    order_id: str,
    item_name: str,
    expected_ingredients: list[str],
    expected_addons: list[str],
    video_path: str = DEFAULT_VIDEO_PATH,
) -> dict:
    """
    Use Gemini vision to inspect the reference assembly video and
    infer which ingredients/addons are actually visible.

    Returns a dict like:
    {
      "status": "ok" | "error",
      "expected_ingredients": [...],
      "expected_addons": [...],
      "detected_ingredients": [...],
      "detected_addons": [...],
      "notes": "..."
    }
    """
    if not os.path.exists(video_path):
        return {
            "status": "error",
            "error_message": f"Reference video not found at '{video_path}'",
            "expected_ingredients": expected_ingredients,
            "expected_addons": expected_addons,
            "detected_ingredients": [],
            "detected_addons": [],
            "notes": "Video path missing on disk.",
        }

    with open(video_path, "rb") as f:
        video_bytes = f.read()

    # For small local video files (< 20MB) we can send bytes directly
    video_part = types.Part.from_bytes(
        data=video_bytes,
        mime_type="video/mp4",
    )

    prompt = (
        "You are a quality inspector for a quick-service restaurant.\n"
        f"Order ID: {order_id}\n"
        f"Item name: {item_name}\n\n"
        "You are given a reference assembly video that shows the *correct* way "
        "to assemble this menu item.\n\n"
        "TASK:\n"
        "1. Look at the final assembled item in the video.\n"
        "2. Based ONLY on what you can clearly see, determine which of the "
        "expected ingredients and addons actually appear.\n\n"
        f"Expected ingredients: {expected_ingredients}\n"
        f"Expected addons: {expected_addons}\n\n"
        "Return ONLY a JSON object with this exact shape:\n"
        "{\n"
        '  "detected_ingredients": ["..."],\n'
        '  "detected_addons": ["..."],\n'
        '  "notes": "short explanation, including any uncertainty or occlusions"\n'
        "}\n"
        "Do NOT include any extra keys or any text outside the JSON."
    )

    try:
        response = client.models.generate_content(
            model=VISION_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        video_part,
                        types.Part(text=prompt),
                    ],
                )
            ],
        )
    except Exception as e:
        # Any API/auth/network error becomes a clean tool-level error
        return {
            "status": "error",
            "error_message": f"Error calling Gemini Vision: {e}",
            "expected_ingredients": expected_ingredients,
            "expected_addons": expected_addons,
            "detected_ingredients": [],
            "detected_addons": [],
            "notes": "Exception in _run_video_analysis",
        }

    raw_text = (response.text or "").strip()

    # --- START FIX: Sanitize Markdown Code Blocks ---
    # Gemini 2.0 often wraps JSON in ```json ... ``` even when asked not to.
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        # Remove the first line (e.g., ```json)
        if lines:
            lines = lines[1:]
        # Remove the last line if it is just backticks
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()
    # --- END FIX ---

    try:
        data = json.loads(raw_text)
        # Normalize keys and add status + echo expected lists for the LLM
        return {
            "status": "ok",
            "expected_ingredients": expected_ingredients,
            "expected_addons": expected_addons,
            "detected_ingredients": data.get("detected_ingredients", []),
            "detected_addons": data.get("detected_addons", []),
            "notes": data.get("notes", ""),
        }
    except Exception as e:
        # Fallback if model returns non-JSON
        return {
            "status": "error",
            "error_message": f"Failed to parse JSON from model: {e}",
            "raw_response": raw_text[:500],
            "expected_ingredients": expected_ingredients,
            "expected_addons": expected_addons,
            "detected_ingredients": [],
            "detected_addons": [],
            "notes": "Parsing error in analyze_assembly_video",
        }


def analyze_assembly_video(
    order_id: str,
    tool_context: ToolContext,
) -> dict:
    """
    High-level tool for the AI Checker Agent.

    Parameters:
      order_id: The order_id to validate.
      tool_context: Provided by ADK. Contains session state, including:
        - state["order"]:
            Either:
              a) a dict like:
                 {
                   "order_id": "...",
                   "items": [...],
                   ...
                 }
              b) a JSON string with the same content
              c) a JSON string wrapped as {"order": {...}}
        - state["kitchen_plan"] or similar:
            Either dict or JSON string containing an "assembly" array.
    """
    state = tool_context.state or {}

    # ---- 1) Normalize `order` from state ----
    raw_order = state.get("order")

    order: dict = {}
    if isinstance(raw_order, dict):
        order = raw_order
    elif isinstance(raw_order, str):
        # Try to parse JSON from string
        try:
            parsed = json.loads(raw_order)
            if isinstance(parsed, dict):
                # Sometimes it's {"order": {...}}
                if "order" in parsed and isinstance(parsed["order"], dict):
                    order = parsed["order"]
                else:
                    order = parsed
        except Exception:
            # If parsing fails, leave as empty dict; we'll fall back later
            order = {}
    elif raw_order is None:
        order = {}
    else:
        # Unknown type; be defensive
        order = {}

    # ---- 2) Normalize `kitchen_plan` / load-balancer output from state ----
    raw_kitchen_plan = (
        state.get("kitchen_plan")
        or state.get("kitchen_load_plan")
        or state.get("station_output")
    )

    kitchen_plan: dict = {}
    if isinstance(raw_kitchen_plan, dict):
        kitchen_plan = raw_kitchen_plan
    elif isinstance(raw_kitchen_plan, str):
        try:
            parsed = json.loads(raw_kitchen_plan)
            if isinstance(parsed, dict):
                kitchen_plan = parsed
        except Exception:
            kitchen_plan = {}
    elif raw_kitchen_plan is None:
        kitchen_plan = {}
    else:
        kitchen_plan = {}

    # ---- 3) Derive item_name from order ----
    item_name = None
    items = order.get("items") or []
    if items:
        first_item = items[0]
        item_name = (
            first_item.get("name")
            or first_item.get("item_name")
            or first_item.get("item")
        )

    # ---- 4) Derive expected ingredients/addons from assembly plan ----
    expected_ingredients: list[str] = []
    expected_addons: list[str] = []

    assembly_blocks = kitchen_plan.get("assembly") or []
    for block in assembly_blocks:
        block_item = block.get("item")
        # In your sample, the assembly block uses `components` not `ingredients`
        # so we treat components as ingredients if `ingredients` missing.
        block_ingredients = (
            block.get("ingredients")
            or block.get("components")
            or []
        )
        block_addons = block.get("addons") or []

        if item_name and block_item == item_name:
            expected_ingredients = block_ingredients
            expected_addons = block_addons
            break

    # ---- 5) Fallbacks if order/assembly incomplete ----
    if not item_name:
        # Try to infer from assembly if order didn't have it
        if assembly_blocks:
            first_block = assembly_blocks[0]
            item_name = first_block.get("item", "unknown item")
            expected_ingredients = (
                first_block.get("ingredients")
                or first_block.get("components")
                or []
            )
            expected_addons = first_block.get("addons") or []
        else:
            item_name = "unknown item"

    if not order_id:
        order_id = order.get("order_id", "UNKNOWN_ORDER")

    # ---- 6) Delegate to low-level vision helper ----
    return _run_video_analysis(
        order_id=order_id,
        item_name=item_name,
        expected_ingredients=expected_ingredients,
        expected_addons=expected_addons,
    )


# -------------------------------------------------------------------
# 4) Tool: request_human_approval  (Human-in-the-loop stub)
#    - Called by the agent AFTER AI analysis
#    - You plug this into your UI / dashboard later
# -------------------------------------------------------------------
def request_human_approval(
    order_id: str,
    item_name: str,
    ai_assessment: dict,
) -> dict:
    """
    Human-in-the-loop approval hook.

    ADK will show this tool call in the trace / logs. In a real system you
    would push `ai_assessment` to your kitchen UI, Slack, or a moderation
    dashboard, and then have a human mark it APPROVED/REJECTED.

    For now this is a 'pending' stub:
    - It marks the check as needing human review.
    - Downstream agents can look at `approval_status`.
    """
    # You can add your own side-effects here:
    # - write to a JSON file
    # - call a webhook
    # - send a notification, etc.
    return {
        "order_id": order_id,
        "item_name": item_name,
        "approval_status": "PENDING",
        "message": (
            "Human approval required for assembly check. "
            "Review ai_assessment and update status in your backend/UI."
        ),
        "ai_assessment": ai_assessment,
    }


# -------------------------------------------------------------------
# 5) AI Checker Agent
#    - Uses tools above
#    - Reads state['order'] and state['kitchen_plan']
#    - Writes final JSON to state['assembly_check']
# -------------------------------------------------------------------
ai_checker_agent = Agent(
    # Use a text model here; vision is only used inside the tool
    model=config.critic_model,
    name="ai_checker_agent",
    description=(
        "Validates assembled food items by first running a vision-based "
        "check on the reference video and then triggering human approval."
    ),
    instruction="""
You are the AI Checker Agent responsible for validating food assembly.

HARD RULES (do not break these):
1. Your FIRST action in every run MUST be a tool call to `analyze_assembly_video`.
2. After you receive that tool result, you MUST call `request_human_approval`
   with your AI assessment.
3. Only AFTER both tools have been called may you produce the final JSON.

CONTEXT:
- The current order object is stored in session state under key "order".
- The kitchen plan / station breakdown (including the assembly block) is
  stored in state under a key like "station_split" (or similar).
- The `analyze_assembly_video` tool will automatically read these from state
  and return both expected and detected ingredients/addons.

TOOLS:
1) analyze_assembly_video(order_id: str)
   - Reads expected ingredients/addons from state and uses Gemini Vision
     on the reference assembly video to detect what is actually present.
2) request_human_approval(order_id: str, item_name: str, ai_assessment: dict)
   - Sends your assessment for a human-in-the-loop check.

YOUR FLOW:
1. Read "order" from the state.
   - If missing, create a FAIL assessment that says the order is missing
     and call `request_human_approval` immediately with that assessment.

2. Call analyze_assembly_video with:
   {
     "order_id": order["order_id"]
   }
   - Wait for the tool result.
   - Use `expected_ingredients`, `expected_addons`,
     `detected_ingredients`, `detected_addons`, and `notes`
     from the tool output.

3. Compute:
   - missing_ingredients = expected_ingredients - detected_ingredients
   - unexpected_items    = items in detected_ingredients or detected_addons
                           that were not expected.

4. Decide provisional status:
   - If missing_ingredients or unexpected_items -> provisional_status = "FAIL"
   - Otherwise -> provisional_status = "PASS"

5. Call request_human_approval with a compact ai_assessment:
   {
     "provisional_status": ...,
     "missing_ingredients": [...],
     "unexpected_items": [...],
     "notes": "...",
   }

6. Use the tool response's approval_status in your final JSON:
   {
     "order_id": "...",
     "item_name": "...",
     "status": "PASS" | "FAIL" | "HOLD",
     "missing_ingredients": [...],
     "unexpected_items": [...],
     "notes": "short explanation",
     "requires_human_review": true/false,
     "human_approval": {
       "message": "short note for the kitchen/admin"
     }
   }

RULES:
- If approval_status is not "APPROVED", set requires_human_review=true
  and status MUST be "HOLD" or "FAIL" (never PASS).
- If the vision tool returns status="error", treat it as:
  status="FAIL", requires_human_review=true, and explain in notes.
- Do NOT guess or fake tool results.
- Do NOT output anything that is not valid JSON.
- Do NOT include tool call traces in the final JSON.
""",
    tools=[
        FunctionTool(analyze_assembly_video),
        FunctionTool(request_human_approval),
    ],
    output_key="assembly_check",
    after_agent_callback=suppress_output_callback,
)
