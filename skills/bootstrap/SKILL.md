---
name: bootstrap
description: "Carregar estado do projeto, inicializar o que falta, alinhar sessão. Idempotente — sempre seguro de rodar. Detecta automaticamente se precisa inicializar ou recarregar. Usar: '/bootstrap' em qualquer projeto, a qualquer momento. '/bootstrap migrate-to-github' migra estado local para GitHub Issues/Milestones."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: "[migrate-to-github]"
---

# /bootstrap — Gestão de estado do projeto

**Input:** `$ARGUMENTS`

| Input | Modo |
|---|---|
| vazio | DEFAULT — detectar, inicializar, carregar, alinhar |
| `migrate-to-github` | MIGRATE — migrar estado local para GitHub Issues/Milestones |

---

## Modo MIGRATE (migrate-to-github)

Migra campaigns e deliverables de planos locais para GitHub Issues/Milestones.

Referência: `skills/shared/github-detection.md` — rodar detecção. Se `GITHUB_MODE=false`: abortar com mensagem clara.

### Step 1 — Auditar estado local

1. Ler `.claude/state/campaigns.md` → listar campaigns ativas E completadas
2. Ler todos os `plan-*.md` em `.claude/state/`:
   - Status `active` → listar deliverables sem campo `Issue: #N`
   - Status `completed` → contar (histórico a migrar como milestones fechados)
3. Ler seção `## Strategic Review Log` do campaigns.md (se existir)
4. Apresentar resumo ao usuário:
   ```
   Migração para GitHub:

   Estado ativo:
   - N campaigns ativas → milestones abertos
   - N deliverables sem issue → issues a criar

   Histórico:
   - N campaigns completadas → milestones fechados
   - N planos completados (ficam locais — sem issues retroativas)
   - Strategic Review Log → comment no milestone mais recente
   ```
5. Pedir confirmação antes de criar qualquer coisa

### Step 2 — Criar milestones das campaigns (idempotente)

#### Campaigns ativas
Para cada campaign ativa:
1. Verificar se milestone `[CN] nome` já existe
2. Se não: criar via `gh api repos/{owner}/{repo}/milestones --method POST`
   - Description: Intent + Success state + signals existentes
3. Criar `[Backlog]` se não existe

#### Campaigns completadas (histórico)
Para cada campaign na seção `## Completed Campaigns`:
1. Verificar se milestone já existe (pode ter sido criada antes de completar)
2. Se não existe: criar milestone com `--field state=closed`:
   ```bash
   gh api repos/{owner}/{repo}/milestones \
     --method POST \
     --field title="[CN] nome da campaign" \
     --field description="Intent: ...\nSuccess state: ...\n\n## Signals\n<signals acumulados>\n\n## Resultado\nCompletada em YYYY-MM-DD" \
     --field state=closed
   ```
3. Se já existe mas está aberta: fechar:
   ```bash
   gh api repos/{owner}/{repo}/milestones/{number} \
     --method PATCH \
     --field state=closed
   ```

#### Strategic Review Log
Se campaigns.md tem seção `## Strategic Review Log` com conteúdo:
1. Encontrar o milestone ativo mais recente (ou o último fechado, se todos fechados)
2. Adicionar como comment via `gh api`:
   ```bash
   gh api repos/{owner}/{repo}/issues/{milestone-tracking-issue}/comments \
     --method POST \
     --field body="## Strategic Review Log (migrado)\n\n<conteúdo do log>"
   ```
   Alternativa se não houver tracking issue: incluir no description do milestone mais recente (respeitando limite de 1024 chars).

### Step 3 — Criar issues dos deliverables

Para cada plan file **ativo** com deliverables sem `Issue: #N`:
1. Identificar milestone da campaign do plano
2. Para cada deliverable sem issue:
   - Criar label `plan:<slug>` se não existe
   - Criar issue com `gh issue create` (mesmo formato do /plan step 3.5)
   - Atualizar plan file: adicionar `**Issue:** #N` ao deliverable

