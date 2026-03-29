# Context Visualizer — Conceito
> Data: 2026-03-27

## Problema

Numa sessão do Claude Code, o usuário força o agente a incorporar contexto novo (via discover, plan, leitura de arquivos, pesquisa com subagentes). Mas não tem visibilidade sobre:
- O que tá dentro da janela de contexto agora
- O que já foi comprimido (perdido)
- O que existe em disco e poderia ser puxado
- Quanto espaço livre resta antes da compactação

## Modelo mental

A sessão é uma lista linear de blocos de texto que preenchem o context window de cima pra baixo. Cada bloco tem tipo, tamanho em tokens, e origem.

O visualizador é uma TUI vertical que renderiza essa lista com um ponteiro descendo conforme o contexto cresce, até bater no threshold de compactação.

## Duas visões

### Visão 1: Session Context (o que tá na janela)

Lista vertical de blocos proporcionais ao tamanho em tokens, com ponteiro descendo:

```
╭─ Session Context ─────────────────────── 38k/200k tokens ─╮
│                                                            │
│  ██████████████████░░░░░░░░░░░░░░░░░░░░  19% used         │
│                                                            │
│  STATIC (loaded at start)                                  │
│  ├─ ■ CLAUDE.md + rules          ~2.4k tk                  │
│  ├─ ■ memories (3 files)         ~1.1k tk                  │
│  └─ ■ state/session-protocol.md  ~0.8k tk                  │
│                                                            │
│  INJECTED (you pulled these in)                            │
│  ├─ ■ discover: API do Linear        ~1.2k tk  3min ago    │
│  ├─ ■ discover: Padrões de TUI       ~0.9k tk  2min ago    │
│  ├─ ■ read: src/index.ts             ~0.4k tk  1min ago    │
│  └─ ■ plan: plan-visualizer.md       ~0.6k tk  just now    │
│                                                            │
│  CONVERSATION                                              │
│  └─ ■ messages (12 turns)            ~31.5k tk             │
│                                                            │
│                 ◄── ponteiro: 38k tk (19%)                 │
│                                                            │
│                   (espaço livre)                            │
│                                                            │
├─ 167k ── auto-compact threshold ─────────────────────────  │
│              (buffer de compactação: 33k)                   │
└─ 200k ─────────────────────────────────────────────────────╯
```

**Categorias de blocos:**
- **STATIC** — carregado automaticamente no início (CLAUDE.md, rules, memories, state via hook)
- **INJECTED** — contexto que o usuário forçou (discover, plan, leitura manual, pesquisa)
- **CONVERSATION** — mensagens user/assistant e tool results do fluxo normal

**Cada bloco mostra:**
- Tipo/origem (skill, tool, auto)
- Label descritivo
- Tamanho estimado em tokens
- Tempo desde injeção

**O ponteiro** desce em real-time conforme tokens são consumidos. Quando cruza o threshold de compactação (~167k), tudo acima vira um bloco único de resumo e o ponteiro volta ao topo.

**Fonte de dados:** transcript JSONL da sessão (`transcript_path` via statusline API). Cada entrada do JSONL é um bloco. O visualizador classifica pelo campo `type` e `tool` de cada entrada.

### Visão 2: Context Map (sessão + disco)

Expande a visão 1 com uma segunda zona mostrando contexto disponível em disco que o agente pode puxar se necessário:

