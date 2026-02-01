# Fridgprompt

```
   _____ ____  ___ ____   ____ ____  ____   ___  __  __ ____ _____
  |  ___|  _ \|_ _|  _ \ / ___|  _ \|  _ \ / _ \|  \/  |  _ \_   _|
  | |_  | |_) || || | | | |  _| |_) | |_) | | | | |\/| | |_) || |
  |  _| |  _ < | || |_| | |_| |  __/|  _ <| |_| | |  | |  __/ | |
  |_|   |_| \_\___|____/ \____|_|   |_| \_\\___/|_|  |_|_|    |_|
```

**A prompt vault for vibe coders.**

Store your AI prompts, rate them, and discover what makes your prompts actually work.

---

## The Problem

You write prompts all day. Some work great. Some don't. But you never remember *why*.

## The Solution

Fridgprompt is your personal prompt refrigerator. Open it up, grab what you need, and over time, learn what ingredients make your prompts succeed.

```
    ┌─────────────────┐
    │  ┌───────────┐  │
    │  │ ★ prompts │  │    ← Store your prompts
    │  │  rated    │  │
    │  └───────────┘  │
    │─────────────────│
    │  ┌───────────┐  │
    │  │ ✓ traits  │  │    ← Analyze patterns
    │  │ analyzed  │  │
    │  └───────────┘  │
    │  ┌───────────┐  │
    │  │ ◆ insights│  │    ← Learn what works
    │  │ patterns  │  │
    │  └───────────┘  │
    └────────□────────┘
```

---

## Features

- **Store prompts** with tags, model info, and task type
- **Rate outcomes** (1-5 stars) with notes
- **Full-text search** across all your prompts
- **Trait detection** using your local LLM (Qwen, Llama, etc.)
- **Pattern insights** showing what makes your prompts succeed or fail
- **Beautiful CLI** with Rich formatting

---

## Install

```bash
git clone https://github.com/yourusername/fridgprompt.git
cd fridgprompt
pip install -e .
```

## Quick Start

```bash
# Add a prompt
fridgprompt add "Fix the auth bug in login.py. Error: TypeError on submit"

# Rate it after you see the result
fridgprompt rate 1 5 -o "Fixed perfectly"

# See your patterns (after 5+ rated prompts)
fridgprompt insights
```

---

## Commands

| Command | Description |
|---------|-------------|
| `add` | Store a new prompt |
| `list` | Browse your prompts |
| `show <id>` | View prompt details |
| `search <query>` | Full-text search |
| `rate <id> <1-5>` | Rate a prompt |
| `analyze` | Detect traits using local LLM |
| `traits <id>` | View traits for a prompt |
| `insights` | See your prompting patterns |
| `stats` | Basic statistics |
| `open` | Visual overview of your vault |

Short alias: `fp` works the same as `fridgprompt`

---

## Trait Detection

Fridgprompt analyzes your prompts for 10 key patterns:

| Trait | What it means |
|-------|---------------|
| **clear_goal** | States what you want built/fixed |
| **gives_context** | Explains the project/situation |
| **references_files** | Points to specific files/functions |
| **shows_error** | Includes actual error messages |
| **describes_behavior** | Explains expected behavior |
| **sets_constraints** | Limits scope or style |
| **breaks_down_task** | Splits into steps |
| **shows_example** | Provides sample input/output |
| **explains_why** | Gives reasoning/motivation |
| **specifies_negative** | Says what NOT to do |

Uses your local Ollama model (Qwen 2.5, Llama 3, etc.) or falls back to rule-based detection.

---

## Insights

After rating 5+ prompts, `fridgprompt insights` shows you:

```
In your ★★★★★ prompts:
  ✓ [████████████████████] 95% References Files
  ✓ [████████████████░░░░] 80% Gives Context
  ✓ [██████████████░░░░░░] 70% Shows Error

In your ★ prompts:
  ✗ [████████████████░░░░] 80% Missing Clear Goal
  ✗ [██████████████░░░░░░] 70% Too Short

Suggestions:
  → Keep referencing specific files - it's in 95% of your best prompts
  → Try adding more context when starting new tasks
```

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) (optional, for LLM-based trait detection)

```bash
# For trait analysis with local LLM
ollama pull qwen2.5:7b
```

---

## Data

Stored in `~/.fridgprompt/prompts.db` (SQLite)

---

## Detailed Usage

See [USAGE.md](USAGE.md) for complete documentation.

---

## License

MIT

---

*Built for vibe coders who want to get better at prompting.*
