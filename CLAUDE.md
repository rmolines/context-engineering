# Context Engineering

Hub de pesquisa, experimentação e tooling sobre context engineering para Claude Code.

## Direction

Construir e formalizar um sistema de gestão de contexto entre sessões que seja auto-sustentável — o Claude de qualquer sessão sabe o que fazer sem depender do usuário re-explicar. Filosofia: always-on (~200 linhas budget) vs progressive disclosure (detail files sob demanda). Princípio de corte: se Claude erraria a direção sem a info, é always-on; se só erraria o detalhe, é disclosure.

## Reference

- `CONTEXT-PHILOSOPHY.md` — filosofia e arquitetura canônica do sistema
- `research/` — pesquisa fundacional (CE overview, landscape, Claude Code internals, intra-session patterns)
- `templates/` — templates reutilizáveis (STATE.md, CLAUDE.md root, CLAUDE.md snippet, CI, workstream)
- `tools/context-viz/` — TUI visualizador de contexto de sessão (Textual/Python)

## How it's applied

Skills globais em `~/.claude/skills/` (bootstrap, discover, plan, run, persist, distill). Hook em `~/.claude/hooks/session-bootstrap.sh` (SessionStart). Rules em `~/.claude/rules/` (session-cycle, git-workflow, standards). Este repo é a referência — projetos que aplicam (ex: Pantheon) usam os templates e seguem a filosofia.

## Commands

Sem build/test — este repo é hub de pesquisa e documentação, não código de aplicação. A exceção é `tools/context-viz/` (Python/Textual).
