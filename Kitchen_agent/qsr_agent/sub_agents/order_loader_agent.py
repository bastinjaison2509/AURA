# blogger_agent/sub_agents/order_loader_agent.py

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from ..config import config
from ..agent_utils import suppress_output_callback
from ..tools import get_order_details


order_loader_agent = Agent(
    model=config.worker_model,
    name="order_loader_agent",
    description="Loads full order details into shared state based on an order ID or natural language input.",
    instruction="""
    You are the first step in the Kitchen Agent pipeline.

    INPUT:
    - The user message may contain an explicit order ID like "ORD001"
      OR a natural-language instruction like "create 2 chicken burgers for table 5".

    BEHAVIOR:

    1. If the user message contains an explicit order ID (e.g. 'ORD001'):
       - Extract that ID.
       - Call the `get_order_details` tool with that order_id.
       - If the order is found, your ONLY output should be a JSON object:
         {
           "order": <full_order_object>
         }

    2. If the message does NOT contain an existing ID but is a natural-language order:
       - Parse items, quantities, table, and delivery_mode.
       - Construct a new synthetic order object like:
         {
           "order_id": "TEMP-<some-id-or-timestamp>",
           "customer_id": "<if available or 'UNKNOWN'>",
           "table": <table_number_or_null>,
           "time": "<current-ISO-timestamp>",
           "items": [
             {"name": "...", "quantity": 2, "addons": ["..."]}
           ],
           "status": "QUEUED",
           "delivery_mode": "table" | "pickup" | "staff_delivery",
           "loyalty_points_awarded": 0
         }
       - Wrap it as:
         { "order": <built_order_object> }

    3. Do NOT ask the user for missing fields unless absolutely necessary.
       Prefer to infer reasonable defaults.

    VERY IMPORTANT:
    - Your ONLY output must be a JSON object with top-level key 'order'.
    - This 'order' will be used by all downstream agents in the sequence.
    """,
    tools=[FunctionTool(get_order_details)],
    # This makes the returned value appear in the shared state as state["order"]
    output_key="order",
    after_agent_callback=suppress_output_callback,
)

