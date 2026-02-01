# Fridgprompt Usage Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fridgprompt.git
cd fridgprompt

# Install in editable mode
pip install -e .

# Verify installation
fridgprompt --version
```

## Quick Start

```bash
# Open the fridge
fridgprompt open

# Add your first prompt
fridgprompt add "Fix the login bug in auth.py"

# Rate it after seeing the result
fridgprompt rate 1 5 -o "Worked perfectly!"

# See your patterns
fridgprompt insights
```

---

## Commands

### Adding Prompts

```bash
# Interactive mode (prompts for details)
fridgprompt add

# Direct with all options
fridgprompt add "Your prompt here" -m claude-4 -t feature --tags "react,api"

# Pipe from clipboard or file
pbpaste | fridgprompt add
cat prompt.txt | fridgprompt add -m gpt-4 -t bugfix
```

**Options:**
- `-m, --model` - Model used (claude-4, gpt-4, etc.)
- `-t, --task-type` - Type of task (feature, bugfix, refactor, etc.)
- `--tags` - Comma-separated tags

---

### Viewing Prompts

```bash
# List recent prompts
fridgprompt list

# Filter by tag
fridgprompt list --tag react

# Filter by rating
fridgprompt list --rating 5

# Show more results
fridgprompt list -n 20

# View specific prompt
fridgprompt show 42
```

---

### Searching

```bash
# Full-text search
fridgprompt search "authentication"
fridgprompt search "TypeError"
```

---

### Rating Prompts

After you use a prompt and see the result, rate it:

```bash
# Rate with stars (1-5)
fridgprompt rate 42 5

# Rate with outcome notes
fridgprompt rate 42 5 -o "Clean implementation, worked first try"

# Rate a bad prompt
fridgprompt rate 43 1 -o "Completely missed the point, had to rewrite"
```

---

### Analyzing Traits

Fridgprompt can detect patterns in your prompts using your local LLM:

```bash
# Analyze all unanalyzed prompts (requires Ollama)
fridgprompt analyze

# Use a different model
fridgprompt analyze --model llama3:8b

# Use simple rule-based analysis (no LLM needed)
fridgprompt analyze --simple

# View traits for a specific prompt
fridgprompt traits 42
```

**Detected Traits:**
| Trait | Description |
|-------|-------------|
| clear_goal | States what you want built or fixed |
| gives_context | Explains the project or situation |
| references_files | Points to specific files or functions |
| shows_error | Includes error message or logs |
| describes_behavior | Explains what should happen |
| sets_constraints | Limits scope or style |
| breaks_down_task | Splits into steps or parts |
| shows_example | Provides sample input/output |
| explains_why | Gives reasoning or motivation |
| specifies_negative | Says what NOT to do |

---

### Getting Insights

After rating 5+ prompts, see what makes your prompts work:

```bash
fridgprompt insights
```

Example output:
```
Your Vault
  23 prompts stored
  18 rated
  4.2 avg rating

In your ★★★★★ prompts:
  ✓ [████████████████████] 95% References Files
  ✓ [████████████████░░░░] 85% Describes Behavior
  ✓ [████████████████░░░░] 80% Gives Context

In your ★ prompts:
  ✗ [████████████████░░░░] 80% Missing Clear Goal
  ✗ [██████████████░░░░░░] 70% No Context Given

Suggestions:
  → Keep using 'references files' - it's in 95% of your best prompts.
  → Missing 'clear goal' correlates with lower ratings.
```

---

### Other Commands

```bash
# View all tags
fridgprompt tags

# Basic statistics
fridgprompt stats

# Open the fridge (visual overview)
fridgprompt open
```

---

## Setting Up Ollama (for Trait Analysis)

1. Install Ollama: https://ollama.ai

2. Pull Qwen model:
   ```bash
   ollama pull qwen2.5:7b
   ```

3. Run analysis:
   ```bash
   fridgprompt analyze
   ```

**Alternative models:**
```bash
fridgprompt analyze --model llama3:8b
fridgprompt analyze --model mistral:7b
```

---

## Tips for Better Prompts

Based on the trait analysis, here's what typically makes vibe coding prompts work:

1. **Reference specific files** - "In `UserCard.tsx`..." not "in the user component"
2. **Include error messages** - Copy the actual error, don't paraphrase
3. **Describe expected behavior** - "Should open modal and confirm" not "should work"
4. **Give context** - "This is a Next.js app using Prisma" helps a lot
5. **Set constraints** - "Keep it simple, no new dependencies"
6. **Say what NOT to do** - "Don't modify the existing API routes"

---

## Data Storage

Your prompts are stored in:
```
~/.fridgprompt/prompts.db
```

This is a SQLite database. You can back it up, copy between machines, or query it directly if needed.

---

## Short Alias

Use `fp` instead of `fridgprompt`:

```bash
fp add "Quick prompt"
fp list
fp rate 1 5
```
