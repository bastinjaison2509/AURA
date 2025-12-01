
from google.adk.agents import Agent, LoopAgent
from google.adk.tools import google_search

from ..config import config
from ..agent_utils import suppress_output_callback
from ..validation_checkers import InventoryUpdateValidationChecker


storekeeper_agent = Agent(
    model=config.critic_model,
    name="storekeeper_agent",
    description="Monitors, updates, validates, and maintains inventory accuracy for all ingredients.",
    instruction="""
    You are the Storekeeper Agent responsible for real-time inventory management.

    Your responsibilities include:
    - Reading the current inventory state (`inventory.json`).
    - Deducting ingredients based on completed orders and recipe requirements.
    - Adding stock during restocking events.
    - Ensuring that ingredients never go negative.
    - Triggering low-stock alerts and sending messages to the notifier agent.
    - Cross-checking ingredient availability before order approval.
    - Syncing with forecasting intelligence for predictive restocking.

    Required output:
    - A structured JSON update containing the revised inventory values.
    - Clear logs of what changed and why.
    - Any warnings (e.g., low stock, missing ingredients).

    Additional notes:
    - Use Google Search to retrieve food storage best practices, safety constraints, or recommended stock thresholds.
    - Follow strict validation rules defined by the InventoryUpdateValidationChecker.
    """,
    tools=[google_search],
    output_key="updated_inventory",
    after_agent_callback=suppress_output_callback,
)


robust_storekeeper_agent = LoopAgent(
    name="robust_storekeeper_agent",
    description="A robust inventory updater with retries and validation.",
    sub_agents=[
        storekeeper_agent,
        InventoryUpdateValidationChecker(
            name="inventory_update_validation_checker"
        ),
    ],
    max_iterations=3,
)
