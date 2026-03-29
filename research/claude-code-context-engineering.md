# Context Engineering para Claude Code CLI — Deep Dive Técnico

> Compilado em 2026-03-26

---

## 1. Arquitetura do Context Window

### Composição Real do Contexto

O Claude Code não usa um system prompt monolítico. São **110+ strings dinâmicas compostas condicionalmente** baseadas no ambiente, configuração e sessão. Contexto total antes do usuário digitar = **~30.000 tokens**.

**Breakdown por componente:**

| Componente | Tokens | % da janela 200K |
|---|---|---|
| System Prompt (base) | ~2.6–3.1k | 1.3–1.6% |
| System Tools (18 built-in) | ~16.8–19.8k | 8.4–9.9% |
| MCP Tools (variável) | 0–26k+ | 0–13%+ |
| Custom Agents (subagents) | ~0.9–2.8k | 0.5–1.4% |
| Memory Files (CLAUDE.md + MEMORY.md) | ~0.3–7.4k | 0.2–3.7% |
| Skills (descrições) | ~0.06–1.0k | 0.03–0.5% |
| Autocompact Buffer | **33k** | **16.5%** |
| Mensagens/histórico | variável | variável |

**Custo por ferramenta built-in:** Grep sozinho = ~300 tokens (inclui docs de sintaxe ripgrep). As 18 tools built-in somam 16–20k tokens por request.

**Custo por MCP tool:** Média de 663–710 tokens (nome ~8t, descrição ~430t, schema ~225t). Servidor MCP com 20 tools = ~14k tokens adicionais.

### O Agentic Loop

Framework oficial: **Explore → Plan → Execute → Commit**

1. Recebe prompt do usuário
2. Usa tools para coletar contexto (Grep, Glob, Read)
3. Age (Edit, Write, Bash)
4. Verifica resultados (Bash para testes, Read para checar outputs)
5. Repete com base no que aprendeu

Uma correção de bug simples: 6–20 tool calls encadeados.

### Como CLAUDE.md É Injetado

CLAUDE.md **NÃO entra no system prompt**. É injetado como **`<system-reminder>`** no array de mensagens.

Implicações:
- Instruções no system prompt têm peso de atenção posicional superior
- CLAUDE.md vence no "o que fazer", perde no "como responder" (tom, verbosidade)
- Para injetar no system prompt: `--append-system-prompt` ou `--system-prompt` (CLI only)
- Razão arquitetural: se CLAUDE.md fosse ao system prompt, cada usuário quebraria o **prompt cache compartilhado** — economicamente inviável

---

## 2. CLAUDE.md — Deep Dive

### Hierarquia Completa (5 Níveis)

| Nível | Localização | Escopo | Compartilhado |
|---|---|---|---|
| **Managed Policy** | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | Org inteira | Todos |
| **User** | `~/.claude/CLAUDE.md` | Todos os projetos | Só você |
| **Project** | `./CLAUDE.md` ou `./.claude/CLAUDE.md` | Um projeto | Time (via git) |
| **Subdir** | `./src/CLAUDE.md` | On-demand ao ler arquivos do dir | Time (via git) |
| **Rules Files** | `.claude/rules/*.md` | Projeto ou usuário | Configurável |

Resolução: Claude sobe o directory tree a partir do CWD carregando todos os CLAUDE.md. Subdir CLAUDE.md carregam on-demand.

### Limites de Tamanho

- **Target**: < 200 linhas por arquivo
- **Ceiling absoluto**: ~300 linhas antes de perder aderência
- **Mínimo eficaz**: 60 linhas
- System prompt do CC já tem ~50 instruções. LLMs seguem ~150-200 com consistência

### Sintaxe de Import

```markdown
@README.md
@package.json
@docs/architecture.md
@~/.claude/personal-prefs.md  # arquivo privado fora do repo
```

Expandidos no launch. Profundidade máxima: 5 hops. Relativo ao arquivo que contém o import.

**HTML comments são removidos antes da injeção:**
```html
<!-- Esta nota é para humanos, NÃO consome tokens -->
```

### Excludes para Monorepos

```json
{ "claudeMdExcludes": ["**/other-team/CLAUDE.md"] }
```

### O Que Incluir (10 Seções Recomendadas)

1. Build e test commands
2. Arquitetura do projeto (diretórios-chave, padrões)
3. Coding conventions
4. Stack e versões
5. Fluxo git (branch naming, commit format)
6. Regras de segurança
7. Anti-patterns a evitar
8. Workflows comuns
9. Compact Instructions
10. Links para docs adicionais

### Anti-Padrões

- Instruções vagas: "Format code properly" → "Use 2-space indentation"
- Conflitos entre arquivos (Claude escolhe arbitrariamente)
- Histórico de projeto (pertence ao git)
- Info que muda frequentemente

---

## 3. Rules Files — `.claude/rules/`

### Estrutura

```
.claude/
├── CLAUDE.md
└── rules/
    ├── code-style.md
    ├── testing.md
    ├── security.md
    ├── frontend/
    │   └── react.md
    └── backend/
        └── api.md
```

