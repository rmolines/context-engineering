# Context Engineering — Landscape 2025-2026
> Pesquisa: 2026-03-27

## Definição e origem do termo

**Andrej Karpathy (junho/2025)** cunhou a definição que viralizou:
> "Context engineering is the delicate art and science of filling the context window with just the right information for the next step."

Defendeu o termo sobre "prompt engineering" porque captura a complexidade real: não é só o texto do prompt, mas tudo que entra na janela — task descriptions, few-shot examples, RAG, dados, tools, state e history.

**Anthropic (setembro/2025)** publicou "Effective context engineering for AI agents" no engineering blog (~500k views). Tese central: construir agentes eficazes é menos sobre "encontrar as palavras certas" e mais sobre "qual configuração de contexto é mais provável de gerar o comportamento desejado do modelo?"

**Gartner (julho/2025)** formalizou: "Context engineering is in, and prompt engineering is out."

## Framework Write / Select / Compress / Isolate

Lance Martin (LangChain, junho/2025) sistematizou 4 estratégias:

| Estratégia | O que faz | Exemplo no Claude Code |
|---|---|---|
| **Write** | Agente escreve estado externo ao contexto | `/persist` salva state em disco |
| **Select** | Pull de contexto relevante via tools/RAG | `/discover`, `/bootstrap` puxam contexto |
| **Compress** | Sumarização, truncamento, mascaramento | Subagentes retornam só o resumo |
| **Isolate** | Sub-agentes com contextos separados | Agent tool com contexto limpo |

## Técnicas documentadas para sessões longas

- **Scratchpad persistente**: salvar plano e progresso em arquivo, não recriar a cada step
- **Compactação híbrida** (JetBrains Research, dez/2025): observation masking + LLM summarization — -11% custo, +2.6% success rate vs. summarization pura
- **ConversationSummaryBufferMemory**: últimas N interações verbatim + summary comprimido do resto
- **Hierarquias de memória**: short-term (turns recentes) → medium-term (summaries de sessão) → long-term (fatos persistidos)
- **ReAct pattern**: recuperar contexto on demand via tools, não pré-carregar
- **Token budgeting**: max_token_limit explícito com trimming hard ceiling
- **Structured note-taking**: agente mantém notas estruturadas (Anthropic usou pro Claude jogar Pokémon por horas)
- **Anchored summaries** (Factory.ai): rolling summary que preserva fatos que importam

## Padrões de injeção de contexto

### Boas práticas
| Padrão | Descrição |
|---|---|
| **Context Minimization** | Injeta prompt, usa pra decidir ação, depois remove |
| **Lazy Loading via ReAct** | Recupera contexto on demand, não upfront |
| **Proactive Recall** | Pre-processor injeta snippets relevantes antes do LLM |
| **Structured Note-Taking** | Notas estruturadas em vez de histórico bruto |
| **Multi-agent Isolation** | Sub-tarefas em contextos separados; só output final retorna |
| **Repo Overview Injection** | Summary de arquitetura no início, economiza tokens exploratórios |

### Anti-padrões
| Anti-padrão | Por que falha |
|---|---|
| **Context Stuffing** | Despejar tudo → context rot, custo alto |
| **Blind Vector Stuffing** | Injetar todos os chunks do vector DB → snippets irrelevantes |
| **Context Pollution em Multi-agent** | Todos compartilhando mesmo contexto → KV-cache explode |
| **Silent Context Drop** (Cursor) | Descartar arquivos sem aviso → código errado |
| **Laundry List de Edge Cases** | Acumular regras exaustivas → modelo não generaliza |
| **Context Rot por acumulação** | Sessões longas sem compactação → degradação progressiva |

## Como ferramentas gerenciam contexto

### Claude Code
- 200k tokens (1M extended)
- CLAUDE.md como "constituição" persistente (sobrevive compactação)
- Sub-agentes com contexto isolado — retornam Z tokens, não X+Y de exploração
- Auto-compact em ~83,5% de uso
- `/compact` manual com foco opcional

### Cursor
- Normal: 128k tokens; Max: 200k tokens
- Auto-mode silenciosamente descarta arquivos quando enche — sem aviso
- Sessões longas degradam visivelmente

### Windsurf
- Codemaps: mapas visuais anotados da estrutura do código
- Cascade context understanding de arquivos relacionados

## Visualizadores existentes (ou falta deles)

Não existe ferramenta standalone dedicada. O que existe:
- **Context indicator do Claude Code** (VS Code): barra de % de uso
- **Open WebUI** (discussion #9668): feature request pra barra de contexto — não implementado
- **MCP Inspector**: inspeciona protocolo MCP, não contexto do LLM
- **Windsurf Codemaps**: visualização de estrutura de código, não do contexto

**Gap claro**: não há tooling dedicado a visualizar o contexto de sessões com LLMs.

## "Context window as managed resource"

A analogia mais forte emergindo em 2025-2026:

**Factory.ai**: "Effective agentic systems must treat context the way operating systems treat memory and CPU cycles: as finite resources to be budgeted, compacted, and intelligently paged."

**LangChain**: "Context is a compiled view over a richer stateful system. Sessions, memory, and artifacts are the sources. Flows and processors are the compiler pipeline. The working context is the compiled view shipped to the LLM."

O paralelo com OS é recorrente: context window como recurso gerenciado com scheduling, paginação e garbage collection — não buffer passivo.

## Referências do time da Anthropic

O principal: ["Effective context engineering for AI agents"](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (setembro/2025). Pontos centrais:
- Claude Code é o artefato de referência interno
- Structured note-taking pra sessões longas
- Sub-agent architectures: manager → workers em contextos limpos
- Fórmula: "find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome"
- Ganhos reportados: até 54% de melhoria com CE vs. prompt engineering simples

## Fontes
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Andrej Karpathy — definição de context engineering](https://x.com/karpathy/status/1937902205765607626)
- [Context Engineering for Agents — LangChain Blog](https://blog.langchain.com/context-engineering-for-agents/)
- [The New Skill in AI is Not Prompting, It's Context Engineering — Phil Schmid](https://www.philschmid.de/context-engineering)
- [The Context Window Problem — Factory.ai](https://factory.ai/news/context-window-problem)
- [Compressing Context — Factory.ai](https://factory.ai/news/compressing-context)
- [Cutting Through the Noise — JetBrains Research](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- [Context Rot: Why LLMs Degrade — Morph](https://www.morphllm.com/context-rot)
- [Context Management with Subagents — RichSnapp.com](https://www.richsnapp.com/article/2025/10-05-context-management-with-subagents-in-claude-code)
- [Ballooning context in the MCP era — CodeRabbit](https://www.coderabbit.ai/blog/handling-ballooning-context-in-the-mcp-era-context-engineering-on-steroids)
- [Claude's Context Engineering Secrets — Bojie Li](https://01.me/en/2025/12/context-engineering-from-claude/)
