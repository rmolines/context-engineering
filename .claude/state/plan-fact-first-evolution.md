# Plan: Evolução Fact-First do Sistema CE

> Status: completed
> Created: 2026-03-30
> Last updated: 2026-03-30

## Objetivo

Evoluir o sistema de Context Engineering de instrução-first para fact-first. Hoje o sistema é ~90% instruções comportamentais ("como trabalhar") e ~10% fatos do domínio ("o que existe"). A pesquisa (Codified Context paper, ReadMe.LLM, Vercel evals) mostra que a proporção deveria ser inversa — fatos concretos do domínio são mais eficazes que instruções. A mudança se aplica à filosofia, templates, skills e hooks.

### Fundamentos (da pesquisa)

- **Codified Context** (283 sessões, 108k LOC): >50% do conteúdo eficaz são fatos do domínio, não instruções
- **AGENTS.md vs Skills** (Vercel eval): contexto always-on (100%) > retrieval ativo (79%)
- **ReadMe.LLM**: código + exemplos = 5x melhoria vs regras sozinhas
- **Post-compaction hook**: pattern emergente pra re-injetar contexto após compaction
- **Trilogia VS Code**: PRODUCT.md + ARCHITECTURE.md + CONTRIBUTING.md como estrutura
- **Codebase Context Spec**: .context/ directory hierárquico como inspiração

## Deliverables

### D1 — Persistir pesquisa em research/
**O que:** Consolidar os dois rounds de pesquisa (landscape CE + tendências 2026) num arquivo em `research/`. Inclui: achados, fontes, análise de aplicabilidade. Este é o fundamento que justifica todas as outras mudanças.
**Deps:** nenhuma
**Tamanho:** medio

### D2 — Reescrever CONTEXT-PHILOSOPHY.md com paradigma fact-first
**O que:** Reestruturar a filosofia para refletir a mudança de peso: fatos do domínio como conteúdo primário, instruções comportamentais como mínimo necessário. Adicionar: layer de domain knowledge na tabela always-on, princípio de pointer > prosa (código como fonte de verdade), canonical patterns como seção obrigatória, proporção recomendada fatos/instruções. Manter tudo que já existe mas rebalancear.
**Deps:** D1
**Tamanho:** grande

### D3 — Criar template de domain map (.claude/docs/)
**O que:** Template de `index.md` para `.claude/docs/` com seções: API Surface, Auth, Data Model, Canonical Patterns, Env Vars. Cada entrada é pointer anotado pro código (link + 3-5 palavras), não prosa. Inspirado na trilogia VS Code e Codebase Context Spec mas adaptado ao nosso sistema (pointer > prosa).
**Deps:** D2
**Tamanho:** medio

### D4 — Atualizar templates de CLAUDE.md
**O que:** Atualizar `claude-md-root.md` e `claude-md-snippet.md` para incluir: pointer pro domain map, seção de canonical patterns, rebalancear proporção fatos/instruções nos comments guia. O CLAUDE.md passa a ter um pointer "Domain knowledge em .claude/docs/ — ler antes de operar no produto" como always-on.
**Deps:** D3
**Tamanho:** pequeno

### D5 — Atualizar skill /bootstrap init
**O que:** Adicionar step de geração do domain map inicial: scan de APIs (app/api/), server actions ('use server'), auth patterns, DB/ORM, env vars, e identificação de canonical patterns (arquivos de referência). O bootstrap passa a produzir `.claude/docs/index.md` como artefato.
**Deps:** D3
**Tamanho:** medio

### D6 — Atualizar skill /persist com drift detection
**O que:** Adicionar heurística de drift: se git diff mostra mudanças em rotas API, actions, auth, ou schema — e `.claude/docs/` não foi atualizado na mesma sessão — alertar o usuário e sugerir atualização.
**Deps:** D3
**Tamanho:** pequeno

### D7 — Post-compaction hook
**O que:** Adicionar hook SessionStart com matcher `compact` que re-injeta: pointers pro domain map, state ativo, e instruções mínimas. Independente do paradigma fact-first mas de alto impacto pra sessões longas. Atualizar template de hooks e documentar na filosofia.
**Deps:** nenhuma
**Tamanho:** pequeno

### D8 — Rule global: context-documentation
**O que:** Criar `~/.claude/rules/context-documentation.md` com os princípios que o Claude deveria aplicar em qualquer projeto ao documentar ou consumir contexto. Três regras:
1. **Fatos > instruções** — ao documentar projeto, priorizar fatos concretos (endpoints, schema, auth, patterns) sobre instruções comportamentais. Quando escrever CLAUDE.md, standards, ou docs: a maioria do budget deveria ser fatos do domínio.
2. **Pointer > prosa** — ao documentar algo que existe no código, apontar pro arquivo com anotação curta. Não duplicar em prosa. Código é fonte de verdade.
3. **Canonical patterns** — ao criar algo novo, procurar e replicar patterns existentes no projeto antes de inventar. Perguntar "qual arquivo é a referência canônica?"
Estas regras mudam como o Claude opera em qualquer projeto — não só nos que seguem o sistema CE formal.
**Deps:** D2 (a filosofia fundamenta as regras)
**Tamanho:** pequeno

## Git Strategy
**Modo:** single-pr
**Branch:** `agent/fact-first-evolution`
**Razão:** todas as mudanças são no mesmo repo de documentação/pesquisa, coesas, e fazem sentido como um único PR.

## Ordem de execução
**Batch 1:** D1 + D7 (independentes — pesquisa e hook são paralelos)
**Batch 2:** D2 (depende de D1 — filosofia fundamentada na pesquisa)
**Batch 3:** D3 + D4 + D8 (D3 depende de D2; D4 depende de D3 — sequencial; D8 depende de D2 — paralelo com D3)
**Batch 4:** D5 + D6 (dependem de D3 — skills atualizadas em paralelo)

## Context

- Este repo é hub de pesquisa, não app — sem build/test/CI
- Arquivos afetados: `CONTEXT-PHILOSOPHY.md`, `templates/claude-md-*.md`, `~/.claude/skills/bootstrap/SKILL.md`, `~/.claude/skills/persist/SKILL.md`, `~/.claude/rules/context-documentation.md` (novo), `research/` (novo), `templates/docs/` (novo), `templates/hooks/` (existente)
- Após completar aqui, aplicar no Pantheon como primeiro caso de uso (fora de escopo deste plano)

## Execution Log
- D1: concluído (2026-03-30) — pesquisa consolidada em research/ce-landscape-2026.md (132 linhas, 6 key findings, 25+ refs)
- D7: concluído (2026-03-30) — post-compact hook template em templates/post-compact-hook.sh + hooks-config.json
- D2: concluído (2026-03-30) — filosofia reescrita com paradigma fact-first (129 linhas adicionadas, 17 removidas)
- D3: concluído (2026-03-30) — template domain map em templates/docs/index.md (pointer-based, 5 seções)
- D4: concluído (2026-03-30) — templates CLAUDE.md atualizados com canonical patterns + domain knowledge pointer
- D8: concluído (2026-03-30) — rule global ~/.claude/rules/context-documentation.md (3 princípios)
- D5: concluído (2026-03-30) — bootstrap init com step 3 "Gerar domain map" (scan APIs, auth, DB, patterns, env vars)
- D6: concluído (2026-03-30) — persist com drift detection (APIs, auth, schema, actions vs .claude/docs/)
