---
name: board
description: "Board meeting — avaliar progresso do founder, detectar drift, recomendar continue/pivot/bridge/kill. Lê Run Reports do GitHub Issue e gera avaliação estruturada. Triggers: '/board', '/board #N', 'board meeting', 'como tá o founder', 'review portfolio', 'avaliar bet', 'checar founder'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: "[#issue-number | all]"
model: sonnet
effort: low
---

# /board — Board meeting

> Templates: `templates/vc/board-report.md`
> Fund state: `.claude/state/fund/bets/`
> Architecture reference: VC-Founder Architecture

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
- GitHub Issue #N comments (all Run Reports from the founder)
- `.claude/state/fund/bets/` — find the directory matching this issue number
- mandate.md metadata: initial_runway, metrics, kill_criteria, check_in_every

```bash
gh issue view $N --json comments --jq '.comments[].body'
```

Parse all comments:
- `## Run Report #X` blocks → extract: progress, metrics values, decisions, blockers
- `## VC Directive` blocks → note any VC interventions
- `## Board Meeting` blocks → previous board meeting summaries

### Step 2 — Analyze (inline)

Build a timeline of metric values across all runs. Detect:

**Metric trajectory:**
- Improving (↑): value trending toward target
- Flat (→): value not changing over 3+ runs
- Declining (↓): value moving away from target

**Drift signals:**
- Scope creep: founder mentioned actions outside mandate scope
- Proxy optimization: founder optimizing for reports, not actual progress
- Circular work: same blocker or same task appearing 3+ consecutive runs
- Stalled: 0 commits or PRs in last 3 runs

**Runway status:**
- Runs completed: count of Run Report comments
- Runway remaining: initial_runway - runs_completed
- Runway at risk: remaining < check_in_every (founder will exhaust before next board)

### Step 3 — Generate recommendation

**CONTINUE** if:
- Metrics improving or on track
- No drift signals
- Runway sufficient for next cycle

**PIVOT** if:
- Metrics flat/declining for 2+ consecutive board meetings
- Scope mismatch (doing the wrong thing)
- Propose specific scope adjustment

**BRIDGE** if:
- Metrics improving but runway running out
- Good progress but more time needed
- Propose specific runway extension (N runs) with justification

**KILL** if:
- Kill criteria met (runway exhausted, metric threshold breached)
- No progress in {kill_after} runs
- Circular work with no resolution

### Step 4 — Write board report

Populate `templates/vc/board-report.md` with the analysis.
Save to `.claude/state/fund/bets/{slug}/board-meetings/{YYYY-MM-DD}.md`

If GITHUB_MODE=true: post the board report as a comment on Issue #N
```bash
gh issue comment $N --body "$(cat board-meeting content)"
```

### Step 5 — Present to VC + ask for decision

Print the board report summary. Then:

If recommendation is CONTINUE: present and ask for confirmation or override.
If PIVOT/BRIDGE/KILL: use AskUserQuestion to get the decision.

**After VC decides:**
- **CONTINUE:** no action needed. Optionally post a VC Directive comment with updated guidance.
- **PIVOT:** update mandate.md with new scope. Post VC Directive comment: "## VC Directive\n{new scope boundaries}"
- **BRIDGE:** update mandate.md runway. Post VC Directive comment: "## VC Directive\nRunway extended by N runs."
- **KILL:** update bet label to `bet:killed`. Post final comment with kill reason. Update status.md.

Update `.claude/state/fund/bets/{slug}/status.md` with board meeting outcome.

---

## Mode: Portfolio (`all`)

Run Mode: Single bet for each active bet. Present a consolidated summary:

```
📊 Portfolio Board — {date}

| Bet | Runs | Runway | Metrics | Recommendation |
|-----|------|--------|---------|----------------|
| startup-a | 8 | 12 runs | ↑ on track | CONTINUE |
| startup-b | 5 | 2 runs | → flat | BRIDGE (needs 5 more) |
| startup-c | 15 | 0 runs | ↓ declining | KILL |
```

Ask VC to confirm all decisions at once.

---

## Rules

- **Read ALL reports before evaluating.** Never judge on last run alone — drift is in the trajectory.
- **Metrics over vibes.** Recommendation must be grounded in metric data, not narrative quality of reports.
- **One recommendation per bet.** Don't hedge (CONTINUE or PIVOT/BRIDGE/KILL, not "maybe").
- **VC decides.** Board generates the recommendation, VC makes the call.
- **Always update status.md.** This is how /fund knows the current state of each bet.
