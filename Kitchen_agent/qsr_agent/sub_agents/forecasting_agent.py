
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from ..config import config
from ..agent_utils import suppress_output_callback
from ..tools import run_prophet_forecast


forecasting_agent = Agent(
    model=config.worker_model,
    name="forecasting_agent",
    description="Uses Prophet to forecast demand and compute preparation requirements by comparing previous and current predictions.",
    instruction="""
    You are the Forecasting Agent for an AI automated restaurant system.

    INPUT YOU RECEIVE:
    {
      "historical_sales": [...],     # list of {timestamp, quantity}
      "previous_forecast": [...],    # last cycle predicted values
      "limit_factor": float,         # e.g., 0.85 (to prevent overstock)
      "item_name": "..."
    }

    YOUR RESPONSIBILITIES:
    1. Call the tool `run_prophet_forecast`. 
       - You do NOT need to provide the 'data' argument; the tool will load 
         historical sales automatically from the database.
       - Simply call `run_prophet_forecast(periods=7)`.

    2. Compare:
       - previous_forecast
       - new current forecast

    3. Apply `limit_factor`:
         final_required = min(predicted_value, predicted_value * limit_factor)

    4. Produce the final structured JSON output:
       {
         "item_name": "...",
         "previous_forecast": [...],
         "current_forecast": [...],
         "recommended_preparation": number,
         "notes": "short explanation"
       }

    RULES:
    - Output ONLY JSON.
    - No additional commentary.
    - Be consistent and concise.
    """,
    tools=[
        FunctionTool(run_prophet_forecast),
    ],
    output_key="forecast_output",
    after_agent_callback=suppress_output_callback,
)
