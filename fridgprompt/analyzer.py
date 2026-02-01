"""Trait analyzer using local LLM (Ollama)."""

import json
from typing import Optional

from .models import TRAITS, Prompt

# Default model - can be changed to any Ollama model
DEFAULT_MODEL = "qwen2.5:7b"


def build_analysis_prompt(prompt_content: str) -> str:
    """Build the prompt for trait analysis."""
    traits_list = "\n".join(
        f"- {name}: {description}" for name, description in TRAITS.items()
    )

    return f"""Analyze this vibe coding prompt and identify which traits are present.

TRAITS TO DETECT:
{traits_list}

PROMPT TO ANALYZE:
\"\"\"
{prompt_content}
\"\"\"

Return ONLY a JSON object with trait names as keys and boolean values.
Example: {{"clear_goal": true, "gives_context": false, "references_files": true, ...}}

Include ALL traits in your response. Be accurate - only mark true if the trait is clearly present.

JSON response:"""


def analyze_prompt_with_ollama(
    prompt: Prompt,
    model: str = DEFAULT_MODEL,
) -> dict[str, bool]:
    """Analyze a prompt using Ollama and return detected traits."""
    try:
        import ollama

        analysis_prompt = build_analysis_prompt(prompt.content)

        response = ollama.generate(
            model=model,
            prompt=analysis_prompt,
            options={
                "temperature": 0.1,  # Low temp for consistent analysis
                "num_predict": 500,
            },
        )

        response_text = response["response"].strip()

        # Try to extract JSON from response
        # Handle cases where model adds extra text
        if "{" in response_text:
            start = response_text.index("{")
            end = response_text.rindex("}") + 1
            json_str = response_text[start:end]
            traits = json.loads(json_str)

            # Ensure all traits are present
            result = {}
            for trait_name in TRAITS:
                result[trait_name] = bool(traits.get(trait_name, False))

            return result

    except ImportError:
        raise RuntimeError(
            "Ollama package not installed. Run: pip install ollama"
        )
    except Exception as e:
        raise RuntimeError(f"Analysis failed: {e}")

    # Default to all False if parsing fails
    return {trait: False for trait in TRAITS}


def analyze_prompt_simple(prompt: Prompt) -> dict[str, bool]:
    """Simple rule-based analysis (fallback when no LLM available)."""
    content = prompt.content.lower()

    return {
        "clear_goal": any(
            word in content
            for word in ["add", "create", "build", "fix", "make", "implement", "want"]
        ),
        "gives_context": any(
            word in content
            for word in ["using", "project", "app", "this is", "we have", "i have"]
        ),
        "references_files": any(
            ext in content
            for ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".html", "component", "file", "function"]
        ),
        "shows_error": any(
            word in content
            for word in ["error", "exception", "failed", "crash", "bug", "issue", "typeerror", "syntaxerror"]
        ),
        "describes_behavior": any(
            word in content
            for word in ["should", "when", "if clicked", "displays", "shows", "returns", "behave"]
        ),
        "sets_constraints": any(
            word in content
            for word in ["simple", "only", "don't use", "without", "keep it", "no external", "limit"]
        ),
        "breaks_down_task": any(
            word in content
            for word in ["first", "then", "step", "1.", "2.", "finally", "after that"]
        ),
        "shows_example": any(
            word in content
            for word in ["example", "like this", "such as", "e.g.", "for instance", '{"', "```"]
        ),
        "explains_why": any(
            word in content
            for word in ["because", "since", "reason", "so that", "in order to", "need to"]
        ),
        "specifies_negative": any(
            word in content
            for word in ["don't", "do not", "avoid", "never", "without", "not include", "skip"]
        ),
    }


def analyze_prompt(
    prompt: Prompt,
    use_llm: bool = True,
    model: str = DEFAULT_MODEL,
) -> dict[str, bool]:
    """Analyze a prompt for traits.

    Args:
        prompt: The prompt to analyze
        use_llm: Whether to use LLM (True) or simple rules (False)
        model: Ollama model to use

    Returns:
        Dict mapping trait names to boolean (present/absent)
    """
    if use_llm:
        try:
            return analyze_prompt_with_ollama(prompt, model)
        except RuntimeError:
            # Fall back to simple analysis
            pass

    return analyze_prompt_simple(prompt)
