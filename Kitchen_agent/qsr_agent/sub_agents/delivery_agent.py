
from google.adk.agents import Agent

from ..config import config
from ..agent_utils import suppress_output_callback


delivery_agent = Agent(
    model=config.worker_model,
    name="delivery_agent",
    description="classifies delivery method: pickup, staff-table-delivery, or drone delivery.",
    instruction="""
    You are the Delivery Agent responsible fordetermining the correct delivery mode.

    INPUT FIELDS YOU RECEIVE:
    {
      "qr_data": "...", 
      "order_id": "...",  
      "delivery_preference": "pickup | table | drone",
      "table_number": "...", 
      "user_type": "customer | staff | vip | automated"
    }

    YOUR JOB:
  

    1. Determine the correct delivery category:
       - "pickup" → customer collects directly
       - "table_delivery" → staff delivers to a table
       - "drone_delivery" → drone dispatch required

    2. Output a structured JSON response:
       {
         "order_id": "...",
         "delivery_mode": "pickup | table_delivery | drone_delivery",
         "table_number": "...",   # null if not applicable,if table numver is not in input give random number
       }

    RULES:
    - If drone delivery is chosen but table_number exists → ignore table number.
    - Your response must NOT include extra text outside JSON.
    """,
    output_key="delivery_assignment",
    after_agent_callback=suppress_output_callback,
)