```
╭─ IN SESSION (na janela agora) ────────── 38k/200k ───────╮
│                                                            │
│  ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  19%              │
│                                                            │
│  STATIC                                                    │
│  ├─ ■ CLAUDE.md + rules              2.4k tk               │
│  ├─ ■ memories                       1.1k tk               │
│  └─ ■ state/session-protocol.md      0.8k tk               │
│                                                            │
│  INJECTED                                                  │
│  ├─ ■ discover: API do Linear        1.2k tk  3m ago       │
│  └─ ■ plan: plan-visualizer.md       0.6k tk  1m ago       │
│                                                            │
│  CONVERSATION                                              │
│  └─ ■ messages (12 turns)           31.5k tk               │
│                                                            │
╰────────────────────────────────────────────────────────────╯

╭─ ON DISK (disponível pra puxar) ─────────────────────────╮
│                                                            │
│  research/                                    ~18k tk      │
│  ├─ ○ context-window-internals.md        4.2k tk           │
│  ├─ ○ context-engineering-landscape.md   3.8k tk           │
│  ├─ ○ tui-frameworks-techniques.md       5.1k tk           │
│  ├─ ● claude-code-context-engineering.md 2.8k tk  ← used   │
│  └─ ● intra-session-patterns.md         2.1k tk  ← used   │
│                                                            │
│  .claude/state/                               ~1.2k tk    │
│  └─ ● session-protocol.md               1.2k tk  ← in     │
│                                                            │
│  .claude/discoveries/                         ~0k tk      │
│  └─ (vazio)                                                │
│                                                            │
│  memories/                                    ~0.8k tk    │
│  ├─ ● project_purpose.md                0.3k tk  ← in     │
│  └─ ● session_protocol.md               0.5k tk  ← in     │
│                                                            │
╰────────────────────────────────────────────────────────────╯
```

**Marcadores de estado dos arquivos em disco:**
- `■` = está na sessão agora (carregado e presente no contexto)
- `●` = já foi usado nessa sessão (lido via Read/Agent, mas pode ter sido comprimido)
- `○` = disponível mas nunca tocado nessa sessão

**Diretórios escaneados:**
- `research/` — pesquisas documentadas
- `.claude/state/` — state files do projeto (workstreams, planos)
- `.claude/discoveries/` — resultados de discovery persistidos
- `~/.claude/projects/<cwd>/memory/` — memories do projeto

**O cruzamento das duas visões permite decisões informadas:**
- "Tem 3 pesquisas em disco que não puxei, e 80% de janela livre — vale injetar"
- "Tô com 70% de uso, se puxar mais vai forçar compactação — melhor ser seletivo"
- "Esse arquivo já foi usado mas provavelmente comprimiu — preciso re-ler?"

## Fontes de dados

| Dado | Fonte | Acesso |
|---|---|---|
| % de uso do contexto | Statusline API (JSON via stdin) | Polling a cada ~2s |
| Blocos na sessão | transcript JSONL (`transcript_path`) | Leitura do arquivo |
| Arquivos em disco | Filesystem scan dos diretórios conhecidos | Glob no startup + watch |
| Quais arquivos foram lidos | Inferido do transcript (tool_calls com tool=Read) | Parse do JSONL |
| Tamanho em tokens | Estimativa via regra ~4 chars/token ou tiktoken | Cálculo local |
| Compactação aconteceu | Inferido: se % de uso cai abruptamente | Heurística |

## Classificação de blocos (inferida do JSONL)

O transcript JSONL contém entradas com type e tool. Mapeamento:

| Entrada no JSONL | Classificação no visualizador |
|---|---|
| type=user | CONVERSATION: mensagem do usuário |
| type=assistant (sem tool_calls) | CONVERSATION: resposta |
| type=tool_result, tool=Read | INJECTED: leitura de arquivo (label = filename) |
| type=tool_result, tool=Agent | INJECTED: resultado de subagente (label = description) |
| type=tool_result, tool=WebSearch | INJECTED: pesquisa web (label = query) |
| type=tool_result, tool=Grep/Glob | INJECTED: busca no código (label = pattern) |
| type=tool_result, tool=Bash | CONVERSATION: execução de comando |
| System prompt, CLAUDE.md, rules | STATIC: detectado no início do transcript |

## O que não é possível hoje (gaps)

1. **Token count exato por bloco** — só estimativa (~4 chars/token)
2. **Saber o que foi comprimido** — só heurística (queda abrupta no %)
3. **Conteúdo do resumo de compactação** — não acessível programaticamente
4. **Breakdown system vs. conversation vs. tools** — só via `/context` (não programático)

## Decisão de stack

Baseado na pesquisa de TUI frameworks:

**Textual (Python)** é a escolha pragmática:
- Layout proporcional com `fr` units = exatamente o que blocos proporcionais precisam
- `set_interval` pra polling da statusline e transcript
- Python permite iteração rápida e parsing fácil de JSONL
- Não precisa de 60fps — refresh a cada 1-2s é suficiente
- Bonus: Textual Web permite ver no browser também
