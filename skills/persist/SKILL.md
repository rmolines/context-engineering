---
name: persist
description: "Persistir estado da sessão atual pro disco. Usar ao finalizar uma tarefa, antes de /clear, ou ao encerrar sessão. Salva progresso, decisões e contexto para que sessões futuras continuem de onde parou. Auto-invocar quando o usuário disser: 'vou encerrar', 'sessão nova', 'contexto limpo', 'vou fechar', 'até a próxima', 'vamos terminar', 'terminar a sessão', 'terminar o trabalho', 'parar por aqui', 'vou parar'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: ""
---

# /persist — Salvar estado da sessão

## Step 1 — Triage (inline, rápido)

Reflita sobre a sessão e rode `git diff --stat` + `git log --oneline -10` pra complementar.

Classifique o que precisa persistir:

| Tipo | Condição | Ação |
|------|----------|------|
| **Workstream** | Houve progresso em trabalho com continuidade | Atualizar/criar .md em `.claude/state/` + STATE.md |
| **Memory** | Aprendizado novo sobre usuário, projeto ou feedback não-óbvio | Salvar/atualizar em `~/.claude/projects/.../memory/` |
| **Direction** | Decisão de direção de produto (tese, princípios, arquitetura macro) | Sugerir ao usuário (não editar automaticamente) |
| **Domain drift** | Código de APIs, auth, schema ou actions mudou mas `.claude/docs/` não foi atualizado | Alertar e sugerir atualização do domain map |
| **Campaign signal** | Sessão avançou uma campaign ou revelou algo inesperado | Atualizar signals em `.claude/state/campaigns.md` |

**Skip agressivo:** se a sessão foi pontual (bugfix, pergunta respondida, exploração sem decisão), diga "nada a persistir" e pare. Não forçar burocracia em sessão que não precisa.

## Step 2 — Executar em paralelo

Pra cada tipo marcado como relevante no triage, executar simultaneamente:

### Workstream (subagente haiku se necessário, inline se simples)

Leia `.claude/state/STATE.md` pra ver workstreams existentes.

- Workstream existente → **atualize** as seções que mudaram (não reescrever tudo)
- Trabalho novo com continuidade → crie `.claude/state/<nome>.md`:

```markdown
# {Nome}
> Last updated: {YYYY-MM-DD}

## Objetivo
## Estado atual
## Decisões tomadas
## Contexto para próxima sessão
```

Seções opcionais (só se relevante): `Tentativas que falharam`, `Pendências e blockers`.

Atualize STATE.md: mover entre Active/Completed, adicionar ao Backlog se surgiram ideias.

### Memory (subagente haiku)

Só se tem aprendizado novo que muda como sessões futuras operam:
- Preferências do usuário → `type: user` ou `type: feedback`
- Decisão de projeto não-óbvia → `type: project`
- Referência externa útil → `type: reference`

**Atualizar** memória existente em vez de duplicar. Verificar MEMORY.md antes.

Não salvar: estado de código, paths, soluções de debug, nada derivável do git.

### Domain drift detection (inline, rápido)

Se `.claude/docs/index.md` existe:
1. Rode `git diff --stat` e verifique se houve mudanças em:
   - `src/app/api/` ou `app/api/` ou `pages/api/` (rotas API)
   - Arquivos com `'use server'` (server actions)
   - Arquivos de auth (`auth.ts`, `session.ts`, `api-auth.ts`, `proxy.ts`)
   - Arquivos de DB/schema (`db-*.ts`, `schema.prisma`, `migrations/`)
   - `.env*` (environment variables)
2. Se houve mudanças nesses paths E `.claude/docs/index.md` não foi modificado na mesma sessão:
   - Alerte o usuário:
     > **Domain map pode estar desatualizado.** Houve mudanças em [APIs/auth/schema/actions]. Quer atualizar `.claude/docs/index.md`?
   - Se sim: releia os arquivos modificados e atualize os pointers relevantes no domain map
   - Se não: registre no prompt de continuação que o domain map pode precisar de atualização

Se `.claude/docs/index.md` não existe: não faça nada (o projeto pode não usar o sistema).

### Campaign feedback (inline, rápido)

Se `.claude/state/campaigns.md` existe E tem campaigns ativas:

1. Identificar qual campaign a sessão avançou — inferir do trabalho feito: commits, arquivos editados, contexto da conversa.
2. Se a sessão mapeia a uma campaign → adicionar signal datado na seção da campaign:
   ```
   - [YYYY-MM-DD] {observação concreta do que a sessão revelou}
   ```
   Signals são observações emergentes, não resumo de trabalho. Exemplos:
   - "setup local é o maior gargalo, não os docs" (insight)
   - "pattern X não escala pra N>100" (descoberta)
   - "usuário priorizou Y sobre Z apesar do plano dizer o contrário" (divergência)
3. Se a sessão NÃO mapeia a nenhuma campaign → registrar no final do arquivo:
   ```
   - [YYYY-MM-DD] ⚡ Sessão fora de campaign: {descrição do trabalho}. Possível estratégia emergente.
   ```
4. Verificar acúmulo de divergência: se 3+ sessões consecutivas não mapeiam a nenhuma campaign:
   > "As últimas sessões não avançaram nenhuma campaign ativa. Isso pode indicar que as campaigns precisam ser revisadas ou que surgiu uma nova direção. Quer revisar o Commander's Intent?"

Se `.claude/state/campaigns.md` não existe: não fazer nada (o projeto pode não usar o nível operacional).

### Direction (inline, só sugerir)

Se uma decisão de direção foi tomada:
> "A direção do projeto pode ter mudado. Quer atualizar `## Direction` no CLAUDE.md?"

Só editar com confirmação explícita.

## Step 3 — Prompt de continuação + resumo

Gere um bloco copiável pra próxima sessão:

```
## Continuação de sessão

### Contexto
<!-- O que, qual workstream, decisões-chave — 2-3 frases -->

### Próximos passos
<!-- Ações concretas na ordem -->

### Arquivos-chave
<!-- Paths relevantes -->

### Campaign
<!-- Qual campaign esta sessão avançou, se alguma -->
```

Mostre ao usuário o que foi salvo (1-2 linhas) + o prompt acima.
