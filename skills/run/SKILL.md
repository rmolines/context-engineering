---
name: run
description: "Executa planos criados pelo /plan. Roda deliverables/steps respeitando deps e batches, paraleliza via subagentes quando possível. Sub-comandos: '/run' próximo batch, '/run D3' deliverable específico, '/run --all' tudo que tiver pronto."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch, TaskCreate, TaskUpdate, TaskList
argument-hint: "[DN | --all]"
---

# /run — Execução de planos

**Input:** `$ARGUMENTS`

Parse:

| Input | Modo |
|---|---|
| vazio | NEXT_BATCH — executa próximo batch pendente |
| `DN` ou `N` | SPECIFIC — executa deliverable/step específico |
| `--all` | ALL — executa todos os batches em sequência |

---

## 1. Carregar plano

Leia `.claude/state/plan-*.md` com status `active`.

- Se um plano → use esse
- Se múltiplos → pergunte qual
- Se nenhum → informe e sugira `/plan <tarefa>`

Sempre releia do disco — outra sessão pode ter atualizado.

## 2. Ler Git Strategy do plano

Verifique se o plano tem seção `## Git Strategy`. Se sim:
- Leia o modo (`direct-commit`, `single-pr`, `pr-per-batch`, `pr-per-deliverable`)
- Leia os branches e agrupamento de deliverables por PR
- Verifique se o projeto tem CI configurado (`.github/workflows/` existe). Se não e o modo não é `direct-commit`: avise e sugira `/bootstrap init`

Se não tem seção Git Strategy: modo `direct-commit` (commit no branch atual, sem PR).

## 3. Determinar escopo

### NEXT_BATCH
Identifique o próximo batch: deliverables/steps cujas deps já estão concluídas.

### SPECIFIC
Verifique se as deps do deliverable estão concluídas. Se não:
- Informe quais deps faltam
- Pergunte se quer executar as deps primeiro

### ALL
Execute batch a batch em sequência, com checkpoint entre batches.

## 4. Executar

Para cada batch:

### 4a. Git — antes do batch

Se modo git != `direct-commit`:
1. Verifique se o branch do batch já existe (pode ser retomada). Se sim: checkout
2. Se não: crie branch a partir do base branch definido no plano
   ```bash
   git checkout -b agent/<slug> <base-branch>
   ```
3. Se PRs anteriores do mesmo plano já mergearam: rebase sobre main atualizado primeiro
   ```bash
   git fetch origin && git rebase origin/main
   ```

### 4b. Deliverables independentes no batch → paralelizar com worktrees

Se o batch tem 2+ deliverables sem deps entre si, delegue a subagentes em paralelo **usando `isolation: "worktree"`**. Cada subagente trabalha numa cópia isolada do repo — sem risco de colisão de arquivos.

Escolha o modelo por deliverable:
- `model: sonnet` — implementação, refatoração, lógica
- `model: haiku` — grep, listagem, formatação, validação de syntax, extração de dados

Cada subagente recebe um **prompt auto-contido** com:
- **O quê:** descrição completa do deliverable (do plano)
- **Onde:** arquivos a ler e editar (paths exatos)
- **Como validar:** comando ou check que confirma sucesso
- **O que NÃO fazer:** limites de escopo, arquivos que não deve tocar
- **Contexto mínimo:** snippets de código relevantes, decisões do plano
- **Git:** fazer commits atômicos no worktree (conventional commit + Co-Authored-By). Não fazer push — o orquestrador cuida disso.

**Worktree lifecycle (o /run orquestra):**

1. **Pré-checks:**
   - `.worktreeinclude` existe? Se o projeto usa `.env*` e não tem, criar com os padrões necessários (`.env`, `.env.local`).
   - `.claude/worktrees/` está no `.gitignore`? Se não, adicionar.
   - Setup é pesado (monorepo, install > 60s)? Se sim e batch tem apenas 2 deliverables, considerar executar inline (4c) — o overhead de 2x install pode anular o ganho do paralelismo.

2. **Spawnar** subagentes em **foreground** com `isolation: "worktree"` (nunca background — subagentes background não podem reportar erros). Todos na mesma mensagem = execução paralela.

3. **Prompt de cada subagente** deve incluir:
   - Tudo do template acima (o quê, onde, como validar, escopo, contexto)
   - **Setup:** `npm install` (ou equivalente) antes de trabalhar, se o projeto usa dependências
   - **Git:** commitar com conventional commit + Co-Authored-By. Não fazer push.
   - **Output obrigatório:** ao finalizar, incluir no texto de resposta: `BRANCH: <nome-do-branch>` e `STATUS: ok|failed` + resumo do que foi feito. Isso é necessário porque o orquestrador precisa saber qual branch mergear.
   - **DB:** se o deliverable roda testes que dependem de banco de dados, avisar que o DB é compartilhado (worktrees não isolam banco). Testes de integração devem usar transações ou fixtures isoladas.

4. **Aguardar** todos completarem. Parsear o output de cada um pra extrair branch e status.

5. **Merge sequencial** (ordem importa se houver arquivos compartilhados):
   - Checkout do batch branch (ou main se `direct-commit`)
   - Pra cada worktree com mudanças, na ordem dos deliverables (D1 antes de D3):
     ```bash
     git merge <worktree-branch> --no-ff -m "merge: DN — <desc>"
     ```
   - Se conflito no merge: **parar e reportar** ao usuário. Não tentar resolver automaticamente — conflitos pós-worktree geralmente indicam overlap que deveria ter sido pego no /plan.

