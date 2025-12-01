
from google.adk.agents import Agent, LoopAgent
from google.adk.tools import google_search

from ..config import config
from ..agent_utils import suppress_output_callback
from ..validation_checkers import LoyaltyUpdateValidationChecker


loyalty_agent = Agent(
    model=config.critic_model,
    name="loyalty_agent",
    description="Manages customer loyalty points, rewards, and tier progress.",
    instruction="""
    You are the Loyalty Agent responsible for:
    - Updating loyalty points after orders.
    - Awarding rewards, discounts, or tier upgrades.
    - Evaluating customer history and behaviour.
    - Ensuring loyalty values never become inconsistent.
    - Generating alerts for reward unlocking.

    Required output:
    - A structured JSON containing updated loyalty data.
    - Any triggered reward events.
    - Logs on what changed and why.

    You may use Google Search to reference standard loyalty reward practices.
    """,
    tools=[google_search],
    output_key="loyalty_update",
    after_agent_callback=suppress_output_callback,
)

robust_loyalty_agent = LoopAgent(
    name="robust_loyalty_agent",
    description="A reliability-enhanced loyalty updater with validation retries.",
    sub_agents=[
        loyalty_agent,
        LoyaltyUpdateValidationChecker(name="loyalty_update_validation_checker"),
    ],
    max_iterations=3,
)
