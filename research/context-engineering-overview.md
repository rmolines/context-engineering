# Context Engineering — Pesquisa Abrangente

> Compilado em 2026-03-26

---

## 1. Definição e Origens

### O que é Context Engineering

Disciplina de projetar e construir sistemas dinâmicos que fornecem ao LLM a informação certa, nas ferramentas certas, no formato certo, no momento certo.

**Andrej Karpathy:**
> "The delicate art and science of filling the context window with just the right information for the next step."

### Quem Popularizou

O termo ganhou tração em **junho de 2025** a partir de dois posts virais:

**Tobi Lutke (CEO do Shopify)** — 18/06/2025:
> "I really like the term 'context engineering' over prompt engineering. It describes the core skill better: the art of providing all the context for the task to be plausibly solvable by the LLM."

**Andrej Karpathy** — endosso no X:
> "+1 for 'context engineering' over 'prompt engineering'. When in every industrial-strength LLM app, context engineering is the delicate art and science of filling the context window."

**Simon Willison** — blog em 27/06/2025: previu que o termo "vai pegar".

**Gartner** — julho 2025: "Context engineering is in, and prompt engineering is out."

---

## 2. Context Engineering vs. Prompt Engineering

| Dimensão | Prompt Engineering | Context Engineering |
|---|---|---|
| Escopo | Uma única entrada de texto | Todo o estado que o modelo vê |
| Foco | Como formular instruções | O que preenche o context window |
| Alcance | Input-output individual | Múltiplos turnos, agentes, sistemas |
| Escala | Manual, iterativo | Arquitetado para reuso e produção |
| Relação | Subconjunto de CE | Superset que engloba prompts |

**Resumo:** prompt engineering é o que você faz *dentro* da janela de contexto; context engineering é como você decide *o que vai preenchê-la*.

---

## 3. Conceitos Centrais e Modelos Mentais

### Os 7 Componentes do Contexto (Phil Schmid)

1. **Instructions / System Prompt** — regras de comportamento, exemplos, restrições
2. **User Prompt** — tarefa ou pergunta imediata
3. **State / History (Short-term Memory)** — histórico da conversa
4. **Long-Term Memory** — conhecimento persistido entre sessões
5. **Retrieved Information (RAG)** — dados externos, documentos, APIs
6. **Available Tools** — funções que o modelo pode invocar
7. **Structured Output** — formato esperado de resposta

### As 4 Estratégias Fundamentais (Lance Martin / LangChain)

1. **Write Context** — persistir informação fora da janela (scratchpads, arquivos, banco de dados)
2. **Select Context** — recuperar apenas o que é relevante (RAG, busca semântica)
3. **Compress Context** — sumarizar ou podar para economizar tokens
4. **Isolate Context** — usar multi-agents ou sandboxes para separar concerns

### Context Rot (Podridão de Contexto)

Documentado pela Anthropic: conforme o contexto cresce, o recall degrada. O modelo tem budget finito de atenção — mais tokens ≠ melhor desempenho. Contextos longos criam:
- Degradação de recall (o modelo "esquece" coisas do meio)
- Fixação em padrões passados em vez de instruções atuais
- Custo quadrático por causa da arquitetura transformer (n² relações)

### "Lost in the Middle" — Position Bias

Pesquisa de Stanford/UC Berkeley/Samaya AI (2023, MIT Press): LLMs seguem um padrão em U — atendem bem ao início e ao fim do contexto, mas ignoram o meio. Causa: Rotary Position Embedding (RoPE) introduz decaimento de longo alcance.

**Implicação prática:** informação crítica deve estar no início ou no fim do contexto, nunca enterrada no meio.

---

## 4. Técnicas e Padrões

### Retrieval e Seleção

- **RAG** — recuperação por embedding antes da inferência. Baseline, não o teto.
- **Just-in-Time Context** — agentes mantêm identificadores leves e carregam dados em runtime via ferramentas, apenas quando necessário.
- **Progressive Disclosure** — o agente descobre contexto incrementalmente por exploração.
- **Hybrid Strategy** — combina retrieval pré-computado (velocidade) com exploração autônoma (flexibilidade). Claude Code usa isso: CLAUDE.md upfront + grep/glob just-in-time.

### Compressão

- **Compaction / Summarization** — sumarizar a trajetória preservando decisões e issues. Claude Code faz auto-compact a 95% da capacidade.
- **Tool Result Clearing** — limpar resultados de ferramentas já processados, preservando a conclusão.
- **Hierarchical Summarization** — sumarização recursiva para contextos muito longos.

### Persistência

- **Structured Note-Taking** — agentes escrevem notas em arquivos externos, relidas conforme necessário.
- **Scratchpad / Extended Thinking** — espaço de trabalho separado para raciocínio. Anthropic reporta +54% em benchmarks.
- **File System as Extended Context** — filosofia do Manus: o sistema de arquivos é memória ilimitada, persistente e restaurável.

### Atenção

- **Objective Recitation** — reescrever periodicamente o resumo da tarefa durante execuções longas, empurrando objetivos críticos para o final do contexto.
- **Error Preservation** — manter ações falhas e stack traces no contexto. O modelo atualiza suas crenças ao ver erros.
- **Context Diversification** — evitar exemplos few-shot repetitivos que disparam mimicry.

### Otimização de Produção (Manus / KV-Cache)

