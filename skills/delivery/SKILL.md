---
name: delivery
description: "Downstream: pega Issue especificada e entrega PR com validation report. Autônomo (Claude sozinho). Fases: research, decompose (plan interno), implement (subagentes), validate (subagente isolado), deliver (PR). Triggers: '/delivery #N', 'implementa #N', 'faz #N', 'entrega #N', 'build #N'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch
argument-hint: "#issue-number"
model: sonnet
effort: high
---

# /delivery — Downstream execution

**Input:** `$ARGUMENTS` — must be a GitHub Issue number (e.g., `#10`)

> Architecture reference: `ARCHITECTURE.md` § "Delivery — downstream"
> This skill runs inline — needs to spawn subagents for research, implementation, and validation.

## Step 1 — Read Issue

```bash
gh issue view $ISSUE_NUMBER --json title,body,milestone,labels
```

Parse the Issue spec:
- Intent (what and why)
- UX flow (if present)
- Technical spec
- Acceptance criteria (the contract)

If the Issue lacks acceptance criteria: **abort**. Return to user:
> "Issue #N has no acceptance criteria. Run `/discovery #N` to complete the spec first."

## Step 1.5 — Resume check

Check if `execution-state.json` exists at `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/`:

**If state file exists:**
1. Read `execution-state.json`
2. Compare `plan_hash` with current plan (if plan.md exists)
   - If hash matches: safe to resume
   - If hash differs: warn "Plan changed since last run. Resume from checkpoint or restart?"
3. Report completed batches: "Batches 1-2 of 5 completed (PRs #15, #16). Resuming from batch 3."
4. **Skip to Step 4** for the first non-completed batch. Skip Steps 2, 2.5, 3 entirely (already done).

**If no state file:** proceed to Step 2 (fresh delivery).

## Step 2 — Research (sonnet subagent)

Subagent reads:
- Issue spec (from step 1)
- Relevant code (files mentioned in spec, canonical patterns from domain map)
- External docs (if spec references APIs, libs, or patterns)

Returns: technical context + risks + suggested approach + list of external premises (APIs, libs, services referenced).

## Step 2.5 — Ground (sonnet subagent with WebSearch)

**Purpose:** Verify external premises from research before committing to a plan. Prevents implementing against wrong assumptions (changed APIs, deprecated libs, outdated patterns).

**Heuristic — skip grounding when ALL of these are true:**
- Pure internal refactor (no external deps involved)
- No external APIs or third-party services referenced in spec or research
- All dependencies are pinned and internal
- Issue is about UI/copy changes only

**When grounding runs**, subagent receives:
- External premises extracted from research output (APIs, lib versions, endpoints, service capabilities)
- Issue spec (for additional external references)

Subagent verifies each premise via WebSearch against live sources (official docs, changelogs, npm/pypi, API references). Returns:

```markdown
## Grounding Report

| Premise | Source | Status | Notes |
|---------|--------|--------|-------|
| jose v5.2 supports ES256 | npmjs.com/package/jose | ✅ verified | current: v5.4, ES256 supported since v4.0 |
| /api/v3/auth accepts PKCE | developer.example.com | ⚠️ changed | v3 deprecated, v4 is current — PKCE only on v4 |
| tailwind v4 supports @apply | tailwindcss.com/docs | ✅ verified | |

### Flagged risks
- **BLOCKING:** /api/v3/auth is deprecated. Spec should target v4. Research premise invalid.

### Corrections
- Update auth integration to use API v4 endpoints (breaking change from v3: new token format)
```

**If blocking risks found:** surface to orchestrator before proceeding to decompose:
> "Grounding found invalid premise for #N: [detail]. Research assumed X but current state is Y. Adjusting plan to account for Y."

**If no blocking risks:** proceed to decompose. Grounding report is carried forward to Step 6 (PR body).

**Persist:** append grounding results to `discovery.md` with timestamp:
```markdown
## Grounding — 2026-04-08
- ✅ jose v5.4: ES256 supported
- ⚠️ API v3 deprecated → using v4
```

──▶ **Notification checkpoint:** "Approaching #N as X in N parts: [summary]. Grounding: N premises verified, N flagged."

## Step 3 — Decompose (inline)

Create internal plan at `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/plan.md`
Create execution log at `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/execution-log.md`

Using templates: `templates/state/issue/plan.md`, `templates/state/issue/execution-log.md`

- Break into deliverables (D1, D2, ...)
- Identify deps and batches
- Define git strategy (direct-commit, single-pr, pr-per-batch)
- Map file domains for parallel work

This is agent infrastructure. Deliverables do NOT become GitHub Issues.

> plan.md is temporary infrastructure — deleted after PR opens (Step 6). 
> If delivery is interrupted, it can be regenerated from the Issue spec + git diff.

**Initialize execution-state.json** with all batches as `pending` and a hash of plan.md:

```json
{
  "issue": N,
  "delivery_started": "ISO-8601",
  "plan_hash": "sha256 of plan.md content",
  "batches": [
    {"id": 1, "status": "pending"},
    {"id": 2, "status": "pending"}
  ],
  "grounding": {"verified_at": "ISO-8601", "flags": []},
  "last_checkpoint": "ISO-8601"
}
```

After creating plan.md, post a `## Decomposition` comment on the Issue:

```bash
gh issue comment $ISSUE_NUMBER --body "$(cat <<'EOF'
## Decomposition

{list of deliverables with size and deps — from plan.md}

**Git strategy:** {mode}, branch: `{branch_name}`
EOF
)"
```

