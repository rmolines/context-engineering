---
name: delivery
description: "Downstream: pega Issue especificada e entrega PR com validation report. Autônomo (Claude sozinho). Fases: research, decompose (plan interno), implement (subagentes), validate (subagente isolado), deliver (PR). Triggers: '/delivery #N', 'implementa #N', 'faz #N', 'entrega #N', 'build #N'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch
argument-hint: "#issue-number"
model: sonnet
effort: high
context: fork
---

# /delivery — Downstream execution

**Input:** `$ARGUMENTS` — must be a GitHub Issue number (e.g., `#10`)

> Architecture reference: `ARCHITECTURE.md` § "Delivery — downstream"
> This skill runs in `context: fork` — isolated from the main conversation.

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

## Step 2 — Research (sonnet subagent)

Subagent reads:
- Issue spec (from step 1)
- Relevant code (files mentioned in spec, canonical patterns from domain map)
- External docs (if spec references APIs, libs, or patterns)

Returns: technical context + risks + suggested approach.

──▶ **Notification checkpoint:** "Approaching #N as X in N parts: [summary]"

## Step 3 — Decompose (inline)

Create internal plan at `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/plan.md`

Using template: `templates/state/issue/plan.md`

- Break into deliverables (D1, D2, ...)
- Identify deps and batches
- Define git strategy (direct-commit, single-pr, pr-per-batch)
- Map file domains for parallel work

This is agent infrastructure. Deliverables do NOT become GitHub Issues.

## Step 4 — Implement (subagents per deliverable)

For each batch (respecting deps):

| Deliverable complexity | Subagent tier |
|---|---|
| Simple (config, rename, boilerplate, unit tests) | haiku |
| Medium (new feature, refactor, integration) | sonnet |
| Complex (architecture, multi-file, non-trivial logic) | sonnet |

Parallel deliverables within a batch use `isolation: "worktree"`.

Log progress to `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/execution-log.md`

──▶ **Architectural gate** (if: new DB table, public API change, interface refactor):
> "Created this structure for #N. OK to proceed?"
> Blocks until user approves.

## Step 5 — Validate (sonnet subagent — isolated)

**Critical: the validator receives ONLY:**
1. The Issue spec (from GitHub, not from the implementer's context)
2. The git diff (`git diff main...HEAD`)

**The validator does NOT inherit implementation context.**

Validator checks each acceptance criterion against the diff:

```markdown
## Validation Report — Issue #N

| Criterion | Status | Evidence |
|-----------|--------|----------|
| criterion 1 | pass | found in src/auth/refresh.ts:L45 |
| criterion 2 | pass | test in tests/refresh.test.ts |
| criterion 3 | fail | not found in diff |

**Result: PASS / FAIL**
```

──▶ **If PASS:** proceed to step 6.
──▶ **If FAIL — Failure gate:**
> "Validation failed for #N. Criteria not met: [list]. Fix or accept?"
> If fix: loop back to step 4 for the failing criteria.
> If accept: proceed with note in PR body.

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

4. Save execution log to `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/execution-log.md`

## Rules

- **Never start without acceptance criteria.** If the Issue is underspecified, abort and redirect to `/discovery`.
- **Never bypass validation.** The validator always runs, even for small changes.
- **Checkpoints are not optional.** Architectural gates block. Notification checkpoints log.
- **The plan is internal.** Deliverables D1/D2/D3 never appear in GitHub.
- **CI is the quality gate.** If it fails, fix it. Never skip.
