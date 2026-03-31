---
name: discover
description: "Pesquisa e amplia contexto antes de agir. Discovery interno (codebase), externo (web/docs), ou ambos. Usar quando precisar entender algo antes de decidir ou implementar. Triggers: '/discover', 'pesquisa sobre', 'faz um discovery', 'quero entender X', 'investiga X', 'levanta contexto sobre'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch
argument-hint: "[tópico | --internal tópico | --external tópico]"
---

# /discover — Ampliação de contexto

Sua missão é trazer conhecimento relevante pro contexto da sessão — interno (codebase) e/ou externo (web, docs, APIs).

**Input:** `$ARGUMENTS`

---

## 1. Entender o escopo

Se o input está vago, pergunte ao usuário com AskUserQuestion:
- O que quer descobrir?
- É sobre o codebase, sobre algo externo, ou ambos?

Parse flags se presentes:
- `--internal` → só codebase
- `--external` → só web/docs
- Sem flag → avalie o tópico e decida. Na dúvida, faça ambos.

## 2. Planejar a pesquisa

Antes de sair pesquisando, pense:
- Que perguntas específicas preciso responder?
- Onde a informação provavelmente está? (quais arquivos, quais sites, quais docs)
- Quais pesquisas posso rodar em paralelo?

## 3. Executar

Delegue a subagentes (model: sonnet) pra proteger o contexto principal. Paralelize agressivamente — não se limite a 2 subagentes. Use quantos fizerem sentido pra cobrir o escopo:

**Exemplos de paralelização:**

Discovery simples (1 eixo):
- 1 subagente interno OU 1 externo

Discovery médio (2 eixos):
- 1 subagente interno (codebase) + 1 externo (web)

Discovery amplo (N eixos):
- 1 subagente pra explorar arquitetura do codebase
- 1 subagente pra pesquisar docs da API X
- 1 subagente pra pesquisar best practices de Y
- 1 subagente pra analisar git log e entender histórico

**Cada subagente recebe:**
- Contexto do que estamos investigando
- Perguntas específicas pra responder
- Instrução de retornar síntese concisa (não dump de dados)

**Para discovery interno leve** (1-2 arquivos, grep simples): faça inline, sem subagente. Não gaste overhead de subagente pra tarefas triviais.

## 4. Sintetizar

Consolide os resultados dos subagentes em um resumo estruturado:
- O que foi descoberto (fatos, padrões, decisões existentes)
- Gaps que persistem (o que não foi possível descobrir)
- Implicações pra tarefa em questão (se há uma)

Apresente ao usuário de forma concisa.

## 5. Próximos passos

Após apresentar os resultados, sugira o caminho natural:
- Se a discovery informa uma tarefa → sugira `/plan <tarefa>` pra planejar a execução
- Se a discovery é pesquisa pura → pergunte se quer salvar em disco

## 6. Persistir (se relevante)

Use AskUserQuestion:

> **Quer salvar essa pesquisa em disco pra sessões futuras?**

Se sim:
- Salve em `.claude/discoveries/<slug>.md` com data e resumo estruturado
- Se o projeto não tem esse diretório, crie
- Se o projeto tem `.claude/state/STATE.md`, mencione a discovery como referência (não como workstream — discoveries não são workstreams)

Se não:
- O conhecimento fica no contexto da sessão (suficiente pra uso imediato)
