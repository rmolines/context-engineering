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

## Uso nas skills

Quando `GITHUB_MODE=true`, a skill pode usar `gh` CLI para:
- Issues: `gh issue list/create/view/close`
- Milestones: `gh api repos/{owner}/{repo}/milestones`
- Labels: `gh label create/list`
- PRs: `gh pr create/view/checks` (já usado no /run)

Quando `GITHUB_MODE=false`, a skill opera exclusivamente com arquivos locais em `.claude/state/` — comportamento atual, inalterado.
