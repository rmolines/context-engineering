# Session & Context Management — snippet for project CLAUDE.md

<!--
  Add this to your project's CLAUDE.md to formalize context management.
  The SessionStart hook auto-injects STATE.md; this snippet adds the rules
  that guide how Claude interacts with the context system.
-->

## Direction

<!-- 5-8 lines: product thesis summary, key principles. What informs every decision. -->
<!-- Full strategy doc: reference but do NOT @import (saves ~3-4k tokens per session) -->

## Context discipline

- State lives in `.claude/state/STATE.md` — auto-injected every session.
- Before working on an initiative or plan, read the linked detail file first.
- Architectural decisions and context that git doesn't capture go into workstream .md files in `.claude/state/`.
- Before ending a significant task, run `/persist`.
- Organic ideas and todos go into STATE.md `## Backlog` — don't let them live only in conversation.
