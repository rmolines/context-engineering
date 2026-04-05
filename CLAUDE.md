# Context Engineering

Context management layer for Claude Code — configures, optimizes, and extends the native context architecture so every session starts with the right context.

## Commander's Intent

Make AI-assisted development sessions **stateful by default**. CE manages both native Claude Code layers (CLAUDE.md, rules, memory, hooks) and creates new ones (state tracking, domain maps, milestone docs). The system operates in **two worlds**: the human world (GitHub: Issues, PRs, Milestones, Project) for requests and tracking, and the agent world (local disk) for execution context and historical archive. Full architecture in `ARCHITECTURE.md`.

Key principles:
- **Two worlds** — human works in GitHub (Issues/PRs), agent works on disk (plans/logs). Issue is the handoff contract.
- **Discovery + Delivery** — upstream (human + Claude define what) → Issue → downstream (Claude alone builds it)
- **Facts first** — >50% of context should be domain facts, not instructions
- **Pointer > prose** — link to code, don't describe it
- **Nothing is disposable** — local docs are historical archive, not ephemeral

## Structure

- `skills/` — 6 skills: init (setup), bootstrap (session), discovery (upstream), delivery (downstream), persist (save), distill (meta)
- `hooks/` — lifecycle hooks (post-compact context recovery)
- `rules/` — behavioral rules (session cycle, standards, context docs)
- `.claude-plugin/plugin.json` — plugin manifest (name: `ce`). Install: `claude --plugin-dir ~/git/context-engineering`
- `templates/` — reusable project templates (CLAUDE.md, milestone, issue, domain map)
- `research/` — foundational research on context engineering
- `tools/context-viz/` — TUI for visualizing session context (Python/Textual)
- `ARCHITECTURE.md` — canonical reference (philosophy, two worlds, skills, disk structure, GitHub mapping)

## Canonical patterns

- Skill definition: `skills/bootstrap/SKILL.md` (frontmatter + phases + checklist)
- Architecture: `ARCHITECTURE.md` (foundation, philosophy, two worlds, end-to-end flow)
- Hook: `hooks/post-compact.sh` (lifecycle event handling)
- Template: `templates/claude-md-root.md` (Commander's Intent format)
- Milestone template: `templates/state/milestones/milestone.md` (intent + signals)
- Rule: `rules/session-cycle.md` (auto-loaded rule format)

## Commands

No build/test — this is a skill system with docs and templates. Exception: `tools/context-viz/` (Python/Textual, install with `pip install -e tools/context-viz`).

## Context discipline

- **Source of truth: GitHub** — Milestones = goals, Issues = specs/requests, PRs = deliveries
- **Two skills for setup vs session:** `/init` once per project (infra), `/bootstrap` every session (context)
- **Disk structure mirrors GitHub**: `.claude/state/milestones/{slug}/issue-{N}-{slug}/` per Issue
- Each Issue directory: `discovery.md` (research/decisions), `plan.md` (agent decomposition), `execution-log.md` (history)
- `.claude/state/STATE.md` is a **session buffer** regenerated live from GitHub by `/bootstrap`
- **3 detection layers:** `GITHUB_MODE=false` (local only) → `true` (Issues/Milestones) → `PROJECTS_MODE=true` (+ board)
- Before working on an Issue, read its local directory in `.claude/state/milestones/`
- Before ending a task, run `/persist`
