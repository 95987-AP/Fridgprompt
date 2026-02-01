"""CLI interface for Fridgprompt."""

import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from . import __version__
from .models import Prompt, TRAITS
from .storage import (
    init_db,
    add_prompt,
    get_prompt,
    list_prompts,
    search_prompts,
    rate_prompt,
    save_traits,
    get_prompts_for_analysis,
    get_all_tags,
)
from .analyzer import analyze_prompt, DEFAULT_MODEL
from .stats import generate_insights, format_trait_bar

console = Console()

# ASCII Art Banner - Simple and clean
BANNER_LOGO = """
   _____ ____  ___ ____   ____ ____  ____   ___  __  __ ____ _____
  |  ___|  _ \\|_ _|  _ \\ / ___|  _ \\|  _ \\ / _ \\|  \\/  |  _ \\_   _|
  | |_  | |_) || || | | | |  _| |_) | |_) | | | | |\\/| | |_) || |
  |  _| |  _ < | || |_| | |_| |  __/|  _ <| |_| | |  | |  __/ | |
  |_|   |_| \\_\\___|____/ \\____|_|   |_| \\_\\\\___/|_|  |_|_|    |_|
"""

BANNER_TAGLINE = "A prompt vault for vibe coders"

FRIDGE_ART = """[cyan]
    ┌─────────────────┐
    │  ┌───────────┐  │
    │  │ [bold yellow]★[/bold yellow] prompts │  │
    │  │  [dim]rated[/dim]   │  │
    │  └───────────┘  │
    │─────────────────│
    │  ┌───────────┐  │
    │  │ [bold green]✓[/bold green] traits  │  │
    │  │ [dim]analyzed[/dim] │  │
    │  └───────────┘  │
    │  ┌───────────┐  │
    │  │ [bold magenta]◆[/bold magenta] insights│  │
    │  │ [dim]patterns[/dim] │  │
    │  └───────────┘  │
    └────────□────────┘
[/cyan]"""

MINI_FRIDGE = "[cyan]┌─┐[/cyan]\n[cyan]│[bold yellow]>[/bold yellow]│[/cyan]\n[cyan]└─┘[/cyan]"


def show_banner():
    """Display the banner."""
    console.print(f"[bold cyan]{BANNER_LOGO}[/bold cyan]")
    console.print(f"[dim]        {BANNER_TAGLINE}[/dim]\n")


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx):
    """Fridgprompt - A prompt vault for vibe coders.

    Store, rate, and analyze your prompts to discover what makes them work.
    """
    init_db()
    if ctx.invoked_subcommand is None:
        show_banner()
        console.print(f"  [dim]v{__version__}[/dim]  Type [bold]fridgprompt --help[/bold] for commands\n")