**Planos completados:** não criar issues retroativas. O histórico de execução está nos commits, plan files locais e PRs. Criar issues pra trabalho já feito seria ruído sem valor operacional.

### Step 4 — Rebuild STATE.md

Rodar o mesmo rebuild do step 2.5 do modo DEFAULT (cache do GitHub).

### Step 5 — Report

```
Migração concluída:

Estado ativo:
- N milestones abertos criados
- N issues criados
- N plan files atualizados

Histórico:
- N milestones fechados criados (campaigns completadas)
- Strategic Review Log migrado para [milestone/comment]

STATE.md regenerado do GitHub
```

---

## Modo DEFAULT

Comando idempotente. Detecta o que existe e o que falta, inicializa o necessário, recarrega o estado.

## 1. Detectar estado

Verifique o que já existe no projeto:

```
STATE.md         = .claude/state/STATE.md existe?
DOMAIN_MAP       = .claude/docs/index.md existe?
CI               = .github/workflows/ci.yml existe?
HAS_PACKAGE_JSON = package.json existe?
HAS_REMOTE       = git remote get-url origin (sucesso?)
```

## 2. Garantir estrutura (idempotente)

### STATE.md
- **Se existe:** leia e siga pro step 3
- **Se não existe:** crie `.claude/state/STATE.md`:

```markdown
# Project State

## Backlog

## Active

## Completed
```

### Discovery inicial (só se STATE.md foi criado agora)
- Leia `README.md`, `CLAUDE.md`, `package.json`, `Cargo.toml`, `pyproject.toml` ou equivalente
- Execute `git log --oneline -20` pra entender atividade recente
- Execute `git branch -a` pra ver branches ativas
- Liste diretórios de primeiro nível pra entender a estrutura

### Domain map
- **Se existe:** pule (drift detection fica no /persist)
- **Se não existe:** gere `.claude/docs/index.md` com scan do projeto:

**API Surface:**
- Procure rotas em `src/app/api/`, `app/api/`, `pages/api/`, `routes/`, ou equivalente do framework
- Para cada rota: liste o path, métodos HTTP (do export: GET, POST, PUT, DELETE), e auth (procure por middleware, Bearer, session, cookie no arquivo)
- Formato: `- [nome semântico](path/relativo) — método(s), tipo de auth`

**Server Actions:**
- Procure arquivos com `'use server'` em `src/app/actions/`, `app/actions/`, ou equivalente
- Liste cada action exportada com path e propósito (inferido do nome da função)

**Auth:**
- Procure por arquivos de auth: `auth.ts`, `session.ts`, `middleware.ts`, `proxy.ts`, `api-auth.ts`
- Identifique o(s) mecanismo(s): JWT, session cookie, API key, OAuth, etc.
- Aponte pro(s) arquivo(s) de implementação

**Data Model:**
- Procure por: `prisma/schema.prisma`, `drizzle/`, `src/lib/db-*.ts`, `models/`, `schema.ts`, `migrations/`
- Se ORM: aponte pro schema file
- Se raw SQL: aponte pros arquivos de query
- Se tem seed/migration: aponte

**Canonical Patterns:**
- Identifique o melhor exemplo de cada tipo que o projeto tem:
  - Se tem API routes: escolha a mais completa (com auth + validation + error handling)
  - Se tem pages/components: escolha a mais representativa
  - Se tem server actions: escolha a mais completa
- Liste como referência canônica

**Environment Variables:**
- Leia `.env.example`, `.env.template`, `.env.development.local` (se existir)
- Ou extraia do código: procure por `process.env.` nos arquivos principais
- Liste cada var com propósito (não valor)

Se um projeto não tem alguma dessas seções (ex: CLI tool sem API), omita a seção.

Use subagentes pra paralelizar o scan se o projeto for grande.

