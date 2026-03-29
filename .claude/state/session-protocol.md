# Session Protocol — Skills e Hooks de gestão de contexto
> Last updated: 2026-03-29 (worktree parallelism)

## Objetivo
Criar um protocolo estruturado de gestão de contexto entre sessões do Claude Code, substituindo padrões ad-hoc repetitivos por skills, hooks e artefatos persistidos.

## Estado atual
- [x] Pesquisa abrangente sobre Context Engineering
- [x] Deep dive em CE para arquitetura do Claude Code CLI
- [x] Pesquisa sobre padrões intra-sessão
- [x] Design do ciclo: Bootstrap → Discover → Plan → Execute → Persist
- [x] Implementar hook SessionStart (bootstrap automático)
- [x] Implementar hook Stop (safety net pra persistir)
- [x] Implementar skill /bootstrap (reload manual + init)
- [x] Implementar skill /persist (salvar estado)
- [x] Implementar skill /plan (planejamento adaptativo com 3 níveis)
- [x] Implementar skill /discover (ampliação de contexto)
- [x] Implementar skill /run (execução de planos com batches e paralelização)
- [x] Implementar rule global session-cycle.md
- [x] Templates (STATE.md, workstream, snippet CLAUDE.md)
- [x] Separar /plan (planejamento) de /run (execução)
- [x] Formato de plano adaptativo: leve (lista), médio (deliverables+deps), profundo (completo com critério de sucesso e fora de escopo)
- [x] Audit de consistência cross-skill + fixes (persist sem Bash, bootstrap sem planos, etc.)
- [x] Revisão holística: fix hook matchers (clear/compact), Co-Authored-By, flag file, delegate→run port
- [x] Worktree parallelism: /run step 4b reescrito com isolation: "worktree", lifecycle completo, 6 gaps corrigidos
- [x] Formalizar filosofia de CE (CONTEXT-PHILOSOPHY.md)
- [x] Evoluir templates (STATE.md com Initiatives, CLAUDE.md root, snippet)
- [x] Atualizar /persist com roteamento de informação + prompt de continuação
- [x] Criar CLAUDE.md do projeto context-engineering
- [ ] Testar o fluxo completo num projeto real
- [ ] Iterar com base no uso real
- [ ] Aplicar no Pantheon: slimmar @tese-v1.md, limpar BACKLOG/STATE overlap

## Decisões tomadas
- STATE.md como kanban (Backlog/Active/Completed) — base pra gestão visual no futuro
- `.claude/state/` como namespace pra state e planos — separado de discoveries
- `.claude/discoveries/` pra resultados de pesquisa persistidos
- Hooks são safety net (100% determinístico), skills são o fluxo completo (on-demand)
- CLAUDE.md snippet é opcional — hooks já cobrem o bootstrap/persist
- /work removido — quebrado em /discover + /plan + /run (composabilidade > monolito)
- /plan é puro planejamento, /run é pura execução — conectados pelo artefato plan-*.md em disco
- Formato de plano se adapta: leve (lista), médio (deliverables+deps+batches), profundo (completo com critério de sucesso, fora de escopo, implementação detalhada)
- Assess de complexidade pergunta ao usuário (AskUserQuestion) em vez de auto-detect
- Discovery paraleliza agressivamente — não limitado a 2 subagentes
- Rule session-cycle.md como fallback (~70% compliance) pra quando não usa skills
- Paths absolutos nos hooks (não ~) pra evitar problemas de expansão
- Always-on (~200 linhas) vs progressive disclosure como princípio de corte
- CLAUDE.md = estável (direção), STATE.md = dinâmico (estado), skills = on-demand
- Não @importar docs grandes — resumo inline + ponteiro pro doc completo
- /persist sugere mas não edita CLAUDE.md Direction automaticamente (direção é "lei")
- Delegate desativado — melhores padrões (prompt auto-contido, haiku tier) portados pro /run
- SessionStop hook removido — /persist auto-invocável via trigger phrases na description
- Worktrees gerenciados pelo /run, não manualmente — isolation: "worktree" no Agent tool
- Worktrees partem de origin/HEAD (não configurável) — OK pra deliverables independentes, fallback pra inline em retry
- Conflito pós-worktree = parar e reportar (indica overlap que deveria ter sido pego no /plan)
- Validação pós-merge obrigatória (test + tsc + lint) antes de continuar
- .worktreeinclude necessário pra .env — /run cria automaticamente se não existir
- Subagentes de worktree devem rodar em foreground (background não reporta erros)

## Tentativas que falharam
- /work como skill monolítica (Explore+Plan+Execute tudo junto) — quebrado por ser rígido demais
- /plan com execução embutida — separado em /plan + /run pra clareza de responsabilidade

## Pendências e blockers
- Nenhum blocker técnico
- Próximo: aplicar no Pantheon (slimmar tese, limpar BACKLOG/STATE) e testar fluxo real

## Contexto para próxima sessão
- Referência canônica: `CONTEXT-PHILOSOPHY.md` na raiz do repo
- CLAUDE.md do projeto criado — qualquer sessão nova tem contexto
- Skills globais: ~/.claude/skills/ (bootstrap, discover, plan, run, persist, distill)
- Hook: ~/.claude/hooks/session-bootstrap.sh (startup|resume|clear|compact)
- Rules: ~/.claude/rules/ (session-cycle, git-workflow, standards)
- Templates: templates/ (claude-md-root, claude-md-snippet, STATE.md, workstream, CI)
- **Worktree parallelism pronto pra teste** — /run step 4b tem lifecycle completo. Próximo: testar com /plan médio/profundo num projeto real (Pantheon)
- Prompt pronto pra aplicar no Pantheon (slimmar tese + limpar BACKLOG) — colar na sessão de pantheon-os
