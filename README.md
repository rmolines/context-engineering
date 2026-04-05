# Context Engineering

A session protocol for Claude Code that gives your AI assistant persistent memory across sessions.

Most AI coding sessions start from zero. The assistant doesn't know your project's architecture, what you were working on yesterday, or where the important files are. You re-explain the same things every time.

Context engineering fixes this. It's the practice of designing what information an AI sees, when it sees it, and how it's stored between sessions — so every conversation starts with the right context instead of a blank slate.

## What it does

Install it and you get slash commands that form a complete session protocol:

| Command | What it does |
|---------|-------------|
| `/bootstrap` | Scans your project, generates a domain map of APIs/auth/data, sets up state tracking. Idempotent — safe to run anytime. |
| `/discovery` | Upstream: transforms a rough request into a spec'd GitHub Issue. Human + Claude collaboration. |
| `/plan` | Decomposes a task into deliverables with dependencies, batches, and git strategy. Three granularity levels. |
| `/run` | Executes plans respecting dependency order. Parallelizes independent work via worktrees. Handles git, PRs, CI. |
| `/persist` | Saves session state to disk — progress, decisions, learnings. Detects domain drift. Generates continuation prompts. |
| `/distill` | Crystallizes a workflow into a reusable skill. Extracts patterns, anti-patterns, and defaults that worked. |

Plus **hooks** (auto-restore context after compaction), **rules** (explore-plan-execute cycle, facts-first documentation), and **templates** (CLAUDE.md, domain maps, CI, state files).

## Install

```bash
claude plugin add github:rmolines/context-engineering
```

## Quick start

After installing, open any project:

```bash
cd your-project
claude
```

Then run:
```
/bootstrap
```

This scans your project and creates:
- `.claude/state/STATE.md` — tracks initiatives, active work, and backlog
- `.claude/docs/index.md` — domain map pointing to your APIs, auth, data model, and canonical patterns

From here, the typical flow is:

```
/discovery →  research + spec a request into a GitHub Issue
/delivery  →  implement a spec'd Issue → PR with validation
/persist   →  save state for next session
```

Next time you open the project, `/bootstrap` detects existing state and loads it — no re-explanation needed.

## The philosophy

The core insight: **facts about your codebase matter more than instructions about behavior.**

Most CLAUDE.md files are full of rules ("always use conventional commits", "follow the style guide"). But what actually prevents wrong output is domain knowledge — which endpoints exist, how auth works, where the canonical patterns are.

```
# Instead of this (instruction-heavy):
"Always validate input with Zod schemas"
"Use Bearer auth on all API routes"
"Follow the existing error handling pattern"

# Do this (fact-first):
- [leads CRUD](src/app/api/leads/route.ts) — Bearer auth, Zod validation, POST/GET
- [session auth](src/lib/session.ts) — JWT cookies for web users
- [API auth](src/lib/api-auth.ts) — Bearer token for agents
```

The AI reads the actual code and pattern-matches. No rules needed — and it never drifts.

**Target ratio:** ~70% domain facts, ~30% behavioral instructions in your always-on context.

Read the full philosophy: **[CONTEXT-PHILOSOPHY.md](CONTEXT-PHILOSOPHY.md)**

## Architecture

```
Session Start
     │
     ▼
┌─────────────────────────────────────────────────┐
│  Always-on context (~200 lines budget)          │
│                                                 │
│  CLAUDE.md          Identity, direction,        │
│                     canonical patterns          │
│                                                 │
│  STATE.md           Active work, backlog        │
│  (hook-injected)    (what am I doing?)          │
│                                                 │
│  Rules              Session cycle, standards    │
│  (auto-loaded)                                  │
│                                                 │
│  Memory index       User prefs, project facts   │
│  (MEMORY.md)                                    │
└─────────────────────┬───────────────────────────┘
                      │
                      │  progressive disclosure
                      │  (loaded on demand)
                      ▼
┌─────────────────────────────────────────────────┐
│  .claude/docs/index.md    Domain map — APIs,    │
│                           auth, data, patterns  │
│                                                 │
│  .claude/state/plan-*.md  Execution plans       │
│                                                 │
│  .claude/state/*.md       Workstream history    │
│                                                 │
│  research/                Foundational research  │
└─────────────────────────────────────────────────┘
```