Após gerar, apresente o domain map ao usuário pra review antes de salvar.

### Campaigns
- **Se existe** (`.claude/state/campaigns.md`): pule (já inicializado)
- **Se não existe:** crie `.claude/state/campaigns.md`:

```markdown
# Campaigns

Last reviewed: YYYY-MM-DD

## Active Campaigns

<!-- C1: [nome] — [objetivo em 1 linha] | Status: [on-track|at-risk|blocked] -->

## Completed Campaigns

<!-- [nome] — [data de conclusão] -->

## Strategic Review Log

<!-- [data] — [decisão ou ajuste de direção] -->
```

### CI (só se não existe + tem package.json + tem remote GitHub)
1. Detecte o stack:
   - Package manager: procure `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, ou default `npm`
   - Node version: leia `.node-version`, `.nvmrc`, `engines.node` em package.json, ou default `22`
   - Scripts disponíveis: leia `scripts` em `package.json` — procure `lint`, `type-check`/`typecheck`, `test`, `build`
2. Gere `.github/workflows/ci.yml` usando o template de CI do diretório `templates/ci/` deste plugin:
   - Substitua as variáveis `{{...}}` com os valores detectados
   - Remova steps cujo script não existe (ex: se não tem `lint`, remova o step Lint)
3. Verifique se a label `ai-generated` existe no repo GitHub:
   ```bash
   gh label list | grep ai-generated || gh label create ai-generated --color 1D76DB --description "PR criado por agente AI"
   ```
4. Informe o usuário do que foi configurado

## 2.5. GitHub sync

**Executar apenas se** o projeto tem remote GitHub E `gh auth status` retorna sucesso. Se qualquer check falhar: pule silenciosamente e siga com o fluxo local (steps 3+).

Referência: `skills/shared/github-detection.md` — rodar a detecção descrita lá.

### Labels (idempotente — criar apenas as que não existem)

Criar cada label com `|| true` pra ignorar erro se já existe:

```bash
gh label create "type:deliverable" --color "0052CC" --description "Plan deliverable" || true
gh label create "type:backlog" --color "FBCA04" --description "Backlog item sem plano ativo" || true
gh label create "status:ready" --color "0E8A16" --description "Deps satisfeitas, pode executar" || true
gh label create "status:in-progress" --color "D93F0B" --description "Em andamento" || true
gh label create "status:blocked" --color "B60205" --description "Bloqueado" || true
gh label create "size:small" --color "C2E0C6" --description "Pequeno" || true
gh label create "size:medium" --color "FEF2C0" --description "Médio" || true
gh label create "size:large" --color "F9D0C4" --description "Grande" || true
```

### Milestones das campaigns (idempotente)

Se `.claude/state/campaigns.md` existe e tem campaigns ativas:

1. Ler campaigns ativas — cada campaign com formato `### CN: nome`
2. Para cada campaign ativa, verificar se milestone já existe:
   ```bash
   gh api repos/{owner}/{repo}/milestones --jq '.[].title' | grep "^\[CN\]"
   ```
3. Se não existe: criar
   ```bash
   gh api repos/{owner}/{repo}/milestones \
     --method POST \
     --field title="[CN] nome da campaign" \
     --field description="Intent: ...\nSuccess state: ...\n\n## Signals" \
     --field state=open
   ```
4. Criar milestone `[Backlog]` se não existe

### STATE.md — rebuild do cache

Regenerar STATE.md a partir do GitHub:

1. Buscar issues abertas:
   ```bash
   gh issue list --state open --json number,title,milestone,labels --limit 200
   ```
2. Buscar issues fechadas recentes (30 dias):
   ```bash
   gh issue list --state closed --json number,title,milestone,labels,closedAt --limit 50
   ```
3. Gerar STATE.md com header indicando que é cache:

