
from google.adk.agents import Agent, LoopAgent
from google.adk.tools import google_search

from ..config import config
from ..agent_utils import suppress_output_callback
from ..validation_checkers import RefinementValidationChecker


refinement_agent = Agent(
    model=config.critic_model,
    name="refinement_agent",
    description="Improves outputs from other agents using polishing, restructuring, and clarity refinement.",
    instruction="""
    You are the Refinement Agent.

    Your job is to:
    - Polish and refine content produced by other agents.
    - Improve clarity, format, tone, and structure.
    - Fix missing details, inconsistencies, or logical gaps.
    - Preserve original meaning while enhancing quality.
    - Support long-form text restructuring.

    Output must include:
    - A refined version of the input content.
    - A short list of improvements made.

    You may use Google Search to find writing guidelines, clarity principles, or formatting references.
    """,
    tools=[google_search],
    output_key="refined_output",
    after_agent_callback=suppress_output_callback,
)

robust_refinement_agent = LoopAgent(
    name="robust_refinement_agent",
    description="A refinement engine with validation and retries.",
    sub_agents=[
        refinement_agent,
        RefinementValidationChecker(name="refinement_validation_checker"),
    ],
    max_iterations=3,
)