## Step 4 — Implement (subagents per deliverable)

For each batch (respecting deps):

| Deliverable complexity | Subagent tier |
|---|---|
| Simple (config, rename, boilerplate, unit tests) | haiku |
| Medium (new feature, refactor, integration) | sonnet |
| Complex (architecture, multi-file, non-trivial logic) | sonnet |

Parallel deliverables within a batch use `isolation: "worktree"`.

**Decision markers:** After each batch, update `execution-log.md` with:
- Batch status (✅ completed / ❌ failed)
- Decision points for consequential choices made during implementation:
  ```html
  <!-- DECISION: {id} | chose: {choice} | alternatives: {alt1 (reason), alt2 (reason)} | reason: {why} -->
  ```
- If a decision leads to failure:
  ```html
  <!-- DECISION-FAILED: {id} | {what went wrong} | revert-to: {decision-id to revisit} -->
  ```

Mark decisions when: choosing between alternatives (lib, architecture, approach), committing to irreversible technical choices (schema, API contract), or explicitly skipping something. Don't mark routine implementation details.

**Checkpoint after each batch:** update `execution-state.json`:
- Set batch status to `completed` with `completed_at`, `branch`, and `pr` number
- Set next batch to `in_progress` with `started_at`
- Update `last_checkpoint` timestamp

This ensures that if the agent crashes mid-delivery, the next `/delivery #N` resumes from the last completed batch (via Step 1.5).

──▶ **Architectural gate** (if: new DB table, public API change, interface refactor):
> "Created this structure for #N. OK to proceed?"
> Blocks until user approves.

## Step 5 — Validate (sonnet subagent — isolated, generate→critique→refine)

**Critical: the validator receives ONLY:**
1. The Issue spec (from GitHub, not from the implementer's context)
2. The git diff (`git diff main...HEAD`)
3. Decision points from `execution-log.md` (what choices were made and why)
4. Grounding report from Step 2.5 (what external premises were verified)

**The validator does NOT inherit implementation context.**

### 5.1 — Structured critique

Validator produces a **structured critique**, not just pass/fail:

```markdown
## Validation Critique — Issue #N

### Blocking (must fix before merge)
1. **{what's wrong}**
   - Criterion: "{which acceptance criterion}"
   - What's wrong: {specific issue with file:line reference}
   - Fix instruction: {actionable — what to change, where}
   - Files affected: {paths}

### Warnings (should fix, not blocking)
2. **{concern}**
   - Criterion: {related criterion or "best practice"}
   - Suggestion: {what to do}

### Observations (informational)
3. **{note}** — {context}

### Scoring

| Dimension | Result |
|-----------|--------|
| Correctness | N/M criteria met |
| Completeness | N% of criteria addressed |
| Safety | ok / warning / blocking |
| Coherence | high / medium / low (follows codebase patterns?) |
| Regressions | N tests passing, N failing |

**Result: PASS / NEEDS REFINEMENT / FAIL**
```

### 5.2 — Refinement loop (max 2 cycles)

──▶ **If PASS:** proceed to step 6.

──▶ **If NEEDS REFINEMENT** (has blocking items but they're fixable):

**Cycle 1:** Send fix instructions to workers (scoped to specific files/functions):
- Workers receive ONLY the blocking items with fix instructions
- Workers apply targeted fixes (don't redo unaffected batches)
- Validator re-critiques the updated diff

**Cycle 2** (if still has blocking items):
- Refined fix instructions based on what changed
- Workers apply second round of fixes
- Validator final evaluation

──▶ **If still failing after 2 refinement cycles — Failure gate:**
> "Validation failed for #N after 2 refinement cycles. Critique history:
> - Cycle 0: {original issues}
> - Cycle 1: {what was fixed, what persists}
> - Cycle 2: {what was fixed, what persists}
> Remaining blocking items: [list with fix attempts].
> Recommend: {human judgment needed — change approach? override? abandon?}"

──▶ **If FAIL** (fundamental design issue, not fixable with targeted patches):
> "Validation identified fundamental issue for #N: {description}.
> Decision point '{id}' may be the root cause.
> Alternatives from execution-log: {alt1, alt2}.
> Recommend: revisit decision '{id}' or escalate to human."

## Step 6 — Deliver (inline)

1. Open PR:
   ```bash
   gh pr create \
     --title "feat: {issue title}" \
     --body "$(cat <<'EOF'
   ## Summary
   {what was built, 2-3 bullets}

   ## Validation Report
   {from step 5}

   ## Grounding Report
   {from step 2.5 — omit section if grounding was skipped}

   ## Test plan
   - [ ] CI passes
   - [ ] {specific checks}

   Closes #{issue_number}

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

2. CI runs as quality gate.

3. If CI fails: diagnose, fix, push. Never `--no-verify`.

4. Delete temporary files (plan + execution state):
   ```bash
   rm -f .claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/plan.md
   rm -f .claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/execution-state.json
   ```
   Note: `execution-log.md` is NOT deleted — it's the permanent history.

## Rules

- **Never start without acceptance criteria.** If the Issue is underspecified, abort and redirect to `/discovery`.
- **Never bypass validation.** The validator always runs, even for small changes.
- **Checkpoints are not optional.** Architectural gates block. Notification checkpoints log.
- **The plan is internal.** Deliverables D1/D2/D3 never appear in GitHub.
- **CI is the quality gate.** If it fails, fix it. Never skip.
