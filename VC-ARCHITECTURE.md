# VC-Founder Architecture

> The human is a VC. The agents are founders. Bets are startups. Autonomy is the default.
> This document is the canonical reference for the VC operating model. Skills, templates, and lifecycle derive from it.

## Mental model: VC Fund

The system extends the Two Worlds model (see `ARCHITECTURE.md`) with a different relationship between human and agent:

| | Squad model (ARCHITECTURE.md) | VC model (this doc) |
|---|---|---|
| **Human role** | Stakeholder — requests features, validates | VC — invests, evaluates, decides |
| **Agent role** | Squad — PM + Designer + Dev + QA | Founder — autonomous operator with strategy |
| **Interaction** | Collaborative (discovery + delivery) | Autonomous with checkpoints (board meetings) |
| **Cadence** | Per-session, synchronous | Multi-week, asynchronous (scheduled tasks) |
| **Artifacts** | Issues, PRs | Bet cards, Run Reports, Retros, Board Reports |

### When to use which

- **Squad model:** user is present, interactive sessions, feature work, bug fixes
- **VC model:** long-running bets, user wants autonomy, agent operates independently for weeks

Both models share the same infrastructure (GitHub, disk state, skills).

## Core principle

**Skills = agent operations. VC decisions = human moments.**

The VC doesn't "run a skill to invest" — they decide to invest and the agent operationalizes it. Skills exist to facilitate human decisions, not to make them.

## Two roles

### The VC (human)

The VC is a capital allocator. They:
- **Invest:** identify opportunities, define thesis, allocate compute (runs)
- **Monitor:** check portfolio health via dashboard
- **Evaluate:** hold board meetings, assess progress vs OKRs
- **Decide:** continue, pivot, bridge, or kill bets
- **Direct:** post ad-hoc directives when needed

The VC doesn't write code, specify tasks, or manage sprints. They set direction and evaluate outcomes.

### The Founder (agent)

The founder is an autonomous operator. They:
- **Strategize:** maintain a thesis about why this bet matters
- **Plan:** define cycles with OKRs and discovery areas
- **Execute:** write code, open PRs, make tactical decisions
- **Learn:** write retros, track patterns, adjust approach
- **Report:** investor updates with metrics, learnings, confidence
- **Escalate:** flag pivot signals when thresholds are met

The founder operates via Cloud Scheduled Task — no human in the loop between board meetings.

## 3 Horizons

Every founder operates in 3 time horizons:

| Horizon | Scope | Cadence | Document | Owner |
|---|---|---|---|---|
| **Strategy** (12-18m) | Why this bet exists, North Star, moat | Reviewed per cycle | `strategy.md` | VC defines at spawn, founder reviews |
| **Cycle** (4-6 weeks) | 1 objective, 3 KRs, discovery areas | New cycle at board | `cycle-plan.md` | Founder proposes, VC approves |
| **Run** (each ~4h) | Execute, measure, report | Every scheduled run | Run Report (Issue comment) | Founder alone |

**Retros** bridge horizons: every 5 runs, the founder reflects on patterns, confidence, and learnings.

## Skills

Three skills operationalize the VC model:

| Skill | Action | Who triggers | Model |
|---|---|---|---|
| `/spawn` | Create founder: due diligence → strategy → cycle-plan → mandate → bet card → scheduled task | VC decides to invest | sonnet |
| `/board` | Evaluate founder: read reports → analyze KRs → detect drift → recommend → VC decides | Periodic (every N runs) or on-demand | sonnet |
| `/fund` | Portfolio view: dashboard, thesis, analytics, bet detail | VC wants status | haiku |

### /spawn — Birth of a founder

The spawn process ensures founders are born with full operating context:

```
VC: "quero investir no repo X"

/spawn <repo>
  ├── Due diligence (parallel: repo audit + external context)
  ├── Define strategy with VC (hypothesis, north star, where/how, anti-goals)
  ├── Define cycle-plan #1 with VC (objective, 3 KRs, discovery areas, pivot triggers)
  ├── Define mandate with VC (mission, scope, boundaries, runway, kill criteria)
  ├── Generate all docs (strategy.md, cycle-1.md, mandate.md)
  ├── Create bet card (GitHub Issue)
  └── Instructions for scheduled task setup
```

The founder is born knowing: why they exist (strategy), what to achieve (cycle OKRs), what they can do (mandate), and when to stop (kill criteria).

### /board — Evaluation ritual

Board meetings are the primary interaction between VC and founder:

```
/board #N
  ├── Load context (reports, retros, cycle-plan, strategy)
  ├── Analyze (KR trajectory, drift signals, confidence trend, pivot triggers)
  ├── Generate recommendation (CONTINUE / PIVOT / BRIDGE / KILL)
  ├── Present to VC
  └── Execute VC decision (new cycle, update mandate, extend runway, or kill)
```

