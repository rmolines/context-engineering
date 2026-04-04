# Plan: {{issue_title}}
<!-- Issue: #{{issue_number}} | Milestone: {{milestone_title}} -->
<!-- Created: {{date}} | Status: active -->

> This is agent infrastructure — internal decomposition for execution.
> The Issue in GitHub is the source of truth for the spec.

## Decomposition

### D1 — {{deliverable_name}}
**What:** {{description}}
**Size:** small | medium | large
**Deps:** none
**Files:** {{paths}}

### D2 — {{deliverable_name}}
**What:** {{description}}
**Size:** small | medium | large
**Deps:** D1
**Files:** {{paths}}

## Git Strategy

**Mode:** direct-commit | single-pr | pr-per-batch
**Base branch:** main
**Branches:**
- `agent/{{slug}}` → D1 + D2 → PR

## Execution Order

**Batch 1:** D1 (no deps)
**Batch 2:** D2 (depends on D1)

## Context

<!-- Technical decisions, constraints, libs chosen -->
