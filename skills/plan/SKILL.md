---
name: plan
description: "Cria e gerencia planos estruturados com controle de granularidade. Sub-comandos: '/plan <tarefa>' cria plano novo, '/plan' retoma plano existente, '/plan decompose N' decompõe deliverable. Execução separada via /run. Usar quando quiser planejar antes de executar, controlar granularidade, ou retomar trabalho planejado."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch
argument-hint: "[tarefa | decompose N]"
---

> ⚠️ **DEPRECATED:** This skill has been absorbed by `/delivery` (step 3: decompose).
> The plan concept still exists as agent-internal infrastructure, but is no longer user-facing.
> Use `/discovery` to create spec'd Issues, then `/delivery #N` to execute.
> See `ARCHITECTURE.md` for the new model.

# /plan — Planejamento estruturado

**Input:** `$ARGUMENTS`

Parse o input:

| Input | Modo |
|---|---|
| vazio | RESUME — retomar plano(s) existente(s) |
| `decompose N` | DECOMPOSE — decompor deliverable N |
| qualquer outro texto | CREATE — criar plano novo |

---

## Modo CREATE

### 1. Assess

Use AskUserQuestion:

> **Qual o nível de profundidade pra esse plano?**
>
> 1. **Leve** — poucos steps, sem deps, execução linear
> 2. **Médio** — deliverables com deps, batches se tiver paralelismo
> 3. **Profundo** — deliverables detalhados, deps, batches, critério de sucesso, fora de escopo

### 2. Explore

Antes de planejar, entenda o contexto:
- Leia arquivos relevantes à tarefa
- Verifique git log recente na área
- Se `.claude/state/campaigns.md` existe: leia pra entender o contexto operacional. Identifique qual campaign este trabalho serve (se alguma).
- Se há gap de conhecimento: pesquise via subagente (model: sonnet) pra não poluir contexto

### 3. Escrever plano

Crie o arquivo em `.claude/state/plan-<slug>.md`. O formato se adapta ao nível:

#### Leve

```markdown
# Plan: <título>

> Status: active
> Created: <YYYY-MM-DD>
> Last updated: <YYYY-MM-DD>

## Objetivo
<O que e por quê>

## Deliverables
- [ ] 1. <deliverable — arquivo(s) envolvido(s)>
- [ ] 2. <deliverable>
- [ ] 3. <deliverable>

## Execution Log
```

#### Médio

```markdown
# Plan: <título>

> Status: active
> Created: <YYYY-MM-DD>
> Last updated: <YYYY-MM-DD>
> Campaign: {CN — nome | nenhuma (tática pontual)}

## Objetivo
<O que e por quê>

## Deliverables

### D1 — <nome>
**O que:** <descrição concisa>
**Issue:** <#N — preenchido pelo step 3.5 se GITHUB_MODE>
**Deps:** nenhuma
**Tamanho:** pequeno | medio | grande

### D2 — <nome>
**O que:** <descrição>
**Issue:** <#N — preenchido pelo step 3.5 se GITHUB_MODE>
**Deps:** D1
**Tamanho:** medio

## Git Strategy
**Modo:** pr-per-batch | pr-per-deliverable | single-pr | direct-commit
**Branches:**
- `agent/<slug-1>` → D1 + D3 (Batch 1) → PR #1
- `agent/<slug-2>` → D2 (Batch 2) → PR #2

## Ordem de execução
**Batch 1:** D1 + D3 (sem deps entre si — paralelo)
**Batch 2:** D2 (depende de D1, D3)

## Context
<Decisões, libs, restrições>

## Execution Log
```

#### Profundo

