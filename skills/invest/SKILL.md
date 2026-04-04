---
name: invest
description: "Spawnar founder autônomo para uma bet do portfolio. Due diligence no repo, define mandate, cria bet card (GitHub Issue) e gera o prompt pro Cloud Scheduled Task. Triggers: '/invest', 'invest in', 'spawn founder', 'nova bet', 'quero investir em', 'criar founder', 'portfolio bet'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch
argument-hint: "<repo-url> [descrição da bet]"
model: sonnet
effort: high
---

# /invest — Spawn an autonomous founder

> Templates: `templates/vc/founder-mandate.md`, `templates/vc/bet-card.md`
> Fund state: `.claude/state/fund/`
> Architecture reference: `ARCHITECTURE.md` § "Two worlds"

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

## Step 3 — Define mandate with VC

Present due diligence summary. Then ask (AskUserQuestion):

```
Due diligence complete for {repo}:
- What it does: {one_liner}
- State: {state}
- Quick wins: {list}

Define the investment terms:
```

Questions to ask (all in one AskUserQuestion call):
1. **Mission** — what should the founder accomplish? (one liner)
2. **Scope** — what can the founder do autonomously? (suggest based on due diligence)
3. **Metrics** — how do we measure success? (suggest based on project)
4. **Runway** — how many runs before first board meeting? (suggest: 10)
5. **Kill criteria** — when to stop? (suggest: no progress in 5 consecutive runs)
6. **Check-in cadence** — board meeting every N runs? (suggest: 5)

If user approves the suggested defaults: proceed. If they want to adjust: update.

## Step 4 — Generate mandate

Populate `templates/vc/founder-mandate.md` with the agreed terms.
Save to `.claude/state/fund/bets/{slug}/mandate.md`

The mandate.md contains both:
1. The **prompt** (to copy into the Cloud Scheduled Task)
2. The **metadata YAML** (for /board and /fund to parse)

## Step 5 — Create bet card (GitHub Issue)

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

## Step 6 — Present to VC + instructions

Print to the user:

```
✅ Bet created: {startup_name}
Bet card: #{issue_number}
Mandate: .claude/state/fund/bets/{slug}/mandate.md

To launch your founder:

1. Open Claude Code and run: /schedule
2. When asked for a prompt, paste the mandate prompt from:
   .claude/state/fund/bets/{slug}/mandate.md
   (the text between the ``` code block fences under "Prompt")

3. Configure the scheduled task:
   - Repo: {repo_url}
   - Schedule: every 4 hours (or your preference, minimum 1h)
   - Connectors: enable GitHub

4. The founder will start on the next scheduled run.

Board meeting: run /board #{issue_number} after {check_in_every} runs.
Kill switch: founder stops automatically when runway reaches 0.
```

## Rules

- **Never start without a repo URL.** The mandate needs a concrete codebase.
- **Due diligence is mandatory.** Never invest without reading the repo.
- **Mandate must be self-contained.** The founder cannot ask questions — every scenario must be handled by the mandate.
- **Metrics must be measurable.** Vague metrics like "make it better" are rejected. Require specifics.
