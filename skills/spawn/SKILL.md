---
name: spawn
description: "Spawnar founder autônomo para uma bet do portfolio. Due diligence no repo, define strategy + cycle plan com VC, cria mandate, bet card (GitHub Issue) e gera o prompt pro Cloud Scheduled Task. Triggers: '/spawn', 'spawn founder', 'nova bet', 'criar founder', 'quero investir em', 'portfolio bet', 'spawnar founder'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch
argument-hint: "<repo-url> [descrição da bet]"
model: sonnet
effort: high
---

# /spawn — Spawn an autonomous founder

> Templates: `templates/vc/founder-mandate.md`, `templates/vc/bet-card.md`, `templates/vc/strategy.md`, `templates/vc/cycle-plan.md`
> Lifecycle reference: `templates/vc/vc-lifecycle.md`
> Fund state: `.claude/state/fund/`

**Input:** `$ARGUMENTS` — repo URL + optional description

---

## Step 1 — Parse input

Extract from `$ARGUMENTS`:
- `repo_url` — GitHub repo URL (required)
- `description` — rough description of the bet (optional, will research if absent)

If no `repo_url`: ask with AskUserQuestion.

## Step 2 — Due diligence (parallel subagents)

**Subagent A — Haiku: repo audit**
```
Read the repo: README, CLAUDE.md, package.json/Cargo.toml/pyproject.toml, git log --oneline -20
Answer:
1. What does this project do? (1 sentence)
2. Current state: active / stale / greenfield?
3. CI exists? (yes/no + what)
4. Main language and stack
5. Entry points / key files
6. Obvious quick wins or immediate tasks
```

**Subagent B — Sonnet: external context (only if repo is a known project)**
Search for: project name, recent activity, community, known issues, roadmap.

Run both in parallel. Synthesize findings inline.

## Step 3 — Define strategy with VC

Present due diligence summary. Then propose a strategy based on findings.

**Propose (inline, then validate with AskUserQuestion):**

Based on due diligence, suggest:
1. **Bet Hypothesis** — why this bet is worth it (1 paragraph)
2. **North Star Metric** — the one metric that defines success + how to measure it
3. **Where to Play** — target user, use case, distribution
4. **How to Win** — differentiator, core advantage, key bet
5. **Anti-goals** — what the founder should NOT do

Present as:
```
Strategy proposal for {startup_name}:

Hypothesis: {proposed hypothesis}
North Star: {proposed metric}
Where to play: {segment}
How to win: {approach}
Anti-goals: {list}

Adjust anything, or approve to continue?
```

VC validates/adjusts. Save agreed strategy using `templates/vc/strategy.md` → `.claude/state/fund/bets/{slug}/strategy.md`

## Step 4 — Define cycle-plan #1 with VC

Based on strategy + due diligence, propose the first cycle:

1. **Objective** — one sentence business outcome for cycle #1
2. **3 Key Results** — baseline → target → kill threshold (suggest based on project state)
3. **Discovery Areas** — 2-3 hypotheses to test
4. **Pivot Triggers** — explicit thresholds
5. **Duration** — estimated runs (suggest: 15-20 for first cycle)

Present as:
```
Cycle #1 proposal:

Objective: {proposed objective}

Key Results:
  KR1: {metric} — {baseline} → {target} (kill if < {threshold})
  KR2: {metric} — {baseline} → {target} (kill if < {threshold})
  KR3: {metric} — {baseline} → {target} (kill if < {threshold})

Discovery: {hypotheses}
Pivot if: {triggers}
Duration: ~{N} runs

Adjust anything, or approve to continue?
```

Note: cycle #1 is exploratory. KRs should focus on "validate if X is possible", not aggressive business metrics.

VC validates/adjusts. Save agreed plan using `templates/vc/cycle-plan.md` → `.claude/state/fund/bets/{slug}/cycles/cycle-1.md`

## Step 5 — Define mandate with VC

Present the operational terms. Ask (AskUserQuestion):

1. **Mission** — what should the founder accomplish? (one liner)
2. **Scope** — what can the founder do autonomously? (suggest based on due diligence)
3. **Boundaries** — what requires VC approval? (suggest based on project)
4. **Runway** — how many runs total? (suggest: 20)
5. **Kill criteria** — when to stop? (suggest: no progress in 5 consecutive runs + KR kill thresholds)
6. **Check-in cadence** — board meeting every N runs? (suggest: 10)

If user approves the suggested defaults: proceed. If they want to adjust: update.

## Step 6 — Generate mandate

Populate `templates/vc/founder-mandate.md` with the agreed terms + references to strategy and cycle-plan.
Save to `.claude/state/fund/bets/{slug}/mandate.md`

Create directory structure:
```
.claude/state/fund/bets/{slug}/
├── mandate.md
├── strategy.md       (from step 3)
├── cycles/
│   └── cycle-1.md    (from step 4)
└── retros/           (empty, founder will populate)
```

The mandate.md contains both:
1. The **prompt** (to copy into the Cloud Scheduled Task)
2. The **metadata YAML** (for /board and /fund to parse)

## Step 7 — Create bet card (GitHub Issue)

If GITHUB_MODE=true:
```bash
gh issue create \
  --repo {owner}/{this-repo} \
  --title "Bet: {startup_name}" \
  --body "$(populate templates/vc/bet-card.md)" \
  --label "bet:active" \
  --milestone "{current milestone or ask}"
```

Save issue number to `.claude/state/fund/bets/{slug}/mandate.md` metadata.

If GITHUB_MODE=false: save bet-card to `.claude/state/fund/bets/{slug}/bet-card.md`

## Step 8 — Present to VC + instructions

Print to the user:

```
Founder spawned: {startup_name}

Bet card: #{issue_number}
Strategy: .claude/state/fund/bets/{slug}/strategy.md
Cycle #1: .claude/state/fund/bets/{slug}/cycles/cycle-1.md
Mandate: .claude/state/fund/bets/{slug}/mandate.md

To launch:

1. Run: /schedule
2. Paste the mandate prompt from:
   .claude/state/fund/bets/{slug}/mandate.md
   (the text between the ``` code block fences under "Prompt")

3. Configure:
   - Repo: {repo_url}
   - Schedule: every 4 hours (or your preference, minimum 1h)
   - Connectors: enable GitHub

4. The founder will start on the next scheduled run.

Retros: founder writes every 5 runs.
Board meeting: run /board #{issue_number} after {check_in_every} runs.
Kill switch: founder stops automatically when runway reaches 0.
```

## Rules

- **Never start without a repo URL.** The mandate needs a concrete codebase.
- **Due diligence is mandatory.** Never spawn without reading the repo.
- **Strategy before tactics.** Define strategy.md and cycle-plan.md BEFORE the mandate.
- **Mandate must be self-contained.** The founder cannot ask questions — every scenario must be handled.
- **Metrics must be measurable.** Vague metrics like "make it better" are rejected. Require specifics.
- **Cycle #1 is exploratory.** Don't set aggressive KRs — validate first, optimize later.
- **VC approves everything.** Strategy, cycle-plan, and mandate all need VC validation before spawn.
