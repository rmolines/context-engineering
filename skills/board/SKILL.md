---
name: board
description: "Board meeting — avaliar progresso do founder, detectar drift, recomendar continue/pivot/bridge/kill. Lê Run Reports, cycle-plan e retros do GitHub Issue e gera avaliação estruturada. Triggers: '/board', '/board #N', 'board meeting', 'como tá o founder', 'review portfolio', 'avaliar bet', 'checar founder'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: "[#issue-number | all]"
model: sonnet
effort: low
---

# /board — Board meeting

> Templates: `templates/vc/board-report.md`
> Lifecycle reference: `templates/vc/vc-lifecycle.md`
> Fund state: `.claude/state/fund/bets/`

**Input:** `$ARGUMENTS`

| Input | Mode |
|---|---|
| `#N` | Single bet — board meeting for issue #N |
| `all` | Portfolio — board meeting for all active bets |
| empty | Prompt to select a bet |

---

## Mode: Single bet (`#N`)

### Step 1 — Load bet context

Read in parallel:
- GitHub Issue #N comments (all Run Reports + Retros from the founder)
- `.claude/state/fund/bets/` — find the directory matching this issue number
- mandate.md metadata: initial_runway, metrics, kill_criteria, check_in_every, current_cycle
- strategy.md: bet hypothesis, north star metric
- cycles/cycle-{current}.md: objective, KRs (baseline/target/kill), discovery areas, pivot triggers
- retros/ — all retro files (highlights, lowlights, patterns, confidence)

```bash
gh issue view $N --json comments --jq '.comments[].body'
```

Parse all comments:
- `## Run Report #X` blocks → extract: progress, KR values, learnings, confidence, pivot_signal
- `## Retro` blocks → extract: highlights, lowlights, patterns, confidence
- `## VC Directive` blocks → note any VC interventions
- `## Board Meeting` blocks → previous board meeting summaries

### Step 2 — Analyze (inline)

#### Metric trajectory (from run reports)
- Improving (↑): KR values trending toward target
- Flat (→): KR values not changing over 3+ runs
- Declining (↓): KR values moving away from target

#### Cycle review (NEW — from cycle-plan + run reports)
For each Key Result:
- Current value vs baseline vs target vs kill threshold
- Status: on_track / at_risk / off_track
- Trend across runs

For each Discovery Area:
- Status: validated / falsified / in_progress
- Key finding (if any)

#### Confidence trend (from retros + run reports)
- Build timeline of confidence levels (HIGH/MEDIUM/LOW)
- Identify if confidence is rising, stable, or dropping
- Cross-reference confidence drops with KR trajectory

#### Drift signals
- Scope creep: founder mentioned actions outside mandate scope
- Proxy optimization: founder optimizing for reports, not actual progress
- Circular work: same blocker or same task appearing 3+ consecutive runs
- Stalled: 0 commits or PRs in last 3 runs
- Strategy drift: founder actions misaligned with strategy.md thesis

#### Pivot trigger check
- Read pivot triggers from cycle-plan
- Check if any trigger thresholds have been met
- Check if founder flagged PIVOT_SIGNAL in recent reports

#### Runway status
- Runs completed: count of Run Report comments
- Runway remaining: initial_runway - runs_completed
- Runway at risk: remaining < check_in_every (founder will exhaust before next board)

### Step 3 — Generate recommendation

**CONTINUE** if:
- KRs improving or on track
- No drift signals
- Runway sufficient for next cycle
- If end of cycle: propose transition to cycle #N+1

**PIVOT** if:
- KRs flat/declining for 2+ consecutive board meetings
- Pivot triggers from cycle-plan have been met
- Discovery areas falsified the core hypothesis
- Propose specific new direction with evidence from retros/reports

**BRIDGE** if:
- KRs improving but runway running out
- Good progress but more time needed
- Propose specific runway extension (N runs) with justification

**KILL** if:
- Kill criteria met (runway exhausted, KR kill thresholds breached)
- No progress in {kill_after} runs
- Circular work with no resolution
- Strategy thesis invalidated with no viable pivot

### Step 4 — Write board report

Populate `templates/vc/board-report.md` with the analysis.
Save to `.claude/state/fund/bets/{slug}/board-meetings/{YYYY-MM-DD}.md`

If GITHUB_MODE=true: post the board report as a comment on Issue #N
```bash
gh issue comment $N --body "$(cat board-meeting content)"
```

### Step 5 — Present to VC + ask for decision

Print the board report summary. Then:

If recommendation is CONTINUE:
- If end of cycle: present proposed cycle #N+1 direction, ask VC to approve
- Otherwise: present and ask for confirmation or override

If PIVOT: use AskUserQuestion to get the decision. If approved, create new cycle-plan from founder's proposal.

If BRIDGE/KILL: use AskUserQuestion to get the decision.

**After VC decides:**
- **CONTINUE (same cycle):** no action needed. Optionally post a VC Directive with updated guidance.
- **CONTINUE (new cycle):** create new `cycles/cycle-{N+1}.md` with VC-approved OKRs. Update mandate metadata `current_cycle`. Post VC Directive: "## VC Directive\nCycle #{N+1} approved. New KRs: {summary}"
- **PIVOT:** create new `cycles/cycle-{N+1}.md` with pivot direction. Update strategy.md if thesis changed. Update mandate metadata. Post VC Directive: "## VC Directive\nPivot approved. New direction: {summary}"
- **BRIDGE:** update mandate.md runway. Post VC Directive: "## VC Directive\nRunway extended by N runs."
- **KILL:** update bet label to `bet:killed`. Post final comment with kill reason + key learnings. Update status.md.

Update `.claude/state/fund/bets/{slug}/status.md` with board meeting outcome.

---

## Mode: Portfolio (`all`)

Run Mode: Single bet for each active bet. Present a consolidated summary:

```
Portfolio Board — {date}

| Bet | Cycle | Runs | Runway | KR Progress | Confidence | Recommendation |
|-----|-------|------|--------|-------------|------------|----------------|
| startup-a | #2 | 18 | 12 runs | 2/3 on track | HIGH | CONTINUE |
| startup-b | #1 | 5 | 2 runs | 1/3 at risk | MEDIUM | BRIDGE (+10) |
| startup-c | #1 | 15 | 0 runs | 0/3 off track | LOW | KILL |
```

Ask VC to confirm all decisions at once.

---

## Rules

- **Read ALL reports before evaluating.** Never judge on last run alone — drift is in the trajectory.
- **Evaluate against cycle-plan KRs.** Not just generic metrics — the KRs are the contract.
- **Check retros for patterns.** Retros contain the founder's self-assessment — use it.
- **Metrics over vibes.** Recommendation must be grounded in KR data, not narrative quality of reports.
- **One recommendation per bet.** Don't hedge (CONTINUE or PIVOT/BRIDGE/KILL, not "maybe").
- **VC decides.** Board generates the recommendation, VC makes the call.
- **Always update status.md.** This is how /fund knows the current state of each bet.
- **Cycle transitions happen here.** New cycle-plans are approved at board meetings.
