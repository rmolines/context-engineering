# Context Engineering

A context management layer for Claude Code that makes AI coding sessions stateful by default.

Most AI coding sessions start from zero. The assistant doesn't know your project's architecture, what you were working on yesterday, or where the important files are. You re-explain the same things every time.

Context engineering fixes this. It configures and optimizes Claude Code's native context layers (CLAUDE.md, rules, memory, hooks) and creates new ones (domain maps, milestone docs, GitHub infrastructure) — so every conversation starts with the right context instead of a blank slate.

## How it relates to Claude Code

Claude Code already has a context architecture: CLAUDE.md files, rules, memory, hooks, skills. CE doesn't replace any of that — it **manages** it:

```
┌─ Claude Code native ─────────────────────────────────────┐
│  CLAUDE.md    Rules    Memory    Hooks    Skills/Plugins  │
├─ CE manages ─────────────────────────────────────────────┤
│  ↑ configures and optimizes native layers                │
│  + creates: domain map, milestone docs, GitHub infra     │
│  + connects: GitHub Issues/Milestones as human interface │
└──────────────────────────────────────────────────────────┘
```

**Native layers CE manages:** generates optimized CLAUDE.md templates, installs session rules, writes learnings to memory, configures hooks.

**New layers CE creates:** domain maps (`.claude/docs/`), milestone docs (`.claude/state/milestones/`), GitHub infrastructure (labels, milestones, Projects V2).

## Two worlds

CE operates across two worlds with different audiences:

```
┌─ Human world (GitHub) ──────────────┐  ┌─ Agent world (local disk) ──────────┐
│                                     │  │                                     │
│  Issues       → requests + specs    │  │  .claude/docs/    → domain map      │
│  Milestones   → goals + signals     │  │  .claude/state/   → milestone docs  │
│  PRs          → deliveries          │  │  discovery.md     → research notes  │
│  Comments     → session history     │  │  plan.md (temp)   → agent infra     │
│                                     │  │                                     │
│  Audience: you (stakeholder)        │  │  Audience: Claude (across sessions) │
│  Nature: permanent record           │  │  Nature: operational + historical   │
└─────────────────────────────────────┘  └─────────────────────────────────────┘
```

The **Issue** is the handoff contract between worlds. Discovery (human + Claude) produces it. Delivery (Claude alone) consumes it. Session history lives as GitHub Issue comments — no local state files needed.

## What it does

Install it and you get slash commands that form a complete session protocol:

| Command | What it does |
|---------|-------------|
| `/init` | Sets up CE in your project — generates CLAUDE.md, domain map, configures GitHub. Idempotent, run anytime to check health. |
| `/bootstrap` | Loads session context — live GitHub query via GraphQL, deep context loading, briefing, alignment. Run at start of each session. |
| `/discovery` | Upstream: transforms a rough request into a spec'd GitHub Issue. Human + Claude collaboration. |
| `/delivery` | Downstream: picks up a spec'd Issue and delivers a PR with validation report. Autonomous. |
| `/persist` | Saves session state as GitHub Issue comments — progress, decisions, continuation context. Detects domain drift. |
| `/distill` | Crystallizes a workflow into a reusable skill. Extracts patterns and anti-patterns. |

Plus **hooks** (auto-restore context after compaction), **rules** (explore-plan-execute cycle, facts-first documentation), and **templates** (CLAUDE.md, domain maps, milestone docs).

### The flow

```
/init       →  one-time project setup (CLAUDE.md, domain map, GitHub)
/bootstrap  →  every session (load context, briefing, align)

/discovery  →  research + spec a request into a GitHub Issue
/delivery   →  implement a spec'd Issue → PR with validation
/persist    →  save session state as Issue comments for next session
```

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

First time? Run init to set up CE:
```
/init
```

This scans your project and creates:
- Optimized `CLAUDE.md` (if missing) with Commander's Intent format
- `.claude/docs/index.md` — domain map pointing to your APIs, auth, data model, and canonical patterns
- `.claude/state/` — state tracking directory
- GitHub labels, milestones (if connected)

Then load session context:
```
/bootstrap
```

This queries GitHub live (single GraphQL call for Issues + comments), loads deep context, and presents a standup briefing with continuation from your last session.

From here, the typical flow is:

```
/discovery →  research + spec a request into a GitHub Issue
/delivery  →  implement a spec'd Issue → PR with validation
/persist   →  save state as Issue comments for next session
```

Next time you open the project, `/bootstrap` loads fresh context from GitHub — no re-explanation needed.

## The philosophy

The core insight: **facts about your codebase matter more than instructions about behavior.**

