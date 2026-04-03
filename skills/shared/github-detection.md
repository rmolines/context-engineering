# GitHub Mode Detection

Bloco reutilizável — embutir nas skills que interagem com GitHub.

## Detecção (rodar no início da skill)

```bash
# 1. Tem remote?
git remote get-url origin 2>/dev/null
# 2. gh está autenticado?
gh auth status 2>/dev/null
```

**Resultado:**
- Ambos OK → `GITHUB_MODE=true`. Extrair `{owner}/{repo}` do remote URL.
- Qualquer falha → `GITHUB_MODE=false`. Seguir com comportamento local (sem erro, sem warning).

## Regras

- **Nunca falhar hard** se GitHub não está disponível. Degradação silenciosa.
- **Não cachear** o resultado entre sessões — sempre re-detectar (auth pode expirar).
- **Extrair owner/repo:** parsear output de `git remote get-url origin`:
  - SSH: `git@github.com:owner/repo.git` → `owner/repo`
  - HTTPS: `https://github.com/owner/repo.git` → `owner/repo`
  - Remover `.git` suffix se presente.
- Se o remote não é GitHub (GitLab, Bitbucket, etc.): `GITHUB_MODE=false`.

## Projects V2 — detecção adicional

### Decisão: 1 Project por repo

O plugin assume **1 Project V2 por repositório**, nomeado `"CE: {repo-name}"`. Múltiplos projects por repo não são suportados.

**Razão:** cada repo é uma unidade de trabalho com suas campaigns e plans. Um Project é a view visual disso. Para múltiplas perspectivas (só backlog, só campaign X, só sprint atual), usar **saved views com filtros** no mesmo Project — é uma feature nativa do GitHub Projects V2, sem custo de complexidade.

**Se necessário no futuro:** o cache (`.github-project-cache.json`) já indexa por `projectNumber`, o que permite evolução pra multi-project sem breaking change.

Se `GITHUB_MODE=true`, verificar se o scope `project` está disponível:

```bash
gh auth status 2>&1 | grep -q "project"
```

- Se scope `project` presente → `PROJECTS_MODE=true`. Permite operações com `gh project`.
- Se ausente → `PROJECTS_MODE=false`. Orientar: `gh auth refresh -s project,read:project`
- **Nunca bloquear** por falta de scope — issues/milestones funcionam sem Projects.

### Cache de IDs do Project

Se `PROJECTS_MODE=true`, verificar se `.claude/state/.github-project-cache.json` existe:
- Se existe → ler e usar os IDs cacheados (project ID, field IDs, option IDs)
- Se não existe → o /bootstrap cria na próxima execução

Formato do cache:
```json
{
  "projectNumber": 1,
  "projectId": "PVT_xxx",
  "owner": "username",
  "fields": {
    "Status": { "id": "PVTSSF_xxx", "options": {"Todo": "opt_1", "In Progress": "opt_2", "Done": "opt_3"} },
    "Campaign": { "id": "PVTSSF_xxx", "options": {"[C1]": "opt_a", "[Backlog]": "opt_b"} },
    "Size": { "id": "PVTSSF_xxx", "options": {"S": "opt_s", "M": "opt_m", "L": "opt_l"} }
  }
}
```

## Uso nas skills

Quando `GITHUB_MODE=true`, a skill pode usar `gh` CLI para:
- Issues: `gh issue list/create/view/close`
- Milestones: `gh api repos/{owner}/{repo}/milestones`
- Labels: `gh label create/list`
- PRs: `gh pr create/view/checks` (já usado no /run)
- Projects (se `PROJECTS_MODE=true`): `gh project create/item-add/item-edit/field-create`

Quando `GITHUB_MODE=false`, a skill opera exclusivamente com arquivos locais em `.claude/state/` — comportamento atual, inalterado.
