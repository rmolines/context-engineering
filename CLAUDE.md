# Context Engineering

Session protocol for Claude Code — gives every AI session the right context at the right time.

## Commander's Intent

Make AI-assisted development sessions **stateful by default**. Every session should start knowing what the project is, what's being worked on, and where the important code lives — without the user re-explaining. The system operates in **two worlds**: the human world (GitHub: Issues, PRs, Milestones, Project) for requests and tracking, and the agent world (local disk) for execution context and historical archive. Full architecture in `ARCHITECTURE.md`, philosophy in `CONTEXT-PHILOSOPHY.md`.

Key principles:
- **Two worlds** — human works in GitHub (Issues/PRs), agent works on disk (plans/logs). Issue is the handoff contract.
- **Discovery + Delivery** — upstream (human + Claude define what) → Issue → downstream (Claude alone builds it)
- **Facts first** — >50% of context should be domain facts, not instructions
- **Pointer > prose** — link to code, don't describe it
- **Nothing is disposable** — local docs are historical archive, not ephemeral

## Structure

- `skills/` — 4 core skills (bootstrap, discovery, delivery, persist) + 3 VC skills (spawn, board, fund)
- `hooks/` — lifecycle hooks (post-compact context recovery)
- `rules/` — behavioral rules (session cycle, standards, context docs) — not auto-loaded via plugin; embedded in skills
- `.claude-plugin/plugin.json` — plugin manifest (name: `ce`). Install: `claude --plugin-dir ~/git/context-engineering`
- `templates/` — reusable project templates (CLAUDE.md, milestone, issue, domain map)
- `research/` — foundational research on context engineering
- `tools/context-viz/` — TUI for visualizing session context (Python/Textual)
- `ARCHITECTURE.md` — canonical architecture reference (two worlds, skills, disk structure, GitHub mapping)
- `VC-ARCHITECTURE.md` — canonical VC-Founder reference (3 horizons, spawn/board/fund, founder lifecycle)
- `CONTEXT-PHILOSOPHY.md` — canonical doctrine reference (facts-first, context strategies)

## Canonical patterns

- Skill definition: `skills/bootstrap/SKILL.md` (frontmatter + phases + checklist)
- Architecture: `ARCHITECTURE.md` (two worlds model, end-to-end flow)
- Hook: `hooks/post-compact.md` (lifecycle event handling)
- Template: `templates/claude-md-root.md` (Commander's Intent format)
- Milestone template: `templates/state/milestone.md` (intent + signals)
- Rule: `rules/session-cycle.md` (auto-loaded rule format)

## Commands

No build/test — this is a skill system with docs and templates. Exception: `tools/context-viz/` (Python/Textual, install with `pip install -e tools/context-viz`).

## Context discipline

- **Source of truth: GitHub** — Milestones = goals, Issues = specs/requests, PRs = deliveries
- **Disk structure mirrors GitHub**: `.claude/state/milestones/{slug}/issue-{N}-{slug}/` per Issue
- Each Issue directory: `discovery.md` (research/decisions), `plan.md` (agent decomposition), `execution-log.md` (history)
- `.claude/state/STATE.md` is a **local cache** regenerated from GitHub by `/bootstrap`
- **Projects V2 board** — 1 per repo. Fields: Status, Priority, Size. Views: Board, Roadmap, By Milestone
- **3 detection layers:** `GITHUB_MODE=false` (local only) → `true` (Issues/Milestones) → `PROJECTS_MODE=true` (+ board)
- Before working on an Issue, read its local directory in `.claude/state/milestones/`
- Before ending a task, run `/persist`
