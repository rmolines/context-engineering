---
name: orchestrate
description: "Autonomous scheduled delivery conductor. Runs /bootstrap, processes PR feedback, delivers ready Issues by priority, runs /persist. Designed for cron/Remote Tasks — works while you sleep. Triggers: '/orchestrate', 'roda autonomo', 'autonomous run'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, WebSearch
argument-hint: "[--budget N] [--dry-run]"
model: sonnet
effort: high
---

# /orchestrate — Autonomous delivery conductor

**Input:** `$ARGUMENTS`

| Argument | Default | Effect |
|---|---|---|
| `--budget N` | 3 | Max Issues to deliver per run |
| `--dry-run` | false | Plan what would happen without executing |

> Architecture reference: `ARCHITECTURE.md` § "Core skills"
> This skill sequences existing skills — it doesn't implement anything itself.
> Designed for use with Claude Code Remote Tasks or `/schedule`.

## Phase 1 — Context

Run `/bootstrap` (DEFAULT mode).

From the briefing, extract:
- **Ready Issues:** have spec (acceptance criteria), prioritized, no blockers
- **Resumable deliveries:** have `execution-state.json` with completed + pending batches
- **PRs with pending feedback:** open PRs where human commented after last agent response

Sort ready Issues by priority:
1. Resumable deliveries first (partially done work)
2. Issues with Priority field set (from GitHub Project)
3. Issues by Milestone (active Milestone Issues before Backlog)
4. If tie: older Issues first (FIFO)

If `--dry-run`: report the plan and stop.

```
Orchestrate plan:
- Feedback: PR #15 has 2 unaddressed comments
- Resume: #10 "auth middleware" — 2/5 batches done
- Deliver: #12 "dark mode" — ready, priority: high
- Deliver: #14 "email templates" — ready, priority: medium
- Budget: 3 Issues (2 remaining after resume + feedback)
```

## Phase 2 — Feedback loop

For each open PR with unaddressed human comments:

### 2.1 — Fetch comments

```bash
gh pr view $PR_NUMBER --json comments,reviews
```

Filter to comments posted AFTER the last agent commit on the PR branch.

### 2.2 — Classify each comment

| Comment pattern | Classification | Action |
|---|---|---|
| "LGTM", "looks good", approval review | **Approval** | Mark PR as ready (or auto-merge if configured) |
| Requests specific change ("use X instead of Y", "add Z") | **Change request** | Rework — re-run affected batch |
| Asks question ("why X?", "what about Y?") | **Question** | Respond with rationale from decision points |
| Expands scope ("also add rate limiting") | **Scope expansion** | Suggest new Issue, don't expand current PR |
| Rejection (close request, "wrong approach") | **Rejection** | Close PR, mark Issue for re-evaluation |

### 2.3 — Process change requests

For each change request:
1. Identify which decision point is affected (parse `execution-log.md`)
2. Re-run the affected batch with the comment as constraint input
3. Push new commits to the same PR branch
4. Update PR body (validation report, decision points)
5. Add `DECISION-OVERRIDDEN` marker to execution-log
6. Comment on PR: "Updated per your feedback. [summary of changes]."

### 2.4 — Process questions

For each question:
1. Find relevant decision points in `execution-log.md`
2. Comment on PR with rationale: "Chose X because [reason]. Alternatives considered: Y, Z."

## Phase 3 — New deliveries

For each ready Issue (by priority), up to `--budget` remaining:

```
/delivery #N
```

This invokes the full delivery pipeline (research → ground → decompose → implement → validate → PR).

**Budget tracking:** decrement budget after each completed delivery. If delivery fails at a gate that requires human input (architectural gate), count it but don't block the run — move to next Issue.

**Between deliveries:** check remaining budget. If exhausted, skip to Phase 4.

## Phase 4 — Persist

Run `/persist`.

Additionally, post a summary comment on each Issue that was worked on:

```bash
gh issue comment $ISSUE_NUMBER --body "$(cat <<'EOF'
## Orchestrate Run — {{date}}

**Action:** {{what was done — delivered / resumed / feedback processed}}
**PR:** #{{pr_number}} ({{status}})
**Next:** {{what remains — more batches, awaiting review, done}}
EOF
)"
```

## Phase 5 — Report

Output a run summary (for logging/monitoring):

```
Orchestrate complete — {{date}}

Feedback processed:
- PR #15: 2 comments addressed (1 change request, 1 question)

Deliveries:
- #10 "auth middleware": resumed, 5/5 batches done → PR #20
- #12 "dark mode": delivered → PR #21
- #14 "email templates": skipped (budget exhausted)

Budget: 3 used / 3 max
Next run: {{cron expression or "manual"}}
```

## Safety rules

- **Never merge PRs.** Only open them. Human approves merges.
- **Never work on draft Issues.** Only Issues with `## Acceptance Criteria`.
- **Respect architectural gates.** If a delivery hits an architectural gate, pause that delivery and move to next Issue. The gate will be resolved in the next human session.
- **Budget is hard.** Never exceed `--budget`. Default 3 keeps cost predictable.
- **Log everything.** Every action is recorded in execution-log and as GitHub comments.
- **Fail gracefully.** If a delivery fails, persist what was done and move on. Don't retry infinitely.

## Scheduling examples

### With Claude Code Remote Tasks
```
Define: repo=owner/repo, prompt="/orchestrate --budget 3", schedule="0 2 * * *"
```

### With /schedule
```
/schedule "0 2 * * *" /orchestrate --budget 3
```

### With /loop (monitoring mode)
```
/loop 6h /orchestrate --budget 1 --dry-run
```
