# Padrões Intra-Sessão com AI Coding Agents

> Compilado em 2026-03-26

---

## 1. O Framework Universal

Toda a literatura converge em:

```
Discover → Plan → Execute → Review → Ship
```

Quando a fase de planejamento é pulada, ciclos de retrabalho aumentam significativamente. Times internos da Anthropic reportam grandes reduções quando steps 1 e 2 nunca são ignorados.

---

## 2. Discovery / Pesquisa

### Interna (codebase)

- Usar `plan mode` (read-only) para exploração antes de qualquer escrita
- Pedir: "Read the codebase and ask me clarifying questions before proposing anything"
- 72.6% dos projetos CC especificam arquitetura no CLAUDE.md
- Projetos com AGENTS.md bem estruturado: 29% redução no runtime, 17% menos outputs
- Arquitetura híbrida: CLAUDE.md upfront + glob/grep just-in-time

### Externa (web, docs)

- Descoberta interna primeiro → gap identificado → busca externa pontual
- Combinar knowledge cutoff com WebSearch pra APIs e versões

---

## 3. Planning e Decomposição

### Plan Mode (Claude Code)

Read-only tools, perguntas clarificadoras, plano para aprovação antes de agir. `Shift+Tab` 2x.

### Effort Level

Ultrathink depreciado em janeiro 2026. Thinking habilitado por padrão. `/effort` controla budget:
- `low` — trivial
- `medium` — default
- `high` — decisões arquiteturais complexas

### Spec-Driven Development (SDD)

Padrão mais importante emergido em 2025. Spec é o artefato primário; código é output derivado.

1. Agente analisa requisitos → gera design + plano
2. Humano revisa em loop iterativo
3. Spec aprovada → agente implementa
4. Código = output, não input

**Ferramentas:**
- GitHub Spec-Kit
- cc-sdd (Claude Code + Cursor + Copilot + Gemini CLI)
- Amazon Kiro (IDE com SDD nativo)
- BMAD Method (multi-agente completo)

**Addy Osmani (Google Chrome team):**
> "Specs, skills, MCPs, small iterative chunks, and always review what the AI suggests."

---

## 4. Execução

### Granularidade

- Uma função, um bug, uma feature por vez
- Decomposição antes de execução
- Prompts monolíticos → outputs frágeis

### Controle vs Autonomia

72% dos devs profissionais: "vibe coding NÃO faz parte do trabalho profissional".

**Modelo operacional convergente:**
- AI agents: primeira passagem, scaffolding, implementação, testes
- Engenheiros: revisão, verificação de risco, alinhamento
- Humanos mantêm: arquitetura, trade-offs, ownership

### Git Worktrees

- `claude --worktree` para paralelização real
- Zero interferência entre sessões
- Limitação: worktrees isolam código, não ambiente (DB, Docker compartilhados)

---

## 5. Orquestração Multi-Agente

### Subagents vs Agent Teams

| Subagents | Agent Teams |
|---|---|
| Resultado retorna ao caller | Comunicação direta entre teammates |
| Tarefas paralelas isoladas | Coordenação com compartilhamento |

### Padrões Canônicos (Anthropic)

1. **Parallelization / Fan-out**: workers simultâneos, outputs agregados
2. **Orchestrator-Workers**: LLM central decompõe e delega dinamicamente
3. **Plan/Execute com model routing**: Opus planeja, Sonnet/Haiku executa
4. **Generator-Evaluator**: um gera, outro avalia em loop
5. **ReAct**: raciocínio + ação em steps pequenos

### BMAD Method

- Analyst Agent → project brief
- PM Agent → PRD
- Architect Agent → design de sistema
- Zero código antes de documentação validada
- Port: [BMAD-AT-CLAUDE](https://github.com/24601/BMAD-AT-CLAUDE)

### Princípio Core Anthropic

> "Start with simple prompts, add multi-step agentic systems ONLY when simpler solutions fall short."

---

## 6. Refinamento Iterativo

```
Execute → Fail → Feed error → Retry → Validate → Continue
```

- Self-refinement: -30% erros em benchmarks
- Validação a cada step, não no final
- Rollback se step falha após N retries
- Fail gracefully com mensagens acionáveis

---

## 7. O Espectro Vibes vs Estruturado

| Vibes (baixa estrutura) | Estruturado |
|---|---|
| Exploração, protótipos | Código de produção |
| Tasks triviais | Dependências complexas |
| Bugfixes simples | Refatorações em larga escala |
| API nova | Mudanças arquiteturais |

> "Coherence Through Orchestration, Not Autonomy" — Mike Mason, 2026

---

## Fontes

- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic: Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Addy Osmani: LLM Coding Workflow 2026](https://addyosmani.com/blog/ai-coding-workflow/)
- [Martin Fowler: Context Engineering for Coding Agents](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html)
- [SDD with Claude Code](https://alexop.dev/posts/spec-driven-development-claude-code-in-action/)
- [Thoughtworks: SDD 2025](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)
- [BMAD Method](https://docs.bmad-method.org/)
- [arXiv: Devs Don't Vibe, They Control](https://arxiv.org/html/2512.14012)
- [Anthropic: Agentic Coding Trends 2026](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)
- [Mike Mason: Coherence Through Orchestration](https://mikemason.ca/writing/ai-coding-agents-jan-2026/)
- [Claude Code Docs: Best Practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code Docs: Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Docs: Agent Teams](https://code.claude.com/docs/en/agent-teams)