```markdown
# Plan: <título>

> Status: active
> Created: <YYYY-MM-DD>
> Last updated: <YYYY-MM-DD>
> Campaign: {CN — nome | nenhuma (tática pontual)}

## Objetivo
<O que e por quê>

## Deliverables

### D1 — <nome>
**O que:** <descrição detalhada>
**Issue:** <#N — preenchido pelo step 3.5 se GITHUB_MODE>
**Implementação:** <como, onde, detalhes técnicos>
**Deps:** nenhuma
**Tamanho:** pequeno

### D2 — <nome>
**O que:** <descrição detalhada>
**Issue:** <#N — preenchido pelo step 3.5 se GITHUB_MODE>
**Implementação:** <como, onde>
**Deps:** D1, D3
**Tamanho:** medio

## Git Strategy
**Modo:** pr-per-batch | pr-per-deliverable | single-pr | direct-commit
**Base branch:** main
**Branches:**
- `agent/<slug-1>` → D1 + D3 + D4 (Batch 1) → PR #1
- `agent/<slug-2>` → D2 (Batch 2) → PR #2 (rebase sobre main após PR #1 mergear)
- `agent/<slug-3>` → D5 + D6 (Batch 3) → PR #3
**Domínios de arquivo:** (pra coordenação entre agentes paralelos)
- D1: `src/api/`
- D3: `src/ui/`
- D4: `src/config/`

## Ordem de execução
**Batch 1:** D1 + D3 + D4 (paralelo)
**Batch 2:** D2 (depende de batch 1)
**Batch 3:** D5 + D6 (paralelo, dependem de D2)

## Critério de sucesso
<Como validar que o plano foi completado com sucesso>

## Fora de escopo
<O que deliberadamente não vamos fazer e por quê>

## Context
<Decisões, libs, restrições>

## Execution Log
```

**Regras de escrita:**
- Cada deliverable/step deve ser verificável independentemente
- Incluir arquivo(s) envolvido(s) quando possível
- Não decompor demais upfront — o usuário decide onde aprofundar
- Se identificar paralelismo, explicite nos batches
- O grafo de deps deve ser consistente (sem deps circulares)

**Regras de Git Strategy (médio e profundo):**
- Escolher modo baseado na natureza do plano:
  - `direct-commit`: plano leve, ou trabalho no branch atual sem PR
  - `single-pr`: tudo num PR (refactors pequenos, configs)
  - `pr-per-batch`: default — cada batch vira um PR sequencial
  - `pr-per-deliverable`: quando deliverables são independentes e devem mergear separado
- Branch naming: `agent/<slug-do-plano>` ou `agent/<slug-do-plano>-<batch>`
- Se batches são sequenciais: cada PR rebasa sobre main após o anterior mergear
- Mapear domínios de arquivo quando há agentes paralelos no mesmo batch (evita conflitos)
- **Worktrees:** deliverables paralelos num batch usam `isolation: "worktree"` no /run — cada subagente trabalha em cópia isolada do repo. O /plan não precisa configurar worktrees, apenas garantir que domínios de arquivo estejam claros pra minimizar conflitos no merge.
- Se o projeto não tem CI configurado: sugerir `/bootstrap` antes de executar com PRs

### 3.5. GitHub Issues (se GITHUB_MODE=true)

Referência: `skills/shared/github-detection.md` — rodar a detecção.

Se `GITHUB_MODE=false`: pular este step inteiro.

#### Identificar milestone

Ler o campo `Campaign:` do header do plano.
- Se tem campaign (ex: `C1 — Dogfooding`): encontrar o milestone correspondente:
  ```bash
  gh api repos/{owner}/{repo}/milestones --jq '.[] | select(.title | startswith("[C1]")) | .title'
  ```
- Se "nenhuma (tática pontual)": usar milestone `[Backlog]`

#### Criar issues (uma por deliverable, em ordem)

Para cada deliverable DN:

1. **Check de duplicata** — buscar issue existente com mesmos labels:
   ```bash
   gh issue list --label "plan:<slug>" --json number,title --jq '.[] | select(.title | startswith("DN"))'
   ```
   Se já existe: pular criação, usar número existente.

2. **Criar issue:**
   ```bash
   gh issue create \
     --title "DN — <nome do deliverable>" \
     --body "$(cat <<'EOF'
   ## O que
   <descrição do deliverable — copiar do campo "O que:" do plano>

   ## Acceptance criteria
   - [ ] <critério derivado da descrição>

   ## Plan
   plan-<slug>.md · Batch N · Deps: <deps ou "nenhuma">
   EOF
   )" \
     --milestone "<[CN] milestone title>" \
     --label "type:deliverable,batch:<N>,size:<size>,plan:<slug>,status:ready"
   ```

3. **Registrar no plano** — adicionar `**Issue:** #N` ao deliverable no plan file:
   ```markdown
   ### D1 — nome
   **O que:** descrição
   **Issue:** #23
   **Deps:** nenhuma
   **Tamanho:** medio
   ```

#### Labels dinâmicos

Se o label `plan:<slug>` ou `campaign:<slug>` não existe: criar antes das issues:
```bash
gh label create "plan:<slug>" --color "BFD4F2" --description "Plan: <slug>" || true
gh label create "campaign:<slug>" --color "D4C5F9" --description "Campaign: <slug>" || true
```