```markdown
# Project State
<!-- Generated from GitHub at YYYY-MM-DDTHH:MM:SSZ — do not edit manually -->
<!-- Regenerated by /bootstrap. Source of truth: GitHub Issues/Milestones. -->

## Active
- #N [CN] DN — título (batch:X, size:Y)

## Backlog
- #N título

## Completed (last 30 days)
- #N [CN] DN — título — closed YYYY-MM-DD via PR #M
```

Se não houver issues no GitHub: manter STATE.md local existente (não sobrescrever com arquivo vazio).

### campaigns.md — refresh de signals

Para cada milestone que mapeia a uma campaign:
1. Ler description do milestone via `gh api`
2. Se há signals no milestone que não estão no campaigns.md local: adicionar
3. Atualizar campo `Last reviewed:` com data de hoje

## 3. Carregar estado

Leia `.claude/state/STATE.md` e mostre overview:

> Se STATE.md tem header `<!-- Generated from GitHub -->`: indicar que está em GitHub mode e as issues são a fonte de verdade.

```
Project State:
- [workstream-a] — status curto
- [workstream-b] — status curto
Backlog: N items | Completed: N items

Planos ativos:
- plan-feature-x.md — 3/7 deliverables concluídos, próximo batch: D4+D5

Domain map: .claude/docs/index.md (N endpoints, N auth flows)
```

Para encontrar planos: liste `plan-*.md` em `.claude/state/` com status != completed.

## 3.5. Backbrief operacional

**Executar apenas se** `.claude/state/campaigns.md` existe E contém campaigns ativas (seção `## Active Campaigns` com pelo menos uma entrada não-comentada). Caso contrário, pule silenciosamente.

Se há campaigns ativas:

1. **Resumo de status** — leia campaigns.md e apresente 1 linha por campaign ativa:
   ```
   Campaigns ativas:
   - C1: [nome] — [status]
   - C2: [nome] — [status]
   ```

2. **Cruzamento com intenção da sessão** — após o usuário responder o que quer fazer no step 5 (Alinhar), cruze a resposta com as campaigns:
   - Se a intenção avança uma campaign → mencione: "Isso avança a campaign C1 — {nome}"
   - Se não há match com nenhuma campaign → pergunte: "Isso é uma campaign nova ou é tática pontual?"

3. **Verificação de cadência** — leia o campo `Last reviewed:` no topo do campaigns.md:
   - Se a data é >14 dias atrás **ou** não há registros de revisão no Strategic Review Log nos últimos 5+ bootstraps:
     > "As campaigns não são revisadas desde {data}. Quer fazer uma revisão estratégica rápida?"

4. **Detecção de divergência** — se há múltiplas sessões seguidas sem match com nenhuma campaign (signal de divergência entre trabalho real e direção declarada):
   > "Os signals recentes sugerem que a direção pode ter mudado. Quer revisar o Commander's Intent?"

## 4. Sugerir workstreams (só se STATE.md foi criado agora)

Com base no discovery, sugira workstreams iniciais ao usuário:
- Branches abertas podem indicar trabalho em andamento
- PRs abertos (se GitHub) podem ser workstreams
- Issues recentes podem ser backlog

Pergunte ao usuário quais quer registrar.
Para cada confirmada, crie o .md em `.claude/state/` e atualize STATE.md.

## 5. Alinhar

Pergunte ao usuário: "O que vamos fazer nesta sessão?"

Com base na resposta:
- Se match com workstream existente → leia o .md completo dela e resuma o contexto relevante
- Se match com plano existente → leia o plano, mostre progresso e sugira `/run` pra continuar execução
- Se é trabalho novo → pergunte se quer criar uma nova workstream ou plano (`/plan <tarefa>`)
- Se é exploração/pesquisa → sugira `/discover`

Confirme:
- Workstream ativa e seu estado
- Plano ativo e próximo batch (se houver)
- Próximos passos sugeridos (do campo "Contexto para próxima sessão" da workstream)
- Blockers conhecidos
