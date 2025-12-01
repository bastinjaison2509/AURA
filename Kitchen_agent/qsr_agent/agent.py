# blogger_agent/agent.py

import datetime
import asyncio
import logging
from typing import Optional, Dict, Any  # ✅ extended types

from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.tools import FunctionTool
from google.adk.runners import InMemoryRunner

# ✅ Guardrail-related imports
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

# ✅ Tool guardrail imports (correct signature)
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool

from .config import config
from .sub_agents import (
    order_loader_agent,
    queuing_agent,
    kitchen_load_balancer_agent,
    ai_checker_agent,
    notifier_agent,
    delivery_agent,
    forecasting_agent,
    robust_storekeeper_agent,
    robust_loyalty_agent,
    robust_feedback_agent,
    robust_refinement_agent,
)
from .tools import get_order_details, update_order_status, fetch_inventory, save_system_logs

# -------------------------------------------------------------------
# Logger for guardrails & API
# -------------------------------------------------------------------
logger = logging.getLogger("qsr_guardrails")

# -------------------------------------------------------------------
# Guardrail 1: Input safety (before_model_callback)
# -------------------------------------------------------------------
def qsr_input_guardrail(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    agent_name = callback_context.agent_name

    # --- 1) Get latest user message text ---
    last_user_text = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts:
                if content.parts[0].text:
                    last_user_text = content.parts[0].text
                    break

    upper_text = last_user_text.upper()
    
    # --- 2) Keyword Check (Keep as is) ---
    banned_keywords = ["DROP TABLE", "DELETE FROM", "HACK", "EXPLODE"]
    if any(bad in upper_text for bad in banned_keywords):
        # ... (Existing blocking logic) ...
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Unsafe input detected.")]
            )
        )

    # --- 3) SMART QUANTITY CHECK (FIXED) ---
    import re

    # Step A: Remove Prices (e.g., $12.99, $5) to avoid counting cents as quantity
    clean_text = re.sub(r'\$\d+(?:\.\d+)?', '', last_user_text)
    
    # Step B: Remove Time (e.g., 35 minutes) 
    clean_text = re.sub(r'\d+\s*(?:min|mins|minutes|hour)', '', clean_text, flags=re.IGNORECASE)

    # Step C: Find remaining numbers (which are likely quantities)
    numbers = re.findall(r"\d+", clean_text)
    
    if numbers:
        max_n = max(int(n) for n in numbers)
        
        # Log what we found for debugging
        logger.debug(
            "[Guardrail] Cleaned text: '%s' | Extracted nums: %s | Max: %d", 
            clean_text, numbers, max_n
        )

        if max_n > 50:
            logger.info(
                "[Guardrail] Blocking large order | max=%d", max_n
            )
            # Block the order
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=(
                                f"This order quantity ({max_n}) seems unusually large. "
                                "Please confirm or split it."
                            )
                        )
                    ],
                )
            )

    return None