#### Adicionar ao Projects V2 (se PROJECTS_MODE=true)

Se `.claude/state/project-cache.json` existe:

Para cada issue criada:
```bash
# Ler cache
PROJECT_NUMBER=$(jq -r '.projectNumber' .claude/state/project-cache.json)
PROJECT_ID=$(jq -r '.projectId' .claude/state/project-cache.json)
OWNER=$(jq -r '.owner' .claude/state/project-cache.json)

# Adicionar ao board
ITEM_ID=$(gh project item-add $PROJECT_NUMBER --owner $OWNER --url {issue_url} --format json | jq -r '.id')

# Setar Campaign
CAMPAIGN_FIELD=$(jq -r '.fields.Campaign.id' .claude/state/project-cache.json)
CAMPAIGN_OPT=$(jq -r '.fields.Campaign.options["[CN]"]' .claude/state/project-cache.json)
gh project item-edit --id $ITEM_ID --project-id $PROJECT_ID --field-id $CAMPAIGN_FIELD --single-select-option-id $CAMPAIGN_OPT

# Setar Size
SIZE_FIELD=$(jq -r '.fields.Size.id' .claude/state/project-cache.json)
SIZE_OPT=$(jq -r ".fields.Size.options[\"$SIZE\"]" .claude/state/project-cache.json)
gh project item-edit --id $ITEM_ID --project-id $PROJECT_ID --field-id $SIZE_FIELD --single-select-option-id $SIZE_OPT
```

Se cache não existe: pular (issues ficam no board sem campos custom até o próximo /bootstrap).

#### Atualizar header do plano

Adicionar ao header do plan file:
```markdown
> GitHub: issues created, milestone=[CN] nome
```

### 4. Atualizar STATE.md

Adicione ou atualize a referência ao plano no STATE.md.

### 5. Checkpoint

Se `.claude/state/campaigns.md` existe mas o plano não referencia nenhuma campaign: use AskUserQuestion:

> **Este trabalho serve alguma campaign ativa? Se sim, qual? Se não, está ok — nem tudo precisa ser campaign.**

- Se o usuário indicar uma campaign → preencher o campo Campaign no header do plano com o nome/ID informado.
- Se o usuário disser que não → manter "nenhuma (tática pontual)" no campo Campaign.

Apresente o plano e use AskUserQuestion:

> **Plano criado. Como quer prosseguir?**
>
> - `decompõe N` — detalha o deliverable/step N
> - `muda N: <descrição>` — reescreve
> - `remove N` — remove
> - `adiciona: <deliverable>` — adiciona
> - `ok` — salva (execute depois com `/run`)

Se o usuário pedir mudança → aplique e volte ao checkpoint.
Se o usuário aprovar → salve e informe que pode executar com `/run`.

---

## Modo RESUME

### 1. Encontrar planos

Leia `.claude/state/` e liste todos os `plan-*.md` com status != completed.

### 2. Apresentar

Se um plano ativo → mostre status (deliverables concluídos/pendentes, próximo batch).
Se múltiplos → liste e pergunte qual retomar.
Se nenhum → informe e sugira criar com `/plan <tarefa>`.

### 3. Checkpoint

Mesmo checkpoint do CREATE — apresente o estado e pergunte como ajustar.

---

## Modo DECOMPOSE

### 1. Identificar plano e deliverable

Se há um plano ativo → use esse.
Se múltiplos → pergunte qual.
Leia o plano e encontre o deliverable/step N.

### 2. Decompor

Explore o codebase se necessário. Decomponha em sub-items:

```markdown
### D3 — Implementar /refresh endpoint
**O que:** handler completo com validação e rotação de tokens
**Deps:** D1
**Tamanho:** medio

Sub-deliverables:
- [ ] D3.1 — Criar handler em src/auth/refresh.ts
- [ ] D3.2 — Validação de refresh token
- [ ] D3.3 — Rotação de tokens
```

### 3. Atualizar artefato e checkpoint

Reescreva no arquivo do plano. Volte ao checkpoint.

---

## Regras gerais

- O plano é a fonte de verdade. Sempre leia do disco antes de agir — outra sessão pode ter atualizado.
- O checkpoint é obrigatório. Nunca pule direto de criar pra aprovar sem apresentar.
- Planejamento e execução são separados: `/plan` planeja, `/run` executa.
- Renumere automaticamente após decomposição ou remoção.
