# Context Engineering

Claude Code plugin — session protocol that gives every AI session the right context at the right time.

## Commander's Intent

Make AI-assisted development sessions **stateful by default**. Every session should start knowing what the project is, what's being worked on, and where the important code lives — without the user re-explaining. The system must be lightweight (always-on budget ~200 lines), fact-first (domain knowledge > behavioral instructions), and self-maintaining (sessions update state, not just consume it). Full philosophy in `CONTEXT-PHILOSOPHY.md`.

Key principles:
- **Facts first** — >50% of context should be domain facts, not instructions
- **Pointer > prose** — link to code, don't describe it
- **Three levels** — Commander's Intent (strategic), Campaigns (operational), Plans (tactical)
- **Write-select-compress-isolate** — the four context strategies, applied systematically

## Structure

- `skills/` — 6 slash commands (bootstrap, discover, plan, run, persist, distill)
- `hooks/` — lifecycle hooks (post-compact context recovery)
- `rules/` — auto-loaded rules (session cycle, standards, context docs)
- `templates/` — reusable project templates (CLAUDE.md, STATE.md, campaigns, domain map)
- `research/` — foundational research on context engineering
- `tools/context-viz/` — TUI for visualizing session context (Python/Textual)
- `CONTEXT-PHILOSOPHY.md` — canonical doctrine reference

## Canonical patterns

- Skill definition: `skills/bootstrap/SKILL.md` (frontmatter + phases + checklist)
- Hook: `hooks/post-compact.md` (lifecycle event handling)
- Template: `templates/claude-md-root.md` (Commander's Intent format)
- Campaign template: `templates/state/campaigns.md` (operational level)
- Rule: `rules/session-cycle.md` (auto-loaded rule format)

## Commands

No build/test — this is a plugin with docs and templates. Exception: `tools/context-viz/` (Python/Textual, install with `pip install -e tools/context-viz`).

## Context discipline

- State lives in `.claude/state/STATE.md` (auto-injected every session)
- Campaigns (operational level) in `.claude/state/campaigns.md`
- Before working on an initiative, read its detail file in `.claude/state/`
- Before ending a task, run `/persist`