Most CLAUDE.md files are full of rules ("always use conventional commits", "follow the style guide"). But what actually prevents wrong output is domain knowledge — which endpoints exist, how auth works, where the canonical patterns are.

```
# Instead of this (instruction-heavy):
"Always validate input with Zod schemas"
"Use Bearer auth on all API routes"

# Do this (fact-first):
- [leads CRUD](src/app/api/leads/route.ts) — Bearer auth, Zod validation, POST/GET
- [session auth](src/lib/session.ts) — JWT cookies for web users
```

The AI reads the actual code and pattern-matches. No rules needed — and it never drifts.

**Target ratio:** ~70% domain facts, ~30% behavioral instructions in your always-on context.

Read the full architecture: **[ARCHITECTURE.md](ARCHITECTURE.md)**

## Architecture

```
Session Start
     │
     ▼
┌─────────────────────────────────────────────────┐
│  Always-on context (~200 lines budget)          │
│                                                 │
│  CLAUDE.md          Identity, direction,        │
│  (native)           canonical patterns          │
│                                                 │
│  Rules              Session cycle, standards    │
│  (native)                                       │
│                                                 │
│  Memory index       User prefs, project facts   │
│  (native)                                       │
└─────────────────────┬───────────────────────────┘
                      │
                      │  progressive disclosure
                      │  (loaded on demand by /bootstrap)
                      ▼
┌─────────────────────────────────────────────────┐
│  GitHub (live)            Issues, comments,      │
│                           milestones, PRs        │
│                                                  │
│  .claude/docs/index.md    Domain map — APIs,     │
│  (CE layer)               auth, data, patterns   │
│                                                  │
│  .claude/state/milestones/ Milestone + Issue docs  │
│  (CE layer)               {slug}/issue-{N}-{slug}/│
│                                                  │
│  research/                Foundational research  │
└──────────────────────────────────────────────────┘
```

**Key constraint:** LLMs degrade after ~70% context window usage. Auto-compaction triggers at ~83.5%. The system keeps critical info in the always-on layer and loads detail on demand.

## What's in the box

```
context-engineering/
├── skills/                  # 6 slash commands
│   ├── init/                #   project setup (native + CE layers)
│   ├── bootstrap/           #   session context loading (GraphQL + briefing)
│   ├── discovery/           #   upstream: request → spec'd GitHub Issue
│   ├── delivery/            #   downstream: Issue → PR with validation
│   ├── persist/             #   session state → GitHub Issue comments
│   └── distill/             #   workflow crystallization
│
├── hooks/                   # Lifecycle hooks
│   ├── hooks.json           #   hook configuration
│   └── post-compact.sh      #   re-inject context after compaction
│
├── rules/                   # Auto-loaded behavioral rules
│   ├── session-cycle.md     #   explore → plan → execute
│   ├── standards.md         #   6-question quality gate
│   └── context-documentation.md  # facts > instructions, pointer > prose
│
├── templates/               # Reusable project templates
│   ├── claude-md-root.md    #   CLAUDE.md template (fact-first)
│   ├── docs/index.md        #   domain map template
│   ├── state/               #   milestone + issue templates
│   └── ci/                  #   GitHub Actions CI template
│
├── research/                # Foundational research on context engineering
│
└── ARCHITECTURE.md          # Canonical reference — philosophy + architecture
```

## Key concepts

### Always-on vs progressive disclosure

Not everything belongs in CLAUDE.md. The ~200 line budget means you need to choose what's critical for *every* decision vs what's only needed *sometimes*.

| If Claude would err on... | It's... | Where it goes |
|--------------------------|---------|---------------|
| **Direction** (builds wrong thing) | Always-on | CLAUDE.md |
| **Detail** (builds right thing, wrong way) | Progressive | .claude/docs/, GitHub Issues |

### Pointer > prose

Don't describe code — point to it. One line with a file path and 3-5 word annotation beats a paragraph that will drift by next week.

### Canonical patterns

Instead of writing rules about code style, point to your best existing example. The AI reads it and pattern-matches — more reliable than any written rule.

### GitHub as session memory

At session end, `/persist` posts structured comments to the GitHub Issues you worked on — what was done, decisions made, and what comes next. At session start, `/bootstrap` reads these comments via GraphQL and presents a continuation briefing. No local state files needed for session handoff.

## Research

The `research/` directory contains foundational research on context engineering:

- **Context engineering overview** — definitions, origin, core components
- **Landscape analysis** — taxonomy of approaches, state of the art
- **Claude Code internals** — how Claude Code manages context natively
- **Context window internals** — degradation curves, compaction mechanics
- **Intra-session patterns** — patterns for managing context within a single session

## License

MIT