# -------------------------------------------------------------------
# Guardrail 2: Tool safety (before_tool_callback)
#   - Runs BEFORE any tool is executed
#   - Can block unsafe tool calls, e.g. invalid order status
#   NOTE: signature must be (tool, args, tool_context)
# -------------------------------------------------------------------
def qsr_tool_guardrail(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Inspect tool name + args before execution.

    Return:
      - dict  -> block the tool and return this dict as the tool "result"
      - None  -> allow the tool to execute normally
    """
    agent_name = tool_context.agent_name
    tool_name = tool.name

    logger.debug(
        "[Guardrail][before_tool] agent=%s | tool=%s | args=%s",
        agent_name,
        tool_name,
        args,
    )

    # Example: validate order status for update_order_status tool
    if tool_name == "update_order_status":
        new_status = args.get("status")
        allowed_statuses = {"QUEUED", "PREPARING", "READY", "COMPLETED"}

        if new_status not in allowed_statuses:
            logger.warning(
                "[Guardrail][before_tool] Blocking tool call | agent=%s | tool=%s | "
                "invalid_status=%r | allowed=%s",
                agent_name,
                tool_name,
                new_status,
                sorted(allowed_statuses),
            )

            # You can also stash into tool_context.state if you want:
            # tool_context.state["guardrail_blocked_tool"] = {...}

            return {
                "status": "error",
                "error_message": (
                    f"'{new_status}' is not a valid order status. "
                    f"Allowed values: {sorted(allowed_statuses)}"
                ),
                "blocked_by": "qsr_tool_guardrail",
                "agent": agent_name,
                "tool": tool_name,
            }

    logger.debug(
        "[Guardrail][before_tool] Tool call allowed | agent=%s | tool=%s",
        agent_name,
        tool_name,
    )
    # No guardrail triggered -> allow tool execution
    return None


# -------------------------------------------------------------------
# 1) SEQUENTIAL PIPELINE: order_flow
#    order_loader_agent -> queuing -> KLB -> AI checker -> notifier -> delivery
# -------------------------------------------------------------------
order_flow = SequentialAgent(
    name="order_flow",
    description=(
        "Sequential pipeline for processing an order: "
        "load order -> queue -> kitchen load balance -> AI check -> notify -> delivery."
    ),
    sub_agents=[
        order_loader_agent,          # 0. load full order into state["order"]
        queuing_agent,               # 1. uses state["order"]
        kitchen_load_balancer_agent, # 2. uses state["order"]
        ai_checker_agent,          # 3. uses state["order"]  (you commented this out)
        notifier_agent,              # 4. uses state["order"]
        delivery_agent,              # 5. uses state["order"]
    ],
)


# -------------------------------------------------------------------
# 2) PARALLEL BACKGROUND ENRICHMENT
# -------------------------------------------------------------------
background_enrichment = ParallelAgent(
    name="background_enrichment",
    description=(
        "Parallel background tasks: forecasting, inventory, "
        "loyalty updates, feedback aggregation, refinement."
    ),
    sub_agents=[
        forecasting_agent,
        robust_storekeeper_agent,
        robust_loyalty_agent,
        robust_feedback_agent,
        robust_refinement_agent,
    ],
)


# -------------------------------------------------------------------
# 3) ROOT LLM AGENT
# -------------------------------------------------------------------
root_agent = Agent(
    name="kitchen_agent",
    model=config.worker_model,
    description="Main controller for the automated AI restaurant ordering system.",
    instruction=f"""
    You are Kitchen Agent, orchestrating sub-agents to process customer orders.

    1. For ANY user message that mentions or implies an order:
       - Rely on the SequentialAgent `order_flow`.
       - The first step, `order_loader_agent`, will ALWAYS produce a shared `order`
         object in the session state under key "order".
       - All subsequent agents in `order_flow` MUST use that `order` and not ask the user
         to re-specify details.

    2. Run `background_enrichment` in parallel to handle:
       - forecasting_agent
       - robust_storekeeper_agent
       - robust_loyalty_agent
       - robust_feedback_agent
       - robust_refinement_agent

    3. Use the provided tools when needed:
       - get_order_details(order_id) to fetch orders from storage
       - update_order_status(...) to move through QUEUED -> PREPARING -> ...
       - fetch_inventory() to understand ingredient availability
       - save_system_logs(...) to log important pipeline events

    The final combined reasoning and status of the pipeline should be written
    to the "kitchen_agent_output" state key.

    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    """,



    # ... rest of your config

    sub_agents=[
        order_flow,
        background_enrichment,
    ],
    tools=[
        FunctionTool(get_order_details),
        FunctionTool(update_order_status),
        FunctionTool(fetch_inventory),
        FunctionTool(save_system_logs),
    ],
    output_key="kitchen_agent_output",

    # 🔒 Attach guardrails
    # before_model_callback=qsr_input_guardrail,
    before_tool_callback=qsr_tool_guardrail,
)



# # -------------------------------------------------------------------
# # 4) RUNNER + process_order()
# # -------------------------------------------------------------------
# runner = InMemoryRunner(agent=root_agent)


# def process_order(user_message: str):
#     """
#     Run the kitchen agent via InMemoryRunner and return a JSON-serializable response.
#     """
#     logger.info("[API] process_order called | user_message=%r", user_message)

#     try:
#         result = asyncio.run(runner.run_debug(user_message))

#         if hasattr(result, "model_dump"):
#             dumped = result.model_dump()
#             logger.debug("[API] process_order result keys=%s", list(dumped.keys()))
#             return dumped

#         logger.debug(
#             "[API] process_order raw result type=%s repr=%r",
#             type(result),
#             result,
#         )
#         return result
#     except Exception as e:
#         logger.exception("[API] process_order failed with error: %s", e)
#         return {"error": str(e)}

# ... (imports remain the same)

# -------------------------------------------------------------------
# 4) RUNNER + process_order()
# -------------------------------------------------------------------
runner = InMemoryRunner(agent=root_agent)

# CHANGE 1: Add 'async' keyword here
async def process_order(user_message: str):
    """
    Run the kitchen agent via InMemoryRunner and return a JSON-serializable response.
    """
    logger.info("[API] process_order called | user_message=%r", user_message)

    try:
        # CHANGE 2: Remove 'asyncio.run()' and use 'await' directly
        # OLD: result = asyncio.run(runner.run_debug(user_message))
        result = await runner.run_debug(user_message)

        if hasattr(result, "model_dump"):
            dumped = result.model_dump()
            logger.debug("[API] process_order result keys=%s", list(dumped.keys()))
            return dumped

        logger.debug(
            "[API] process_order raw result type=%s repr=%r",
            type(result),
            result,
        )
        return result
    except Exception as e:
        logger.exception("[API] process_order failed with error: %s", e)
        return {"error": str(e)}