- **KV-Cache hit rate** é a métrica mais crítica em produção
- Prefixos estáveis de prompt (não mudar timestamps, IDs na system prompt)
- Contexto append-only com serialização determinística
- **Mask, não remova ferramentas** — remover ferramentas invalida o KV-cache; use masking de logits
- Custo com cache vs sem cache: diferença de 10x

---

## 5. Aplicação ao Claude Code

### Arquitetura de Contexto

Claude Code é um "harness" — runtime local que envolve o LLM com ferramentas, memória e orquestração. Loop central: **Think → Act → Observe → Repeat** (TAOR). Extensibilidade declarativa via `.md` e `.json`.

### CLAUDE.md — Maior Alavancagem

Carregado em toda sessão. Hierarquia de merging:

```
Enterprise CLAUDE.md
  → ~/.claude/CLAUDE.md (usuário global)
    → ./CLAUDE.md (projeto)
      → subdiretórios/CLAUDE.md
```

**Boas práticas:**
- Estrutura **WHY / WHAT / HOW**
- LLMs seguem ~150-200 instruções com consistência. System prompt do CC já tem ~50. Manter CLAUDE.md < 300 linhas; ideal < 60
- **Universal applicability rule**: só o que se aplica a todas as tarefas
- **Pointers, não copies**: referenciar `file:line`, não copiar código
- **Progressive disclosure**: arquivos separados consultados sob demanda
- **Nunca use para style guidelines**: use linters

### Hooks vs. Instruções

Instruções no CLAUDE.md: ~70% de compliance. Hooks: 100% — determinísticos. Use hooks para ações que não podem falhar.

### Workflow de Contexto Limpo

Para features maiores:
1. Sessão de coleta: Claude entrevista, escreve spec em `SPEC.md`
2. Nova sessão limpa: executa implementação com contexto focado

Previne context rot e fixação em padrões de sessões anteriores.

---

## 6. Pensadores e Líderes

| Pessoa | Contribuição |
|---|---|
| **Tobi Lutke** (Shopify) | Popularizou o termo em junho 2025 |
| **Andrej Karpathy** | Definição canônica |
| **Simon Willison** | Análise e previsão de adoção |
| **Lance Martin** (LangChain) | Framework Write/Select/Compress/Isolate |
| **Manus team** | 6 técnicas de produção para agentes |
| **Dexter Horthy** (HumanLayer) | 12-Factor Agents |
| **Phil Schmid** | 7 componentes do contexto |
| **Bojie Li** | Best practices from Anthropic |

---

## 7. Ferramentas e Frameworks

### Orquestração

| Ferramenta | Descrição |
|---|---|
| **LangChain** (111k stars) | Framework mais influente |
| **LangGraph** | Grafo de estados com context management |
| **Google ADK** | Agent Development Kit |
| **12-Factor Agents** | Framework de 12 princípios |

### Memória e Persistência

| Ferramenta | Descrição |
|---|---|
| **mem0** | Memory layer — short + long-term |
| **Letta (ex-MemGPT)** | Agentes stateful com memory management |
| **graphiti** | Knowledge graphs para memória de agentes |
| **cognee** | Memory management para LLMs |

### Repositórios de Referência

- [yzfly/awesome-context-engineering](https://github.com/yzfly/awesome-context-engineering)
- [jihoo-kim/awesome-context-engineering](https://github.com/jihoo-kim/awesome-context-engineering)
- [Meirtz/Awesome-Context-Engineering](https://github.com/Meirtz/Awesome-Context-Engineering)
- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)

---

## 8. Resultados Práticos

- **Microsoft**: contexto arquitetural → +26% tarefas de software concluídas
- **Enterprise platforms**: +55% velocidade de onboarding, +70% qualidade de output
- **Context windows bem engenhados**: 65% menos erros
- **Limitação de toolset (<30)**: 3x acurácia de seleção de ferramentas
- **Manus**: ratio input:output 100:1, ~50 tool calls/tarefa, 10x economia com KV-cache

---

## 9. Papers Acadêmicos

- **"A Survey of Context Engineering for LLMs"** — arXiv:2507.13334 (julho 2025)
- **"Agentic Context Engineering"** — arXiv:2510.04618 (outubro 2025) — contextos como playbooks evolutivos
- **"Lost in the Middle"** — MIT Press/TACL — position bias em U-shape

---

## 10. Princípio Unificador

> "Find the smallest set of high-signal tokens that maximize the likelihood of some desired outcome." — Anthropic

---

## Fontes

- [Anthropic — Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Manus — Context Engineering for AI Agents](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [LangChain — The Rise of Context Engineering](https://blog.langchain.com/the-rise-of-context-engineering/)
- [Lance Martin — Context Engineering for Agents](https://rlancemartin.github.io/2025/06/23/context_engineering/)
- [Phil Schmid — The New Skill in AI](https://www.philschmid.de/context-engineering)
- [Simon Willison — Context Engineering](https://simonwillison.net/2025/Jun/27/context-engineering/)
- [FlowHunt — Definitive 2025 Guide](https://www.flowhunt.io/blog/context-engineering/)
- [Prompting Guide — Context Engineering Guide](https://www.promptingguide.ai/guides/context-engineering-guide)
- [Galileo — Deep Dive for Agents](https://galileo.ai/blog/context-engineering-for-agents)
- [Weaviate — Context Engineering Blog](https://weaviate.io/blog/context-engineering)
- [Gartner — Context Engineering](https://www.gartner.com/en/articles/context-engineering)
- [mem0 — Context Engineering Guide](https://mem0.ai/blog/context-engineering-ai-agents-guide)
- [Lost in the Middle — MIT Press](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00638/119630/)
