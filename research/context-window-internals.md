# Context Window Internals — Claude Code
> Pesquisa: 2026-03-27

## Como a janela de contexto é gerenciada

Cada sessão começa com context window zerado. A janela tem 200k tokens por padrão (1M com extended context, GA desde março 2026). O CLI funciona como agentic harness: gerencia o preenchimento com mensagens, tool calls, resultados, arquivos e instruções.

O contexto é linear — tudo que foi lido, executado e respondido ocupa espaço. A sessão persiste como `.jsonl` em `~/.claude/projects/<encoded-cwd>/*.jsonl`.

Não existe memória automática entre sessões. O que persiste é carregado explicitamente (CLAUDE.md, MEMORY.md).

## Distribuição de tokens

| Componente | Tokens aprox. | % da janela (200k) |
|---|---|---|
| System prompt | ~4.200 | 2,1% |
| System tools | ~16.800 | 8,4% |
| Custom agents | ~1.300 | 0,7% |
| Memory files (MEMORY.md) | ~680–7.400 | 0,3–3,7% |
| Skills | ~1.000 | 0,5% |
| MCP tools (deferred, só nomes) | ~120 | ~0,06% |
| Environment info | ~280 | 0,1% |
| **Buffer de auto-compact** | **~33.000** | **16,5%** |
| **Total overhead pré-conversa** | **~30–40k** | **15–20%** |
| Mensagens e tool calls | variável | restante |

O `used_percentage` da statusline é calculado com input tokens: `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. Output tokens não entram.

## Compactação automática

Opera em três camadas:

### Microcompactação (contínua)
Tool outputs volumosos são salvos em disco e substituídos por referência no contexto. Resultados recentes ficam inline, antigos viram referências. Transparente e contínua.

### Auto-compactação (limiar ~83,5%)
Dispara quando uso atinge ~83,5% (reservando ~33k tokens pro processo de sumarização). O processo:
1. Claude gera resumo estruturado de toda a conversa
2. Histórico completo é substituído pelo resumo
3. Sessão continua com resumo como nova base

**Preservado no resumo:** intenção do usuário, decisões técnicas, arquivos modificados, erros e soluções, tarefas, estado atual, próximo passo.

**Perdido:** nomes de variáveis específicos, mensagens de erro exatas, nuances de decisões do início, outputs verbosos.

**Importante:** CLAUDE.md sobrevive à compactação — é re-lido do disco e re-injetado fresco. Instruções dadas apenas na conversa são perdidas.

### Compactação manual (`/compact`)
Invocada pelo usuário, aceita foco: `/compact focus on API changes`. Após compactação, re-lê arquivos acessados recentemente.

### Controles
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (1-100): controla quando auto-compact dispara
- `autoCompact: false` em `~/.claude/settings.json`: desabilita (mas há relatos de ser ignorado)
- Múltiplas compactações causam perda cumulativa — qualidade degrada progressivamente

## Como CLAUDE.md, rules, memories e hooks ocupam contexto

### CLAUDE.md
- Carregado integralmente (recomendação: < 200 linhas)
- Injetado como user message após system prompt (não é parte do system prompt)
- Hierarquia: managed policy → user (`~/.claude/CLAUDE.md`) → project (`./CLAUDE.md`) → subdir (on-demand)
- HTML comments (`<!-- -->`) removidos antes da injeção

### Rules (`.claude/rules/`)
- Sem `paths` frontmatter: carregadas no início como CLAUDE.md
- Com `paths` frontmatter: carregadas on-demand quando Claude trabalha com arquivos matching

### Auto memory (MEMORY.md)
- Apenas primeiros 200 linhas ou 25KB carregados automaticamente
- Topic files (`*.md` na pasta memory) não carregam no startup — lidos on-demand
- Compartilhado entre worktrees do mesmo git repo

### Hooks
- Definições em settings.json consomem tokens no contexto de configuração
- Output dos hooks volta como tool results
- Hooks pesados podem ser filtrados via PreToolUse

### MCP tools
- Deferred por padrão: só nomes no contexto (~120 tokens)
- Schemas completos carregam quando Claude usa a tool (via tool search)
- `ENABLE_TOOL_SEARCH=false` força carregamento upfront de todos os schemas

## APIs e mecanismos de observabilidade

### Statusline API (mais completa)
Scripts de statusline recebem JSON via stdin:
```json
{
  "context_window": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4521,
    "context_window_size": 200000,
    "used_percentage": 8,
    "remaining_percentage": 92,
    "current_usage": {
      "input_tokens": 8500,
      "output_tokens": 1200,
      "cache_creation_input_tokens": 5000,
      "cache_read_input_tokens": 2000
    }
  },
  "session_id": "abc123...",
  "transcript_path": "/path/to/transcript.jsonl",
  "cost": { "total_cost_usd": 0.01234 },
  "rate_limits": { "five_hour": { "used_percentage": 23.5 } }
}
```

### Comandos internos
- `/context` — breakdown detalhado do que consome espaço
- `/cost` — uso de tokens e custo da sessão
- `/stats` — padrões de uso (Pro/Max)

### Limitações
- Modelo não tem acesso programático ao próprio `session_id` e `context_window_used_percentage` durante tool calls (feature request #36678)
- Hooks não recebem dados de contexto por padrão (feature requests #6577, #11535, #29829)

### API de Compactação (beta)
Disponível desde janeiro 2026 via header `compact-2026-01-12`:
```python
response = client.beta.messages.create(
    betas=["compact-2026-01-12"],
    model="claude-opus-4-6",
    context_management={"edits": [{"type": "compact_20260112"}]},
)
```

## Implicações para o visualizador

### O que é possível hoje
1. **Statusline** dá % de uso e tokens em real-time (polling)
2. **transcript_path** permite ler o `.jsonl` da sessão e inferir o que foi injetado
3. **Log de injeção** (a criar) — cada skill registra o que injetou com estimativa de tokens

### O que não é possível (gaps)
1. Saber exatamente o que foi comprimido e quando
2. Modelo acessar seu próprio usage durante execução
3. Breakdown granular automático (system vs. conversation vs. tools) fora do `/context`

### Fontes cruzadas para a TUI
- Statusline → "quanto tá cheio" (real-time)
- Log de injeção → "com o quê" (rastreamento)
- Heurística de compressão → "o que provavelmente já foi perdido" (estimativa)

## Fontes
- [Claude Code Context Buffer: The 33K-45K Token Problem](https://claudefa.st/blog/guide/mechanics/context-buffer-management)
- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [How Claude remembers your project](https://code.claude.com/docs/en/memory)
- [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
- [Manage costs effectively](https://code.claude.com/docs/en/costs)
- [Customize your status line](https://code.claude.com/docs/en/statusline)
- [Session Management — Anthropic Docs](https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-sessions)
- [Expose session_id and context_window usage — Issue #36678](https://github.com/anthropics/claude-code/issues/36678)
- [Context Compaction Research](https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f)