@main.command()
@click.option("-m", "--model", help="Model used (e.g., claude-4, gpt-4)")
@click.option("-t", "--task-type", help="Task type (e.g., feature, bugfix, refactor)")
@click.option("--tags", help="Comma-separated tags")
@click.argument("content", required=False)
def add(content: str, model: str, task_type: str, tags: str):
    """Add a new prompt to the vault.

    You can provide the prompt directly, via stdin, or interactively.

    Examples:
        fridgprompt add "Fix the login bug"
        fridgprompt add -m claude-4 -t bugfix --tags "auth,react"
        cat prompt.txt | fridgprompt add
    """
    # Get content from argument, stdin, or interactive
    if content:
        prompt_content = content
    elif not sys.stdin.isatty():
        prompt_content = sys.stdin.read().strip()
    else:
        console.print("[bold]Enter your prompt[/bold] (Ctrl+D when done):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        prompt_content = "\n".join(lines)

    if not prompt_content:
        console.print("[red]No prompt content provided.[/red]")
        raise SystemExit(1)

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # Interactive prompts for missing info
    if not model:
        model = console.input("[dim]Model used (optional):[/dim] ").strip() or None

    if not task_type:
        task_type = console.input("[dim]Task type (optional):[/dim] ").strip() or None

    if not tag_list:
        tags_input = console.input("[dim]Tags, comma-separated (optional):[/dim] ").strip()
        if tags_input:
            tag_list = [t.strip() for t in tags_input.split(",")]

    prompt = Prompt(
        content=prompt_content,
        model=model,
        task_type=task_type,
        tags=tag_list,
    )

    prompt_id = add_prompt(prompt)
    console.print(f"[green]Saved as #{prompt_id}[/green]")


@main.command("list")
@click.option("--tag", help="Filter by tag")
@click.option("--rating", type=int, help="Filter by rating (1-5)")
@click.option("-n", "--limit", default=10, help="Number of prompts to show")
def list_cmd(tag: str, rating: int, limit: int):
    """List stored prompts."""
    prompts = list_prompts(tag=tag, rating=rating, limit=limit)

    if not prompts:
        console.print("[dim]No prompts found.[/dim]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Prompt", style="white", max_width=50)
    table.add_column("Rating", justify="center", width=8)
    table.add_column("Tags", style="blue", max_width=20)
    table.add_column("Model", style="dim", max_width=12)

    for p in prompts:
        # Truncate content
        content_preview = p.content[:47] + "..." if len(p.content) > 50 else p.content
        content_preview = content_preview.replace("\n", " ")

        rating_str = "★" * p.rating + "☆" * (5 - p.rating) if p.rating else "[dim]--[/dim]"
        tags_str = ", ".join(p.tags[:3]) if p.tags else ""

        table.add_row(
            str(p.id),
            content_preview,
            rating_str,
            tags_str,
            p.model or "",
        )

    console.print(table)


@main.command()
@click.argument("prompt_id", type=int)
def show(prompt_id: int):
    """Show details of a specific prompt."""
    prompt = get_prompt(prompt_id)

    if not prompt:
        console.print(f"[red]Prompt #{prompt_id} not found.[/red]")
        raise SystemExit(1)

    # Header
    rating_str = "★" * prompt.rating + "☆" * (5 - prompt.rating) if prompt.rating else "Not rated"

    console.print(Panel(
        prompt.content,
        title=f"[bold]Prompt #{prompt_id}[/bold]",
        subtitle=f"{rating_str}",
        box=box.ROUNDED,
    ))

    # Metadata
    if prompt.model or prompt.task_type or prompt.tags:
        meta = []
        if prompt.model:
            meta.append(f"[dim]Model:[/dim] {prompt.model}")
        if prompt.task_type:
            meta.append(f"[dim]Type:[/dim] {prompt.task_type}")
        if prompt.tags:
            meta.append(f"[dim]Tags:[/dim] {', '.join(prompt.tags)}")
        console.print("  ".join(meta))

    # Outcome
    if prompt.outcome:
        console.print()
        console.print(Panel(
            prompt.outcome,
            title="[bold]Outcome[/bold]",
            box=box.SIMPLE,
        ))

    # Traits
    if prompt.traits:
        console.print()
        console.print("[bold]Detected Traits:[/bold]")
        for trait, detected in sorted(prompt.traits.items()):
            icon = "[green]✓[/green]" if detected else "[dim]✗[/dim]"
            desc = TRAITS.get(trait, "")
            trait_display = trait.replace("_", " ").title()
            console.print(f"  {icon} {trait_display} [dim]- {desc}[/dim]")


@main.command()
@click.argument("query")
@click.option("-n", "--limit", default=10, help="Number of results")
def search(query: str, limit: int):
    """Search prompts by content."""
    prompts = search_prompts(query, limit=limit)

    if not prompts:
        console.print(f"[dim]No prompts matching '{query}'[/dim]")
        return

    console.print(f"[bold]Found {len(prompts)} prompts:[/bold]\n")

    for p in prompts:
        rating_str = "★" * p.rating if p.rating else ""
        console.print(f"[cyan]#{p.id}[/cyan] {rating_str}")
        content_preview = p.content[:100] + "..." if len(p.content) > 100 else p.content
        console.print(f"  {content_preview.replace(chr(10), ' ')}")
        console.print()


@main.command()
@click.argument("prompt_id", type=int)
@click.argument("rating", type=click.IntRange(1, 5))
@click.option("-o", "--outcome", help="Notes about the outcome")
def rate(prompt_id: int, rating: int, outcome: str):
    """Rate a prompt (1-5 stars).

    Examples:
        fridgprompt rate 42 5
        fridgprompt rate 42 5 -o "Worked perfectly!"
    """
    if not get_prompt(prompt_id):
        console.print(f"[red]Prompt #{prompt_id} not found.[/red]")
        raise SystemExit(1)

    if rate_prompt(prompt_id, rating, outcome):
        stars = "★" * rating + "☆" * (5 - rating)
        console.print(f"[green]Rated #{prompt_id}: {stars}[/green]")
    else:
        console.print("[red]Failed to rate prompt.[/red]")


@main.command()
@click.option("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
@click.option("--simple", is_flag=True, help="Use simple rule-based analysis (no LLM)")
def analyze(model: str, simple: bool):
    """Analyze prompts for traits using local LLM."""
    prompts = get_prompts_for_analysis()

    if not prompts:
        console.print("[dim]All prompts have been analyzed.[/dim]")
        return

    console.print(f"[bold]Analyzing {len(prompts)} prompts...[/bold]\n")

    use_llm = not simple

    for prompt in prompts:
        console.print(f"[cyan]#{prompt.id}[/cyan] ", end="")

        try:
            traits = analyze_prompt(prompt, use_llm=use_llm, model=model)
            save_traits(prompt.id, traits)

            detected = [t for t, v in traits.items() if v]
            console.print(f"[green]✓[/green] {len(detected)} traits detected")

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")


@main.command()
@click.argument("prompt_id", type=int)
@click.option("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
@click.option("--simple", is_flag=True, help="Use simple rule-based analysis")
def traits(prompt_id: int, model: str, simple: bool):
    """Show/detect traits for a specific prompt."""
    prompt = get_prompt(prompt_id)

    if not prompt:
        console.print(f"[red]Prompt #{prompt_id} not found.[/red]")
        raise SystemExit(1)

    # If no traits yet, analyze
    if not prompt.traits:
        console.print("[dim]Analyzing...[/dim]")
        detected = analyze_prompt(prompt, use_llm=not simple, model=model)
        save_traits(prompt_id, detected)
        prompt.traits = detected

    console.print(f"\n[bold]Traits for Prompt #{prompt_id}[/bold]\n")

    present = [(t, d) for t, d in TRAITS.items() if prompt.traits.get(t)]
    absent = [(t, d) for t, d in TRAITS.items() if not prompt.traits.get(t)]

    if present:
        console.print("[green]Present:[/green]")
        for trait, desc in present:
            console.print(f"  [green]✓[/green] {trait.replace('_', ' ').title()} - {desc}")

    if absent:
        console.print("\n[dim]Missing:[/dim]")
        for trait, desc in absent:
            console.print(f"  [dim]✗ {trait.replace('_', ' ').title()} - {desc}[/dim]")


@main.command()
def insights():
    """Show patterns from your rated prompts."""
    data = generate_insights()

    if not data["ready"]:
        console.print(f"[yellow]{data['message']}[/yellow]")
        console.print("\n[dim]Rate more prompts with: fridgprompt rate <id> <1-5>[/dim]")
        return

    stats = data["stats"]

    console.print(Panel(
        f"[bold]{stats['total_prompts']}[/bold] prompts stored\n"
        f"[bold]{stats['rated_prompts']}[/bold] rated\n"
        f"[bold]{stats['avg_rating']:.1f}[/bold] avg rating",
        title="[bold]Your Vault[/bold]",
        box=box.ROUNDED,
    ))

    # Good patterns
    if data["good_patterns"]:
        console.print("\n[bold green]In your ★★★★★ prompts:[/bold green]")
        for trait, pct in data["good_patterns"][:5]:
            bar = format_trait_bar(pct)
            trait_display = trait.replace("_", " ").title()
            console.print(f"  [green]✓[/green] {bar} {trait_display}")

    # Bad patterns
    if data["bad_patterns"]:
        console.print("\n[bold red]In your ★ prompts:[/bold red]")
        for trait, pct in data["bad_patterns"][:5]:
            bar = format_trait_bar(pct)
            trait_display = trait.replace("_", " ").title()
            console.print(f"  [red]✗[/red] {bar} {trait_display}")

    # Suggestions
    if data["suggestions"]:
        console.print("\n[bold yellow]Suggestions:[/bold yellow]")
        for suggestion in data["suggestions"]:
            console.print(f"  [yellow]→[/yellow] {suggestion}")


@main.command()
def tags():
    """List all tags."""
    all_tags = get_all_tags()

    if not all_tags:
        console.print("[dim]No tags yet.[/dim]")
        return

    console.print("[bold]Tags:[/bold]")
    console.print("  " + ", ".join(all_tags))


@main.command()
def stats():
    """Show basic statistics."""
    data = generate_insights()
    s = data["stats"]

    avg = f"{s['avg_rating']:.1f}" if s['avg_rating'] else "N/A"

    stats_panel = f"""
  [bold cyan]Prompts:[/bold cyan]     {s['total_prompts']}
  [bold yellow]Rated:[/bold yellow]       {s['rated_prompts']}
  [bold green]Avg Rating:[/bold green]  {avg}
"""

    console.print(Panel(
        stats_panel,
        title="[bold]Fridgprompt Stats[/bold]",
        border_style="cyan",
        box=box.DOUBLE,
    ))


@main.command("open")
def open_fridge():
    """Open the fridge and see what's inside."""
    show_banner()
    data = generate_insights()
    s = data["stats"]

    # Build fridge display
    console.print(FRIDGE_ART)

    if s['total_prompts'] == 0:
        console.print("[dim]  Your fridge is empty![/dim]")
        console.print("  [dim]Add your first prompt:[/dim] [bold]fridgprompt add[/bold]\n")
    else:
        avg = f"{s['avg_rating']:.1f}" if s['avg_rating'] else "-"
        console.print(f"  [bold]{s['total_prompts']}[/bold] prompts stored")
        console.print(f"  [bold]{s['rated_prompts']}[/bold] rated [dim]([/dim][yellow]{avg}[/yellow] [dim]avg)[/dim]")

        # Show recent tags
        recent_tags = get_all_tags()[:5]
        if recent_tags:
            console.print(f"  [dim]Tags:[/dim] {', '.join(recent_tags)}")
        console.print()


if __name__ == "__main__":
    main()