Carregados automaticamente com mesma prioridade que `.claude/CLAUDE.md`. Descoberta recursiva.

### Path-Scoped Rules (killer feature)

```yaml
---
paths:
  - "src/api/**/*.ts"
---

# API Rules
- All endpoints must include input validation
```

- Sem `paths` → carrega incondicionalmente
- Com `paths` → carrega quando Claude lê arquivos que fazem match

### Diferença Rules vs CLAUDE.md vs Skills

| Feature | CLAUDE.md | Rules | Skills |
|---|---|---|---|
| Carrega sempre | Sim | Sim (sem paths) / on-demand | Não — só quando invocado |
| Modular | Não | Sim (múltiplos arquivos) | Sim |
| Path-scoped | Não | Sim | Não |
| Tokens | Sempre | Sempre ou on-demand | Mínimo (só descrição) |
| Caso de uso | Contexto geral | Regras por tipo de arquivo | Workflows repetíveis |

---

## 4. Sistema de Memória

### Auto Memory

Localização: `~/.claude/projects/<project>/memory/`

```
memory/
├── MEMORY.md          # Índice, carregado em toda sessão
├── debugging.md       # Notas detalhadas
├── api-conventions.md # Decisões de design
└── ...
```

**Primeiras 200 linhas** do MEMORY.md são carregadas no startup. Após 200 linhas = não carregado.

Topic files (debugging.md, etc.) NÃO carregam no startup — Claude os lê on-demand.

### Subagents com Memória Persistente

```yaml
---
name: code-reviewer
memory: user   # ~/.claude/agent-memory/code-reviewer/
---
```

Escopos: `user`, `project`, `local`

---

## 5. Auto-Compaction

### Mecânica

- **Trigger**: ~83.5% do context window (~167K tokens em janela 200K)
- **Buffer reservado**: 33K tokens (16.5%) — sempre indisponível
- **Espaço efetivo**: ~167K tokens

### Fluxo

1. Detecta aproximação do limite
2. Limpa tool outputs antigos (forma mais leve)
3. Se necessário: gera summary da conversa
4. Cria bloco `compaction` com resumo
5. Descarta mensagens anteriores ao bloco

### O Que Sobrevive

- **CLAUDE.md**: SIM — relido do disco após compaction
- **Instruções na conversa**: NÃO — se perdem
- **Regra**: tudo que importa vai para CLAUDE.md, não para a conversa

### Compact Instructions no CLAUDE.md

```markdown
## Compact Instructions
When compacting, always preserve:
- Complete list of modified files
- Test commands discovered
- Current task state and next steps
- All architectural decisions
```

### Controle Manual

```bash
/compact                           # compaction simples
/compact focus on the API changes  # com foco específico
CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50 # override do threshold
```

---

## 6. Hooks — Context Engineering Determinístico

### Por Que São CE

CLAUDE.md = contexto passivo (~70% compliance). Hooks = **injeção garantida** no momento exato (100%).

### Eventos Principais

| Evento | Pode Bloquear | Uso |
|---|---|---|
| `PreToolUse` | Sim | Security gates, injeção de contexto |
| `PostToolUse` | Não | Formatação automática, logging |
| `UserPromptSubmit` | Sim | Pré-processar prompts |
| `SessionStart` | Não | Carregar contexto inicial |
| `Stop` | Sim | Verificações pós-conclusão |
| `PreCompact` | Não | Preservar info antes de compactar |
| `PostCompact` | Não | Recarregar estado |

### Injeção de Contexto via Hooks

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "Database is currently in read-only mode",
    "updatedInput": { "timeout": 60 }
  }
}
```

### 4 Tipos de Hooks

1. **Command** — shell scripts, JSON via stdin
2. **HTTP** — POST para endpoint
3. **Prompt** — LLM single-turn para validação
4. **Agent** — spawna subagent com ferramentas

### Exemplo Prático: Formatação Automática

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "prettier --write \"$TOOL_INPUT_FILE_PATH\"",
        "async": true
      }]
    }]
  }
}
```

---

## 7. Skills — Injeção On-Demand

### Mecanismo

Quando invocada, o sistema injeta o **conteúdo completo do SKILL.md** como mensagem oculta. Até ser invocada, apenas a descrição (~100 tokens) fica no contexto.

### Custo

- Descrição disponível: ~100 tokens por skill
- Quando invocada: +1.500–7.000 tokens por turno
- Budget de descrições: 2% da context window

### Dynamic Context com Shell

```yaml
---
name: pr-review
---
## PR Context
- Diff: !`gh pr diff`
- Comments: !`gh pr view --comments`
```

Os `` !`comando` `` executam **antes** de Claude ver — preprocessing puro.

### Controle de Invocação

| Config | Você invoca | Claude invoca |
|---|---|---|
| (padrão) | Sim | Sim |
| `disable-model-invocation: true` | Sim | Não |
| `user-invocable: false` | Não | Sim |

### Frontmatter Completo

