# Research: VC-Founder Architecture for Autonomous AI Agents
<!-- 2026-04-04 — foundational research for portfolio model -->

## Core question
How to structure autonomous AI agents as "founders" running with VC-like dynamics:
thesis-driven allocation, founder autonomy, periodic board meetings, portfolio thinking.

## Key findings

### 1. Long-running agent patterns

**Anthropic harness pattern** (most battle-tested):
- Two agents: initializer (creates structure) + coding agent (incremental sessions)
- `claude-progress.txt` as explicit state artifact — each session reads it to reconstruct context
- Git history as audit trail
- Demo: C compiler built across ~2,000 sessions, compiles Linux kernel
- Source: [anthropic.com/engineering/effective-harnesses-for-long-running-agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

**Session duration data**: Claude Code sessions nearly doubled Oct/2025→Jan/2026 (25→45min). Sonnet 4.5 reaches 30+ hours in certain contexts.
- Source: [anthropic.com/research/long-running-Claude](https://www.anthropic.com/research/long-running-Claude)

**Autonomy levels** (Anthropic paper): operator → collaborator → consultant → approver → observer
- Source: [anthropic.com/research/measuring-agent-autonomy](https://www.anthropic.com/research/measuring-agent-autonomy)

### 2. Multi-agent orchestration — closest to VC/founder

**ComposioHQ/agent-orchestrator** — most relevant open source:
- Fleet of coding agents, each with own git worktree, branch, PR
- Orchestrator plans tasks, spawns agents, monitors CI failures, re-injects feedback
- Agent-agnostic (Claude Code, Codex, Aider), tracker-agnostic (GitHub, Linear)
- 40K lines TypeScript, built in 8 days by its own agents
- Source: [github.com/ComposioHQ/agent-orchestrator](https://github.com/ComposioHQ/agent-orchestrator)

**Squad (GitHub/bradygaster)**:
- Team of agents (lead, frontend, backend, tester) initialized per repo
- Persistent memory: each agent writes learnings to `history.md` in `.squad/`
- Key rule: agent that wrote code cannot review its own work
- Source: [github.com/bradygaster/squad](https://github.com/bradygaster/squad)

**Principal-agent framework** (California Management Review, July 2025):
- "Guided autonomy" — autonomy within delegation boundaries that grow with trust
- Maps directly to VC/founder: trust grows as founder delivers results
- Source: [cmr.berkeley.edu/2025/07/rethinking-ai-agents-a-principal-agent-perspective/](https://cmr.berkeley.edu/2025/07/rethinking-ai-agents-a-principal-agent-perspective/)

### 3. Drift control strategies

**Types of drift observed:**
- Gradual behavioral drift: income verification step was invoked reliably at first, then skipped 20-30% of cases. Silent degradation.
- Proxy optimization: customer service agent learned refunds → positive reviews → gave refunds too liberally
- Long-horizon inconsistency: agent loses track of original objectives as context grows

**What works:**
| Strategy | How it works |
|---|---|
| Structured checkpointing | Explicit progress file per session (Anthropic harness) |
| LLM-as-judge | Separate LLM evaluates outputs at each step |
| Kill criteria | Pre-defined thresholds for automatic escalation to human |
| Guided autonomy | Competency zones — agent knows where autonomy ends |
| Sequence observation | Monitor action sequences, not individual actions |
| Self-review prohibition | Different agent reviews work (Squad pattern) |

**Key insight**: drift is detected by observing *sequences* of actions, not individual actions. This is the least developed but most critical control layer.

### 4. GitHub as coordination layer

**GitHub Agentic Workflows** (Feb 2026 — technical preview):
- Workflows written in Markdown, converted to Actions
- Read-only by default, "safe outputs" for writes
- Threat detection job scans proposed changes before applying
- Source: [github.com/github/gh-aw](https://github.com/github/gh-aw)

**GitHub Issues as handoff contracts** (DEV Community case study):
- 6 specialized agents coordinating through Issues
- Detailed instructions as Issue comments before agents start
- Persists beyond sessions — agents resume exactly where they left off
- Source: [dev.to/alprimak/building-an-ai-agent-orchestrator-how-6-specialized-agents-coordinate-through-github-55gk](https://dev.to/alprimak/building-an-ai-agent-orchestrator-how-6-specialized-agents-coordinate-through-github-55gk)

### 5. Claude Code scheduled tasks

Two mechanisms:
- `/loop` — session-scoped, doesn't persist between sessions
- Scheduled tasks — cloud or desktop, persists, auto-expires after 7 days (natural review point)

The 7-day expiry is actually a feature for VC model: forces periodic "board meeting" to renew runway.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Monolithic context | Context overflows mid-session, agent guesses |
| Implicit memory | Each session starts fresh — must be explicit |
| Black box operation | Drift detected too late without step-level observability |
| Proxy optimization | Agent optimizes for metric, not objective |
| Static policies | Model updates change what's safe |
| Self-review | Agent can't catch its own blind spots |
| Autonomy without boundaries | Agent doesn't know where competence ends |

## Implications for VC-founder architecture

1. **Founder state must be explicit** — progress file + git, never implicit memory
2. **Board meetings are checkpoints** — not just reports, actual drift detection points
3. **Guided autonomy grows with trust** — start tight, expand as founder delivers
4. **Kill criteria upfront** — what failure looks like, defined before funding
5. **Cross-founder review** — one founder reviews another's work
6. **GitHub as the coordination primitive** — Issues as contracts, Projects as portfolio board
7. **7-day scheduled task expiry = natural funding round** — must justify renewal
