# Execution Log: {{issue_title}}
<!-- Issue: #{{issue_number}} | Milestone: {{milestone_title}} -->
<!-- Created: {{date}} | Status: active -->

> This log records execution history with marked decision points.
> Decision markers are HTML comments parsed by `/bootstrap` for continuation context.

## Step 2 — Research
<!-- findings, risks, suggested approach -->

## Step 2.5 — Grounding
<!-- grounding report summary, if applicable -->

## Step 3 — Decompose
<!-- deliverables, batches, git strategy -->

## Step 4 — Implement

### Batch 1 — {{batch_description}}
<!-- implementation notes -->

<!-- DECISION: {{id}} | chose: {{choice}} | alternatives: {{alt1 (reason), alt2 (reason)}} | reason: {{why}} -->

<!-- Status: ✅ completed | PR: #N -->

### Batch 2 — {{batch_description}}
<!-- implementation notes -->

<!-- Status: ✅ completed | ⏳ in_progress | ❌ failed -->

## Step 5 — Validate
<!-- validation report summary -->

---

## Decision Marker Reference

Decision markers are HTML comments that `/bootstrap` parses for continuation context.

### Format

```html
<!-- DECISION: {id} | chose: {choice} | alternatives: {alt1 (reason), alt2 (reason)} | reason: {why} -->
```

### When a decision fails

```html
<!-- DECISION-FAILED: {id} | {what went wrong} | revert-to: {decision-id to revisit} -->
```

### When a human overrides a decision

```html
<!-- DECISION-OVERRIDDEN: {id} | original: {choice} | override: {new_choice} | by: human (PR #N comment) | reason: {why} -->
```

### What counts as a decision point

Mark when:
- Choosing between alternatives (library, architecture, approach)
- Committing to a decomposition strategy (batch structure, parallelism)
- Making an irreversible technical choice (schema design, API contract)
- Skipping something explicitly (decided NOT to do X because Y)

Don't mark:
- Implementation details (variable names, file structure)
- Routine steps (ran tests, committed code)
- Information gathering (read file X, searched for Y)