6. **Validação pós-merge:** após mergear todos os worktrees, rodar validação integrada:
   - Se o projeto tem testes: `npm test` (ou equivalente)
   - Se tem type-check: `npx tsc --noEmit`
   - Se tem lint: `npm run lint`
   - Se falhar: diagnosticar, corrigir inline, commitar o fix.

7. **Atualizar plano:** marcar cada deliverable como concluído e adicionar ao Execution Log:
   ```
   - D1: concluído (YYYY-MM-DD) — <resumo> [worktree]
   - D3: concluído (YYYY-MM-DD) — <resumo> [worktree]
   ```

8. **Cleanup:** worktrees sem mudanças são removidos automaticamente. Após merge bem-sucedido:
   ```bash
   git worktree remove <path> && git branch -d <branch>
   ```

**Quando NÃO paralelizar (executar inline via 4c):**
- Deliverables no batch editam os mesmos arquivos (overlap)
- Batch tem apenas 1 deliverable
- Setup do projeto é muito pesado e batch tem poucos deliverables

**Limitação conhecida:** worktrees partem de `origin/HEAD`, não do batch branch. Pra deliverables independentes (sem deps entre si no batch), isso é OK. Se um retry precisa do estado acumulado no batch branch, executar inline.

Nota: subagentes não podem spawnar outros subagentes — dimensione a granularidade do prompt pra que cada um resolva inline.

### 4c. Deliverable único ou com deps internas → executar inline

Execute sequencialmente. Para cada deliverable/step:

1. Informe o que vai executar
2. Execute
3. Valide (rode testes se aplicável, leia output, verifique comportamento)
4. Commit atômico — stage explícito por arquivo, conventional commit com Co-Authored-By:
   ```bash
   git add path/to/file1 path/to/file2
   git commit -m "$(cat <<'EOF'
   feat: <descrição concisa do que e por quê>

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```
   - **SEMPRE** listar arquivos explicitamente no `git add` (nunca `git add .` ou `git add -A`)
   - **SEMPRE** incluir `Co-Authored-By` no footer do commit
   - Prefixo: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:` conforme a natureza da mudança
5. Marque como concluído no arquivo do plano
6. Adicione entrada no Execution Log:
   ```
   - D1: concluído (YYYY-MM-DD) — <resumo de 1 linha>
   ```

### Sub-deliverables (D3.1, D3.2...)

Se um deliverable foi decomposto em sub-items:
- Execute sub-items em sequência
- Sub-items independentes podem ir em paralelo via subagentes com `isolation: "worktree"` (mesmo padrão do 4b)
- Marque o deliverable pai como concluído quando todos os sub-items estiverem done

### Se falha

- Pare a execução do batch
- Diagnostique a causa
- Registre o erro no Execution Log:
  ```
  - D3: FALHOU (YYYY-MM-DD) — <erro encontrado>
  ```
- Informe o usuário e pergunte como proceder

### 4d. Git — após o batch

Se modo git != `direct-commit` e este batch fecha um PR (conforme Git Strategy):

1. Push do branch:
   ```bash
   git push -u origin agent/<slug>
   ```
2. Abrir PR com `gh` (usar HEREDOC pro body):
   ```bash
   gh pr create --title "feat: <título do batch/deliverable>" --body "$(cat <<'EOF'
   ## Summary
   - <bullet points do que foi feito>

   ## Test plan
   - [ ] <checklist de validação>

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )" --label "ai-generated"
   ```
3. Registrar PR no Execution Log:
   ```
   - PR: #123 (agent/<slug>) — D1 + D3
   ```
4. Se modo `--all` ou `pr-per-batch` com batches seguintes:
   - Esperar CI passar: `gh pr checks <pr-number> --watch`
   - Se CI falha: diagnosticar, corrigir, push, esperar novamente (máx 2 tentativas, depois parar)
   - Após merge (auto-merge via CI): `git checkout main && git pull origin main`
   - Seguir pro próximo batch com main atualizado

Se modo `direct-commit`: nenhuma ação git adicional.

## 5. Checkpoint pós-batch

Após cada batch, apresente:
- O que foi concluído
- O que resta (próximo batch, deliverables pendentes)
- PRs abertos e status do CI (se aplicável)
- Use AskUserQuestion:

> **Batch N concluído. Como prosseguir?**
>
> - `próximo` — executa o próximo batch
> - `para` — pausa aqui
> - `decompõe DN` — detalha um deliverable antes de continuar (invoque /plan decompose N)

### Modo ALL
No modo `--all`, entre batches: mostre progresso e prossiga automaticamente, sem checkpoint. Pare apenas se houver falha ou CI falhar 2x.

## 6. Plano concluído

Quando todos os deliverables estão done:
- Marque status como `completed` no arquivo do plano
- Atualize STATE.md explicitamente: mova o plano de Active pra Completed (ou atualize a descrição de status)
- Resuma o que foi feito
- Mostre como validar (critério de sucesso do plano, se existir)
- Sugira `/persist` pra salvar o estado completo da sessão
