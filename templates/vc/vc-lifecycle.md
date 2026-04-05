# VC Lifecycle

> Reference document — formalizes the VC journey as moments and rituals.
> Skills operationalize decisions; the VC makes the decisions.

## Principle

**Skills = agent operations. VC decisions = human moments.**

The VC doesn't "run a skill to invest" — they decide to invest and the agent operationalizes it. The dynamics of the VC (investing, evaluating, killing) are human moments facilitated by the agent, not agent actions.

## VC Moments (human decisions)

| Moment | Trigger | What happens | Skill involved |
|---|---|---|---|
| **Invest** | VC identifies opportunity | Decides bet, defines thesis | `/spawn` operationalizes |
| **Monitor** | Curiosity / routine | Checks portfolio dashboard | `/fund` presents |
| **Evaluate** | Periodic (every N runs) | Board meeting with founder | `/board` facilitates |
| **Decide** | Post-board | Continue / Pivot / Bridge / Kill | Human decision, `/board` records |
| **Direct** | Ad hoc | Posts VC Directive on Issue | Manual (GitHub comment) |

## Bet Lifecycle

```
VC decides to invest
  └── /spawn → founder is born with strategy + cycle-plan #1
        │
        ├── Runs 1-5: founder executes, reports
        │     └── Run 5: MANDATORY retro
        ├── Runs 6-10: founder executes, reports
        │     └── Run 10: RETRO + /board meeting
        │           └── VC decides: CONTINUE → cycle-plan #2
        │                          PIVOT → founder proposes new cycle
        │                          BRIDGE → +runway, same cycle
        │                          KILL → bet ends
        └── Repeat until exit or kill
```

## Operating Cadence

| Frequency | Artifact | Who |
|---|---|---|
| Each run (~4h) | Run Report | Founder |
| Every 5 runs | Retro | Founder |
| Every 10 runs (or board_cadence) | Board Meeting | VC + `/board` |
| Per cycle (~4-6 weeks) | New Cycle Plan | Founder proposes, VC approves |
| Per cycle | Strategy review | Founder updates if needed |

## Founder's 3 Horizons

| Horizon | Scope | Cadence | Document |
|---|---|---|---|
| **Strategy** (12-18m) | Thesis + North Star + why this matters | Reviewed per cycle | `strategy.md` |
| **Cycle** (4-6 weeks) | 1 objective, 3 KRs, discovery areas, pivot thresholds | Every 4-6 weeks (VC approves at board) | `cycle-plan.md` |
| **Run** (each execution) | Execute, measure, report | Each run (~4h) | Run Report (Issue comment) |
| **Retro** | What did I learn? Patterns? Adjust? | Every 5 runs | `retro.md` |

## Pivot Authority

The founder **never** pivots alone. But can:

1. **Detect** that pivot thresholds have been reached (data in retro)
2. **Propose** new cycle-plan with evidence ("KR1 flat for 3 runs, suggest zoom-in on feature X")
3. **Escalate** to VC via flag in run-report (`PIVOT_SIGNAL: true`)

The VC decides at `/board`: accept pivot, adjust, or kill.

## Disk Structure (per bet)

```
.claude/state/fund/bets/{slug}/
├── mandate.md           # scheduled task prompt
├── strategy.md          # thesis, north star, where/how to play
├── cycles/
│   ├── cycle-1.md       # OKRs, discovery areas, thresholds
│   └── cycle-2.md
├── retros/
│   ├── retro-run-5.md   # highlights, lowlights, patterns
│   └── retro-run-10.md
└── (runs live as comments on the GitHub Issue)
```

---
*Reference document — managed by CE VC skills*