**Key constraint:** LLMs degrade after ~70% context window usage. Auto-compaction triggers at ~83.5%. The system keeps critical info in the always-on layer and loads detail on demand — so you never waste context budget on things you don't need right now.

## What's in the box

```
context-engineering/
├── skills/                  # 7 slash commands (4 core + 3 supplemental)
│   ├── bootstrap/           #   project initialization + state loading
│   ├── discovery/           #   upstream: request → spec'd GitHub Issue
│   ├── delivery/            #   downstream: Issue → PR with validation
│   ├── plan/                #   (deprecated) structured planning
│   ├── run/                 #   (deprecated) plan execution
│   ├── persist/             #   session state persistence
│   └── distill/             #   workflow crystallization
│
├── hooks/                   # Lifecycle hooks
│   ├── hooks.json           #   hook configuration
│   └── post-compact.sh      #   re-inject state after context compaction
│
├── rules/                   # Auto-loaded behavioral rules
│   ├── session-cycle.md     #   explore → plan → execute
│   ├── standards.md         #   6-question quality gate
│   └── context-documentation.md  # facts > instructions, pointer > prose
│
├── templates/               # Reusable project templates
│   ├── claude-md-root.md    #   CLAUDE.md template (fact-first)
│   ├── claude-md-snippet.md #   lightweight CLAUDE.md snippet
│   ├── docs/index.md        #   domain map template
│   ├── state/STATE.md       #   state tracking template
│   ├── state/_workstream.md #   workstream template
│   ├── ci/                  #   GitHub Actions CI template
│   └── post-compact-hook.sh #   hook template
│
├── research/                # Foundational research on context engineering
│   ├── context-engineering-overview.md
│   ├── context-engineering-landscape.md
│   ├── ce-landscape-2026.md
│   ├── claude-code-context-engineering.md
│   ├── context-window-internals.md
│   └── intra-session-patterns.md
│
├── tools/
│   └── context-viz/         # TUI for visualizing session context (Python/Textual)
│
└── CONTEXT-PHILOSOPHY.md    # Canonical reference — the full system design
```

## Key concepts

### Always-on vs progressive disclosure

Not everything belongs in CLAUDE.md. The ~200 line budget means you need to choose what's critical for *every* decision vs what's only needed *sometimes*.

| If Claude would err on... | It's... | Where it goes |
|--------------------------|---------|---------------|
| **Direction** (builds wrong thing) | Always-on | CLAUDE.md, STATE.md |
| **Detail** (builds right thing, wrong way) | Progressive | .claude/docs/, plan files |

### Pointer > prose

Don't describe code — point to it. One line with a file path and 3-5 word annotation beats a paragraph that will drift by next week.

### Canonical patterns

Instead of writing rules about code style, point to your best existing example. The AI reads it and pattern-matches — more reliable than any written rule.

### The /persist bridge

At session end, `/persist` routes information to the right place — progress to STATE.md, learnings to memory, drift detection to domain maps. It generates a continuation prompt so the next session picks up exactly where you left off.

## Research

The `research/` directory contains foundational research on context engineering:

- **Context engineering overview** — definitions, origin (Andrej Karpathy), core components
- **Landscape analysis** — taxonomy of approaches, market players, state of the art (March 2026)
- **Claude Code internals** — how Claude Code manages context, CLAUDE.md cascading, hooks, skills
- **Context window internals** — how LLM windows work, degradation curves, compaction mechanics
- **Intra-session patterns** — patterns for managing context within a single session

## License

MIT
