---
name: fund
description: "Portfolio management — visão consolidada do fundo VC, thesis, lista de bets ativas e status. Sub-comandos: '/fund' dashboard, '/fund thesis' editar thesis, '/fund analytics' burn rate e métricas. Triggers: '/fund', 'portfolio', 'meu fundo', 'quantas bets', 'status do portfolio', 'ver bets', 'fund thesis'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
argument-hint: "[thesis | analytics | #issue-number]"
model: haiku
effort: low
---

# /fund — VC Portfolio management

> Templates: `templates/vc/fund-thesis.md`
> Lifecycle reference: `templates/vc/vc-lifecycle.md`
> Fund state: `.claude/state/fund/`

**Input:** `$ARGUMENTS`

| Input | Mode |
|---|---|
| empty | DASHBOARD — portfolio overview |
| `thesis` | THESIS — create or edit fund thesis |
| `analytics` | ANALYTICS — burn rate, ROI, allocation |
| `#N` | BET DETAIL — status of a specific bet |

---

## Mode: DASHBOARD (default)

### Step 1 — Read all bets

```bash
# Read all mandate.md files in .claude/state/fund/bets/
find .claude/state/fund/bets -name "mandate.md" | xargs ...
# Read all status.md files
find .claude/state/fund/bets -name "status.md" | xargs ...
# Read current cycle-plan for each bet
find .claude/state/fund/bets -name "cycle-*.md" | xargs ...
```

For each bet, extract from mandate.md metadata:
- startup name, repo, bet_issue, initial_runway, metrics, current_cycle

For each bet, extract from status.md (if exists):
- last board meeting date and recommendation
- current runway remaining
- current metric values

For each bet, extract from current cycle-plan:
- cycle number, objective, KR statuses
- confidence level (from latest retro or run report)

If GITHUB_MODE=true: cross-check with GitHub Issue labels (bet:active / bet:paused / bet:killed / bet:exited)

### Step 2 — Present dashboard

```
VC Portfolio — {fund_name}

Active bets ({N}):

  {startup_name} (#{issue})
     Repo: {repo}
     Cycle: #{cycle_number} — {objective}
     KRs: {on_track}/{total} on track | Confidence: {HIGH/MEDIUM/LOW}
     Runway: {remaining}/{initial} runs
     Last board: {date} → {CONTINUE/BRIDGE/...}

  {startup_name} (#{issue})
     [PAUSED — runway exhausted, awaiting renewal]

  {startup_name} (#{issue})
     [KILLED — {date} — {one_line_reason}]

Completed ({N}):
  {startup_name} — exited {date}

Portfolio health: {N} active, {N} at risk, {N} killed
KR summary: {total_on_track}/{total_krs} on track across portfolio

Next board meetings:
  - {startup_name}: in {N} runs (est. {date})
  - {startup_name}: in {N} runs (est. {date})
```

---

## Mode: THESIS (`thesis`)

### If thesis exists
Read `.claude/state/fund/thesis.md`. Present current thesis. Ask:
- Edit a section?
- Rewrite entirely?
- Just view?

### If thesis doesn't exist
Populate `templates/vc/fund-thesis.md` interactively.
Ask key questions (AskUserQuestion):
1. Fund name
2. One-paragraph thesis
3. Target bet types
4. Default terms (runway, cadence, kill criteria)
5. Max concurrent bets

Save to `.claude/state/fund/thesis.md`

---

## Mode: ANALYTICS (`analytics`)

### Compute metrics

For each bet (from mandate.md metadata + Run Report comments):

**Burn rate estimate:**
- Runs completed × estimated cost per run
- Default estimate: $5/run (Sonnet, moderate activity)
- Override: read cost from mandate metadata if set

**Velocity:**
- Average runs between meaningful commits
- PRs opened per 10 runs

**ROI projection:**
- Qualitative: on track / at risk / off track
- Based on last board meeting recommendation + KR trajectory

**Cycle efficiency:**
- KRs achieved per cycle
- Average cycle duration (runs)
- Pivot rate (cycles pivoted / total cycles)

### Present analytics

```
Portfolio Analytics

Total investment (estimated):
  {startup_a}: {N} runs × ${cost}/run = ${total}
  {startup_b}: {N} runs × ${cost}/run = ${total}
  ─────────────────────────────
  Total: ${grand_total} across {N} bets

Velocity:
  {startup_a}: {commits}/run, {prs}/10 runs
  {startup_b}: {commits}/run, {prs}/10 runs

Cycle efficiency:
  {startup_a}: cycle #{N}, {krs_achieved}/{total_krs} KRs achieved
  {startup_b}: cycle #{N}, {krs_achieved}/{total_krs} KRs achieved

Portfolio health:
  On track: {N} bets ({%})
  At risk: {N} bets ({%})
  Off track: {N} bets ({%})
```

---

## Mode: BET DETAIL (`#N`)

Read mandate.md + strategy.md + current cycle-plan + status.md + latest retro for the specific bet. Read last 5 Run Reports from GitHub.

Present:
- Strategy summary (hypothesis, north star, where/how to play)
- Current cycle objective + KR progress
- Confidence trend (from retros)
- Timeline of last 5 runs
- Last board meeting recommendation
- Next recommended action

---

## Rules

- **Always read status.md first.** It's the cached summary — avoids re-reading all Issue comments.
- **Dashboard includes cycle info.** Show cycle number, KR progress, and confidence for each bet.
- **Dashboard is read-only.** /fund doesn't modify bets — that's /spawn and /board.
- **If .claude/state/fund/ doesn't exist:** display "No fund initialized. Run /spawn to create your first bet."
- **Haiku stays inline.** No subagents for simple reads — this skill is fast and lightweight.
