# Context Engineering — Domain Map

Project: `context-engineering` — Context management layer for Claude Code. Configures native layers and creates new ones for stateful AI-assisted development.
Type: **Meta-project** (framework for Claude Code sessions, not a shipping app).

---

## Skills Surface

**Infra Skill** — project setup

- [init](../../skills/init/SKILL.md) — Set up CE: CLAUDE.md, domain map, dirs, GitHub labels/milestones/Projects V2. Idempotent.

**Core Skills** — session lifecycle

- [bootstrap](../../skills/bootstrap/SKILL.md) — Session context: live GitHub query, deep context loading, briefing, alignment.
- [discovery](../../skills/discovery/SKILL.md) — Upstream: transform request → spec'd GitHub Issue. Human + Claude collab.
- [delivery](../../skills/delivery/SKILL.md) — Downstream: Issue → researched, decomposed, implemented, validated, PRd. Claude solo.
- [persist](../../skills/persist/SKILL.md) — End-of-session: save execution log, update signals, commit. Manual or hooked.

**Supplemental Skills**

- [distill](../../skills/distill/SKILL.md) — Extract repeated pattern from session → new skill or update existing.
- [plan](../../skills/plan/SKILL.md) — (deprecated, use /delivery) Decompose task into deliverables.
- [run](../../skills/run/SKILL.md) — (deprecated, use /delivery) Execute plans.

---

## Disk Structure

**Root context**
- [`CLAUDE.md`](../../CLAUDE.md) — Commander's Intent. Context management layer goals, principles, structure.
- [`ARCHITECTURE.md`](../../ARCHITECTURE.md) — Canonical reference: philosophy, context sources & routing, skills, disk structure, GitHub mapping.
- `README.md` — Quickstart for users.

**Session & State**
- `.claude/state/STATE.md` — Session buffer of active Issues/Milestones (regenerated live by `/bootstrap`).
- `.claude/state/milestones/{slug}/milestone.md` — Campaign intent, success state, signals (local docs per Milestone).
- `.claude/state/milestones/{slug}/issue-{N}-{slug}/discovery.md` — Decision log, UX spec, acceptance criteria.
- `.claude/state/milestones/{slug}/issue-{N}-{slug}/plan.md` — Decomposition, deliverable status, owner assignment.
- `.claude/state/milestones/{slug}/issue-{N}-{slug}/execution-log.md` — Session by session: work done, next steps, learnings.
- `.claude/docs/index.md` — This file. Project domain/surface map.

**Plugin & Hooks**
- [`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json) — Plugin manifest. Name: `ce`. Installs 6 skills + rules.
- [`hooks/hooks.json`](../../hooks/hooks.json) — Lifecycle hooks (e.g., post-compact context recovery).
- [`hooks/post-compact.md`](../../hooks/post-compact.md) — Hook handler to reload context after Claude's message compression.

**Skills & Rules**
- `skills/` — Skill definitions. Format: `skills/{name}/SKILL.md`.
  - `skills/init/` — Infra skill: project setup.
  - `skills/bootstrap/` — Core skill: session context loading.
  - `skills/discovery/` — Core skill: upstream (request → Issue).
  - `skills/delivery/` — Core skill: downstream (Issue → PR).
  - `skills/persist/` — Core skill: session state persistence.
  - `skills/distill/` — Supplemental: workflow crystallization.
  - `skills/plan/`, `skills/run/` — Deprecated (use /delivery).
  - `skills/shared/` — Shared markdown docs (e.g., `github-detection.md`).

- `rules/` — Behavioral rules (NOT auto-loaded; embedded in CLAUDE.md or skill bodies).
  - `rules/session-cycle.md` — Explore → Plan → Execute cycle.
  - `rules/standards.md` — 6 standards checklist.
  - `rules/context-documentation.md` — Facts > instructions, pointer > prose.
  - `rules/agency.md` — `/agency:kam` operating model.

**Templates & Scaffolds**
- `templates/claude-md-root.md` — Template for project CLAUDE.md (Commander's Intent format).
- `templates/state/milestone.md` — Template for campaign milestone.md files.
- `templates/state/issue/` — Templates for discovery.md, plan.md, execution-log.md.
- `templates/ci/` — GitHub Actions CI templates (lang-agnostic).

**Research & Docs**
- [`research/llm-knowledge-base-pattern.md`](../../research/llm-knowledge-base-pattern.md) — Search + context synthesis pattern for long-term project memory.
- `ARCHITECTURE.md` — Canonical reference: philosophy (facts-first, pointer > prose), context sources & routing, skills, state flows, GitHub integration.

---

## GitHub Integration

**Source of Truth:** GitHub Issues, Milestones, Projects V2 board.

- **Issues** — Feature specs, bugs, tasks. Labels: `type:`, `status:`, `size:`, `milestone:`, `ai-generated`.
- **Milestones** — Campaigns. Title: `[CN] Name`. Description: intent, success state, signals.
- **Projects V2** — Board view (status columns), Roadmap view (start/target dates). Custom fields: Priority, Size, Start Date, Target Date.

**Detection Layers** (3 levels of GitHub connectivity):

1. **GITHUB_MODE=false** — Local-only. No GitHub. `/bootstrap` skips sync.
2. **GITHUB_MODE=true** — Issues/Milestones as source of truth. Labels auto-created, STATE.md regenerated, Issues → disk structure.
3. **PROJECTS_MODE=true** — +Projects V2 board. Custom fields, auto-link Issues to board.

**Git Workflow**
- Branch naming: `agent/{ticket-id}-{description}` or `agent/{description}`.
- Commits: conventional format (`feat:`, `fix:`, etc.), English, include `Co-Authored-By` footer.
- PRs: auto-create via `/run`, auto-merge on CI pass, squash merge → 1 commit per PR on main.
- Worktrees: `/run` uses `isolation: "worktree"` for parallel deliverables. Each subagent gets isolated copy.

---

## Execution Flow

```
/init (once) → set up CE layers in the project
       ↓
/bootstrap (each session) → load context, briefing, align
       ↓
/discovery (if spec needed) → Issue spec'd + labeled
       ↓
/delivery #N → research, decompose, implement, validate, PR
       ↓
PR created, CI runs, auto-merges on pass
       ↓
/persist (eod) → execution log, signals updated
       ↓
[Next session: /bootstrap loads fresh context, continues]
```

---

## Canonical Patterns

1. **Skill definition** — See `skills/bootstrap/SKILL.md`: frontmatter (name, description, triggers), phases, checklist.
2. **Issue discovery** — See `templates/state/issue/discovery.md`: decisions, UX flow, acceptance criteria.
3. **Plan decomposition** — See `templates/state/issue/plan.md`: deliverables, dependencies, owner, status.
4. **Execution log** — See `templates/state/issue/execution-log.md`: session-by-session work, next steps, learnings.
5. **Milestone signals** — See `.claude/state/milestones/c1-dogfooding/milestone.md`: dated signals from sessions, strategic review log.
6. **GitHub Issue → disk structure mapping** — See `ARCHITECTURE.md` § "Disk structure mirrors GitHub".

---

## Project State

Loaded dynamically by `/bootstrap` — see `.claude/state/STATE.md`.

---

Last updated: 2026-04-05.
