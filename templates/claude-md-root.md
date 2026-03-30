# {Project Name}

<!-- 2-3 lines: what is this project -->

## Direction

<!-- 5-8 lines: product thesis summary, key principles -->
<!-- These lines inform EVERY decision Claude makes. Keep it short and high-signal. -->
<!-- Full strategy doc lives at {path} — read on demand, not @imported. -->

## Canonical patterns

<!-- Point to reference implementations Claude should read before creating something new. -->
<!-- These are more effective than written rules — AI pattern-matches against real code. -->
<!-- Example: -->
<!-- - API route: src/app/api/leads/route.ts (auth + validation + response) -->
<!-- - Server Action: src/app/actions/auth.ts (form action + Zod) -->
<!-- - Dashboard page: src/app/(dashboard)/leads/page.tsx -->

## Structure

<!-- Map of the repo/monorepo. Where things live. -->

## Domain knowledge

<!-- 1-2 lines: pointer to domain map. Loaded when Claude needs to operate on the product. -->
- Domain map in `.claude/docs/index.md` — read before operating on APIs, auth, or data

## Commands

<!-- Build, test, dev commands -->

## Context discipline

<!-- How to work with the context system in this project. -->
- State lives in `.claude/state/STATE.md` (auto-injected every session)
- Before working on an initiative, read its detail file in `.claude/state/`
- Decisions go into `BACKLOG.md` (dated, append-only)
- Before ending a task, run `/persist`
