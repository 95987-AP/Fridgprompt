"""Statistics and insights generation."""

from .models import TRAITS
from .storage import get_trait_stats


def generate_insights() -> dict:
    """Generate insights from stored prompts and traits."""
    stats = get_trait_stats()

    if stats["rated_prompts"] < 5:
        return {
            "ready": False,
            "message": f"Need at least 5 rated prompts for insights. You have {stats['rated_prompts']}.",
            "stats": stats,
        }

    high_traits = stats["high_rated_traits"]
    low_traits = stats["low_rated_traits"]

    # Find traits that appear much more in high-rated prompts
    good_patterns = []
    bad_patterns = []
    suggestions = []

    for trait in TRAITS:
        high_pct = high_traits.get(trait, 0)
        low_pct = low_traits.get(trait, 0)

        if high_pct >= 70:
            good_patterns.append((trait, high_pct))

        if low_pct >= 60 and high_pct < 40:
            bad_patterns.append((trait, low_pct))

        # Generate suggestions
        if high_pct >= 70 and low_pct < 40:
            suggestions.append(
                f"Keep using '{trait.replace('_', ' ')}' - it's in {high_pct:.0f}% of your best prompts."
            )
        elif low_pct >= 60 and high_pct < 40:
            suggestions.append(
                f"Missing '{trait.replace('_', ' ')}' correlates with lower ratings."
            )
        elif high_pct < 30 and trait in ["shows_example", "breaks_down_task"]:
            suggestions.append(
                f"Try adding '{trait.replace('_', ' ')}' more often - you rarely use it."
            )

    return {
        "ready": True,
        "stats": stats,
        "good_patterns": sorted(good_patterns, key=lambda x: -x[1]),
        "bad_patterns": sorted(bad_patterns, key=lambda x: -x[1]),
        "suggestions": suggestions[:5],  # Top 5 suggestions
    }


def format_trait_bar(percentage: float, width: int = 20) -> str:
    """Format a percentage as an ASCII bar."""
    filled = int(percentage / 100 * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {percentage:.0f}%"
