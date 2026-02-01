"""Data models for Fridgprompt."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Trait definitions for vibe coding prompts
TRAITS = {
    "clear_goal": "States what you want built or fixed",
    "gives_context": "Explains the project or situation",
    "references_files": "Points to specific files or functions",
    "shows_error": "Includes error message or logs",
    "describes_behavior": "Explains what should happen",
    "sets_constraints": "Limits scope or style",
    "breaks_down_task": "Splits into steps or parts",
    "shows_example": "Provides sample input/output",
    "explains_why": "Gives reasoning or motivation",
    "specifies_negative": "Says what NOT to do",
}


@dataclass
class Prompt:
    """A stored prompt with metadata."""

    id: Optional[int] = None
    content: str = ""
    outcome: Optional[str] = None
    rating: Optional[int] = None
    model: Optional[str] = None
    task_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)
    traits: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class InsightStats:
    """Statistics for prompt insights."""

    total_prompts: int = 0
    rated_prompts: int = 0
    avg_rating: float = 0.0
    trait_frequency_high: dict[str, float] = field(default_factory=dict)
    trait_frequency_low: dict[str, float] = field(default_factory=dict)
