
from google.adk.agents import Agent, LoopAgent
from google.adk.tools import google_search

from ..config import config
from ..agent_utils import suppress_output_callback
from ..validation_checkers import FeedbackValidationChecker


feedback_agent = Agent(
    model=config.critic_model,
    name="feedback_agent",
    description="Analyzes customer feedback and categorizes sentiment, issues, and improvement areas.",
    instruction="""
    You are the Feedback Agent.

    Responsibilities:
    - Analyze raw customer feedback.
    - Identify sentiment (positive, neutral, negative).
    - Tag categories (food quality, delay, staff, price, cleanliness, etc.)
    - Detect actionable issues for service improvement.
    - Summarize insights clearly.

    Required output:
    - A structured JSON with scores, tags, and recommendations.
    - A human-readable summary.

    You may use Google Search to understand restaurant feedback trends and best practices.
    """,
    tools=[google_search],
    output_key="feedback_analysis",
    after_agent_callback=suppress_output_callback,
)

robust_feedback_agent = LoopAgent(
    name="robust_feedback_agent",
    description="A feedback analyzer wrapped with validation and retry logic.",
    sub_agents=[
        feedback_agent,
        FeedbackValidationChecker(name="feedback_validation_checker"),
    ],
    max_iterations=3,
)