Board meetings are where cycles transition: the VC can approve a new cycle-plan, authorize a pivot, or kill the bet.

### /fund — Portfolio dashboard

The fund skill is read-only — it presents, never modifies:

```
/fund           → portfolio dashboard (all bets, cycle progress, confidence)
/fund thesis    → create or edit fund thesis
/fund analytics → burn rate, velocity, ROI projection
/fund #N        → detailed view of a specific bet
```

## Templates

All templates live in `templates/vc/`:

| Template | Purpose | Created by |
|---|---|---|
| `vc-lifecycle.md` | Reference: VC journey, cadence, bet lifecycle | (reference doc) |
| `strategy.md` | Founder's thesis: hypothesis, north star, where/how to play | `/spawn` |
| `cycle-plan.md` | Cycle OKRs: objective, 3 KRs, discovery areas, pivot triggers | `/spawn` (first), `/board` (subsequent) |
| `retro.md` | Founder retro (YC format): highlights, lowlights, patterns, confidence | Founder (every 5 runs) |
| `founder-mandate.md` | Scheduled task prompt: identity, 3 horizons, scope, instructions | `/spawn` |
| `bet-card.md` | GitHub Issue: thesis, strategy, terms, KRs, scope, kill criteria | `/spawn` |
| `board-report.md` | Board meeting: cycle review, drift analysis, recommendation | `/board` |
| `fund-thesis.md` | Fund thesis: investment approach, targets, default terms | `/fund thesis` |

## Disk structure

```
.claude/state/fund/
├── README.md                    # this structure explanation
├── thesis.md                    # fund thesis (optional)
└── bets/
    └── {slug}/
        ├── mandate.md           # scheduled task prompt + metadata YAML
        ├── strategy.md          # thesis, north star, where/how to play
        ├── cycles/
        │   ├── cycle-1.md       # OKRs, discovery areas, thresholds
        │   └── cycle-2.md       # (created at board meeting)
        ├── retros/
        │   ├── retro-run-5.md   # highlights, lowlights, patterns
        │   └── retro-run-10.md
        ├── status.md            # last known status (updated by /board)
        └── board-meetings/
            └── YYYY-MM-DD.md    # board meeting reports
```

Runs live as comments on the GitHub Issue (bet card), not on disk.

## GitHub integration

| GitHub artifact | VC usage |
|---|---|
| **Issue** | Bet card — the contract between VC and founder |
| **Issue comments** | Run Reports, Retros, VC Directives, Board Meeting summaries |
| **Labels** | `bet:active`, `bet:paused`, `bet:killed`, `bet:exited` |
| **Milestone** | Groups related bets (optional) |

## Lifecycle

Full lifecycle reference in `templates/vc/vc-lifecycle.md`. Summary:

```
VC decides to invest
  └── /spawn → founder born with strategy + cycle-plan #1
        │
        ├── Runs 1-5: execute, report (with KRs, learnings, confidence)
        │     └── Run 5: MANDATORY retro
        ├── Runs 6-10: execute, report
        │     └── Run 10: RETRO + /board meeting
        │           └── VC decides: CONTINUE → cycle-plan #2
        │                          PIVOT → new direction
        │                          BRIDGE → more runway
        │                          KILL → bet ends
        └── Repeat until exit or kill
```

### Operating cadence

| Frequency | Artifact | Who |
|---|---|---|
| Each run (~4h) | Run Report | Founder |
| Every 5 runs | Retro | Founder |
| Every 10 runs (or board_cadence) | Board Meeting | VC + `/board` |
| Per cycle (~4-6 weeks) | New Cycle Plan | Founder proposes, VC approves |

### Pivot authority

The founder **never** pivots alone. They can:
1. **Detect** that pivot thresholds (from cycle-plan) are met
2. **Propose** new direction with evidence (in retro or run report)
3. **Escalate** via `PIVOT_SIGNAL: true` flag in run report

The VC decides at the next `/board`: accept pivot, adjust, or kill.

## Migration guide

### Migrating an existing bet to the new operating model

For bets created with the old `/invest` skill (no strategy/cycle docs):

1. **Create strategy.md** — extract thesis from the bet card Issue, define North Star Metric based on existing metrics
2. **Create cycle-plan.md** — convert existing metrics to KRs with baseline (from run reports), target, and kill thresholds
3. **Update mandate.md** — replace the old prompt with the new 3-horizon template, referencing strategy and cycle-plan
4. **Create directory structure** — `cycles/`, `retros/` directories
5. **Update scheduled task** — paste new mandate prompt
6. **First run under new model** — founder will self-check against strategy and cycle-plan

The bet card Issue doesn't need migration — run reports and retros will appear as new comments.

---
*Canonical reference for the VC-Founder Architecture. Skills, templates, and lifecycle derive from this document.*
