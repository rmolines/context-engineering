# Context Engineering — Philosophy & Architecture

> How we design, organize, and orchestrate context for AI-assisted development.
> This is the canonical reference. Projects that apply this system get a compact operational version.

## Core principle

> "Find the smallest set of high-signal tokens that maximize the likelihood of the desired outcome." — Anthropic

Context is a finite resource. More tokens ≠ better results. After ~70% window usage, precision degrades. After ~85%, hallucinations increase. The goal is not to load everything — it's to load the **right thing at the right time**.

## The four strategies (Anthropic framework)

| Strategy | What it means | Our mechanism |
|----------|--------------|---------------|
| **Write** | Persist state outside the window | STATE.md, workstream files, plan files, BACKLOG.md |
| **Select** | Retrieve only what's relevant | Progressive disclosure, /discover, hook auto-injection |
| **Compress** | Summarize to save tokens | Inline summaries + detail file pointers, subagent isolation |
| **Isolate** | Separate concerns across agents | Subagents with fresh windows, worktree isolation |

## Context layers — always-on vs progressive disclosure

### Always-on (~200 lines budget)

Auto-loaded at session start. Informs **every** decision. If Claude would err on **direction** without it, it's always-on.

| Layer | Mechanism | Content |
|-------|-----------|---------|
| Project identity | CLAUDE.md root (cascata) | What is this, 2-3 lines |
| Direction | CLAUDE.md root (inline, 5-8 lines) | Product thesis summary, key principles |
| Conventions | App CLAUDE.md (~80 lines) | Stack, commands, design system, how to work |
| Current state | STATE.md (via SessionStart hook) | Initiatives table, active workstreams, backlog |
| Process guardrails | Rules (session-cycle, git-workflow, standards) | How to operate |
| User profile | Memory (MEMORY.md index) | Preferences, operating model |

### Progressive disclosure

Available but loaded on demand. If Claude would only err on **detail** without it, it's disclosure.

| Content | Where | When to load |
|---------|-------|-------------|
| Full thesis/strategy doc | `tese-v1.md` or equivalent | Discussing product, pitch, strategy |
| Initiative details | `initiatives.md` | Working on a specific initiative |
| Execution plans | `plan-*.md` | `/run` executing a plan |
| Workstream history | `workstream.md` in state/ | Resuming specific work |
| Research/discoveries | `.claude/discoveries/` | Needing prior research |
| Detailed standards | `.claude/standards/` | Editing specific file types (path-scoped rules) |
| Competitor/pricing analysis | Inside strategy docs | GTM/pricing discussions |

**The connecting mechanism is the pointer.** Always-on context contains short summaries + links to detail files. Claude sees the map, reads the detail when acting.

## File architecture

### In a monorepo

```
project-root/
  CLAUDE.md              ← identity + direction summary + structure + discipline
  tese-v1.md             ← full strategy (progressive, NOT @imported)
  BACKLOG.md             ← decision log (append-only, dated)
  apps/
    main-app/
      CLAUDE.md          ← stack, conventions, commands (cascades from root)
      .claude/
        state/
          STATE.md       ← initiatives table + active + backlog (hook-injected)
          initiatives.md ← detail per initiative (progressive)
          plan-*.md      ← execution plans (progressive, via /run)
          *.md           ← workstream files (progressive)
        rules/           ← path-scoped rules (conditional on file type)
        standards/       ← detailed standards (progressive)
```

### In a single repo

```
project-root/
  CLAUDE.md              ← identity + direction + conventions (all-in-one)
  .claude/
    state/
      STATE.md           ← initiatives + active + backlog
      ...
```

### CLAUDE.md cascata (Claude Code native behavior)

When cwd = `apps/main-app/`, Claude Code auto-loads:
1. `project-root/CLAUDE.md` (parent)
2. `apps/main-app/CLAUDE.md` (cwd)

Both are always-on. The root carries strategic context; the app carries operational context.

## State management

### STATE.md — the session entry point

The SessionStart hook injects STATE.md. This is what Claude sees first. Structure:

```markdown
# State — {Project}

## Initiatives
> Detail: [initiatives.md](initiatives.md)
| ID | Name | Priority | Status | Deps |

## Active
- [plan-name](plan-name.md) — one-line status

## Backlog
- Idea or task not yet prioritized

## Completed
- [workstream](workstream.md) — what was done
```

### What goes where

| Type of info | Destination | Cadence |
|-------------|-------------|---------|
| Product direction, thesis | CLAUDE.md `## Direction` (inline summary) | Changes rarely |
| Architecture decisions | CLAUDE.md or dedicated doc | Decided once, lasts months |
| Initiatives/roadmap | STATE.md `## Initiatives` table + initiatives.md | Changes weekly |
| Active execution | STATE.md `## Active` + plan files | Changes per session |
| Organic ideas, todos | STATE.md `## Backlog` | Grows organically |
| Dated decisions | BACKLOG.md (if hub pattern) | Append-only log |
| Cross-session learnings | Memory system | When non-obvious patterns emerge |

### The /persist bridge

At session end, `/persist` routes information to the right place:
- Execution progress → STATE.md + plan files
- New ideas/todos → STATE.md `## Backlog`
- Direction changes → suggest updating CLAUDE.md (with confirmation)
- Decisions → BACKLOG.md (if exists)
- Learnings → Memory system
- Generates a continuation prompt for the next session

## Skill lifecycle

```
SessionStart (hook) → auto-inject STATE.md
  ↓
/discover → research before acting (optional)
  ↓
/plan → decompose into deliverables with git strategy
  ↓
/run → execute plan (commits, PRs, CI)
  ↓
/persist → save state + generate continuation prompt
```

Skills are inherently progressive disclosure — only the description (~100 tokens) loads until invoked. Full content (1-7k tokens) loads on demand.

## Anti-patterns

| Anti-pattern | Why it's bad | What to do instead |
|-------------|-------------|-------------------|
| @importing 200+ line docs | Eats context budget every session | Inline 5-8 line summary + pointer |
| Duplicate sources of truth | Conflicting state, confusion | One canonical location per info type |
| Logging decisions without datestamp | Can't tell if still relevant | Always `[YYYY-MM-DD]` prefix |
| Putting everything in CLAUDE.md | Exceeds 200-line target, low adherence | Split: CLAUDE.md (stable) / STATE.md (dynamic) / skills (on-demand) |
| Depending on user memory | "I told Claude last session" | Persist to disk, auto-inject via hook |
| Saving code patterns to memory | Stale fast, derivable from code | Only save non-obvious decisions and rationale |

## Key constraints (from research)

- **CLAUDE.md target**: <200 lines per file for max adherence
- **Auto-compact trigger**: ~83.5% of context window. After compaction, CLAUDE.md survives (re-read from disk), conversation details are lost
- **"Lost in the middle"**: LLMs attend well to beginning and end, ignore the middle. Critical info at start or end, never buried
- **Hook compliance**: 100% deterministic. Rule compliance: ~70%. Prefer hooks for critical behaviors
- **Subagent isolation**: Fresh 200K window, only final output (~1-2K tokens) returns to parent
- **Skill injection**: Only description in context until invoked — true progressive disclosure
