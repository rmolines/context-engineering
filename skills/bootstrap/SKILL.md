---
name: bootstrap
description: "Carregar estado do projeto, inicializar o que falta, alinhar sessão. Idempotente — sempre seguro de rodar. Detecta automaticamente se precisa inicializar ou recarregar. Usar: '/bootstrap' em qualquer projeto, a qualquer momento."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /bootstrap — Gestão de estado do projeto

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

## 3. Carregar estado

Leia `.claude/state/STATE.md` e mostre overview:

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