```yaml
---
name: deploy
description: Deploy to prod
disable-model-invocation: true
allowed-tools: Bash(deploy:*)
model: opus
effort: high
context: fork        # roda em subagent isolado
agent: Explore
hooks:
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
---
```

---

## 8. Subagents e Isolamento de Contexto

### Isolamento Total

Subagent recebe:
- Context window fresca (200K separados)
- Apenas system prompt do subagent
- Prompt passado via Agent tool como único input

**Único canal parent → subagent**: a string do prompt. Inclua tudo que ele precisa.

**Retorno**: apenas output final (~1–2K tokens). Todo trabalho intermediário fica isolado.

### Built-in Subagents

| Subagent | Model | Tools | Uso |
|---|---|---|---|
| **Explore** | Haiku | Read-only | Busca e análise |
| **Plan** | Herda parent | Read-only | Pesquisa em plan mode |
| **general-purpose** | Herda parent | Todas | Multi-step complexo |

### Regras

- Subagents **NÃO podem** spawnar subagents (profundidade máx: 1)
- Auto-compaction independente (~95% de capacidade)
- Podem ter memória persistente e skills precarregadas

### MCP Scoping a Subagents

```yaml
---
name: browser-tester
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
---
```

Parent não vê as tools do Playwright → context window preservado.

---

## 9. MCP e Context

### Impacto

- 50+ tools = 50K–100K tokens antes de você digitar
- Tool Search ativa automaticamente quando MCP > 10% da janela
- Com Tool Search: redução de ~85% no custo de MCP

### Otimização

1. Consolidar tools similares
2. Minimizar descriptions (87 tokens → 12 tokens = 86% redução)
3. Scopar MCP a subagents quando possível

---

## 10. Extended Thinking e Planning

### Palavras-Chave

- `"think"` → thinking padrão
- `"think more"` / `"think harder"` → mais profundo
- `"ultrathink"` → máximo (pode ser colocado em SKILL.md)

### Adaptive Reasoning (Opus 4.6 / Sonnet 4.6)

- `low` → mínimo thinking
- `medium` → default
- `high` → análise complexa
- `max` → máximo (só Opus 4.6)

### Planning Mode

`Shift+Tab` 2x → Plan Mode. Read-only tools, plano para aprovação antes de agir.

---

## 11. Padrões de Power Users

### 1. Feedback Loop Explícito

```
Implement validateEmail. Test cases: 'user@example.com' → true,
'invalid' → false. Run tests after each change.
```

### 2. /clear Entre Tarefas

Limpa histórico, Claude re-lê CLAUDE.md. Usar entre tarefas não relacionadas.

### 3. Just-In-Time em Vez de Pre-Loading

```markdown
# Architecture
- Auth logic: src/auth/handlers.ts
- DB schemas: src/db/models/
- API conventions: docs/api-design.md (read before writing APIs)
```

Referências > cópias. Claude carrega on-demand.

### 4. Símbolos para Compressão de Rules

```
validate:zod | wrap:asyncHandler | log:logger.* !=console.*
```

Mais token-eficiente E mais preciso que prosa.

### 5. Fork Session para Exploração

```bash
claude --continue --fork-session
```

Branch do contexto atual sem afetar sessão original.

### 6. Isolamento de Outputs Verbosos via Subagent

```
Use a subagent to run the full test suite and report only
the failing tests with their error messages.
```

---

## 12. Princípios da Anthropic

### Context Rot

- **~70% uso** → perda de precisão começa
- **~85%** → alucinações aumentam
- **~90%+** → respostas erráticas

### Princípio Fundamental

> "Find the smallest set of high-signal tokens that maximize the likelihood of some desired outcome"

### Hierarquia de Compaction

1. Tool result clearing (mais leve)
2. Conversation summarization
3. External note-taking (MEMORY.md)
4. Sub-agent architectures (cada um com window limpa)

---

## Fontes

- [How Claude Code works — Claude Docs](https://code.claude.com/docs/en/how-claude-code-works)
- [Claude Code System Prompts — Piebald-AI](https://github.com/Piebald-AI/claude-code-system-prompts)
- [Understanding Claude Code's Context Window — Damian Galarza](https://www.damiangalarza.com/posts/2025-12-08-understanding-claude-code-context-window/)
- [Context Buffer Management — claudefa.st](https://claudefa.st/blog/guide/mechanics/context-buffer-management)
- [Memory — Claude Code Docs](https://code.claude.com/docs/en/memory)
- [Hooks Reference — Claude Code Docs](https://code.claude.com/docs/en/hooks)
- [Skills — Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Effective Context Engineering — Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [Hooks for Guaranteed Context Injection — DEV Community](https://dev.to/sasha_podles/claude-code-using-hooks-for-guaranteed-context-injection-2jg)
- [Claude Skills Deep Dive — Lee Han Chung](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Optimising MCP Context — Scott Spence](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)
- [Inside Claude Code's System Prompt — Claude Code Camp](https://www.claudecodecamp.com/p/inside-claude-code-s-system-prompt)
- [Best Practices — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
