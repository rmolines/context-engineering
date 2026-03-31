# Context Engineering

Claude Code plugin — session protocol for persistent context across sessions.

## Direction

A system where every Claude session starts with the right context: what the project is, what you're working on, and where the important code lives. Philosophy: always-on (~200 lines budget) for direction-critical info, progressive disclosure for detail.

## Structure

- `skills/` — 6 slash commands (bootstrap, discover, plan, run, persist, distill)
- `hooks/` — lifecycle hooks (post-compact context recovery)
- `rules/` — auto-loaded rules (session cycle, standards, context docs)
- `templates/` — reusable project templates (CLAUDE.md, STATE.md, domain map, CI)
- `research/` — foundational research on context engineering
- `tools/context-viz/` — TUI for visualizing session context (Python/Textual)
- `CONTEXT-PHILOSOPHY.md` — canonical reference for the full system design

## Commands

No build/test — this is a plugin with documentation and templates, not application code. Exception: `tools/context-viz/` (Python/Textual, install with `pip install -e tools/context-viz`).
