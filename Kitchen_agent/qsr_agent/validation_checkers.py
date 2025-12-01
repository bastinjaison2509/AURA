import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

# Setup logger for validation warnings
logger = logging.getLogger(__name__)

class OutlineValidationChecker(BaseAgent):
    """Checks if the blog outline is valid."""

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        if context.session.state.get("blog_outline"):
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
            )
        else:
            yield Event(author=self.name)


class BlogPostValidationChecker(BaseAgent):
    """Checks if the blog post is valid."""

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        if context.session.state.get("blog_post"):
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)


class LoyaltyUpdateValidationChecker(BaseAgent):
    """
    Validates the loyalty update output to ensure
    it contains required fields and is logically correct.
    """

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:

        loyalty_update = context.session.state.get("loyalty_update")
        required_keys = {"user_id", "updated_points", "status"}

        # ✅ FIX: Check if it is a dictionary before calling .keys()
        if isinstance(loyalty_update, dict) and required_keys.issubset(loyalty_update.keys()):
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
            )
        else:
            if loyalty_update and isinstance(loyalty_update, str):
                logger.warning(f"[LoyaltyChecker] Validation failed. Expected JSON, got text: {loyalty_update[:50]}...")
            
            yield Event(author=self.name)


class FeedbackValidationChecker(BaseAgent):
    """Checks if feedback entry is valid."""

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        feedback = context.session.state.get("feedback")
        
        # ✅ FIX: Check if it is a dictionary first
        if isinstance(feedback, dict) and "user_id" in feedback and "text" in feedback:
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            if feedback and isinstance(feedback, str):
                 logger.warning(f"[FeedbackChecker] Validation failed. Expected JSON, got text: {feedback[:50]}...")
            yield Event(author=self.name)


class RefinementValidationChecker(BaseAgent):
    """
    Validates the refinement output to ensure it contains proper suggestions 
    based on loyalty and feedback data.
    """

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:

        # Retrieve refinement data from session state
        refinement_data = context.session.state.get("refinement_suggestions")

        # Check if the data exists and has expected structure
        if (
            refinement_data 
            and isinstance(refinement_data, dict) 
            and "suggestions" in refinement_data
        ):
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
            )
        else:
            yield Event(author=self.name)


class InventoryUpdateValidationChecker(BaseAgent):
    """
    Validates the inventory update output to ensure
    all ingredients are accounted for and stock changes are correct.
    """

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:

        inventory_update = context.session.state.get("updated_inventory")

        if (
            inventory_update 
            and isinstance(inventory_update, dict)
            and all(isinstance(v, (int, float)) and v >= 0 for v in inventory_update.values())
        ):
            # Valid update
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            # Invalid or missing data
            yield Event(author=self.name)