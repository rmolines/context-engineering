---
name: init
description: "Setup do Context Engineering no projeto. Configura camadas nativas do Claude Code (CLAUDE.md, rules, hooks) e cria camadas CE (state, domain map, GitHub). Idempotente — safe to re-run. '/init' em qualquer projeto novo ou pra checar saúde do setup."
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
model: sonnet
effort: medium
---

# /init — CE project setup

> Architecture reference: `ARCHITECTURE.md` § "Foundation: Claude Code context layers"
> This skill is idempotent — always safe to run.
> CE manages native Claude Code layers AND creates new ones. This skill sets up both.

**No arguments.** Run in the root of any project.

---

## Phase 1 — Diagnose

Check every context layer. Two categories: native Claude Code layers that CE configures, and new layers that CE creates.

### 1.1 Native layers

**CLAUDE.md:**
```
CLAUDE_MD = ./CLAUDE.md or ./.claude/CLAUDE.md exists?
```
If exists: check for `## Commander's Intent` section (CE format indicator).

**Rules:**
```
RULES_DIR = .claude/rules/ exists?
```
If exists: list which rules are installed.

**Memory:**
```
MEMORY = check if auto-memory is active (informational only — CE doesn't create this)
```

**Hooks:**
```
HOOKS = .claude/settings.json exists? Has SessionStart hook configured?
```
Informational — CE doesn't configure hooks in this version.

### 1.2 CE layers

**State directory:**
```
STATE_DIR    = .claude/state/ exists?
MILESTONES   = .claude/state/milestones/ exists?
```

**Domain map:**
```
DOMAIN_MAP   = .claude/docs/index.md exists?
```

**GitHub infrastructure:**

Reference: `skills/shared/github-detection.md` — run detection first.

```
HAS_REMOTE   = git remote get-url origin (success?)
GH_AUTH      = gh auth status (success?)
```

If GITHUB_MODE=true:
```
LABELS       = check if priority/size/ai-generated labels exist
MILESTONES   = check if GitHub Milestones match local milestone docs
PROJECTS_V2  = check if Project board exists (if PROJECTS_MODE=true)
```

**CI:**
```
CI           = .github/workflows/ci.yml exists?
HAS_PACKAGE  = package.json exists? (CI only relevant for projects with build tooling)
```

## Phase 2 — Report + confirm

Present diagnostic in clear format:

```
CE Health Check:

Native layers (Claude Code):
  ✅ CLAUDE.md — exists, has Commander's Intent
  ✅ Rules — 3 rules installed (session-cycle, standards, context-docs)
  ⚠️  Memory — active (not managed by CE)
  ℹ️  Hooks — no SessionStart hook configured

CE layers:
  ✅ .claude/state/ — exists
  ✅ .claude/state/milestones/ — exists, 3 milestones
  ❌ Domain map — missing
  ✅ GitHub labels — 8/8 present
  ✅ GitHub milestones — 3 synced
  ❌ CI — not configured
```

Then list proposed actions:

```
Proposed actions:
  1. Generate domain map (.claude/docs/index.md)
  2. Set up CI (.github/workflows/ci.yml)

Proceed? [Y/n]
```

Use AskUserQuestion for confirmation. Only list actions that would change something — if everything is healthy, report and exit:

```
CE Health Check: All layers healthy. ✅
Run /bootstrap to load session context.
```

### Rules for Phase 2:
- Never modify existing files without asking
- CLAUDE.md exists but lacks CE format → suggest, don't overwrite
- GitHub auth fails → report and continue with local layers
- No actions needed → report health and exit immediately

## Phase 3 — Execute

Execute only the actions the user approved. Order matters:

### 3.1 Directory structure (inline)

```bash
mkdir -p .claude/state/milestones
mkdir -p .claude/docs
```

### 3.2 CLAUDE.md (inline, only if missing)

If no CLAUDE.md exists at all:
1. Read `README.md`, `package.json` / `pyproject.toml` / `Cargo.toml` for project identity
2. Generate from template `templates/claude-md-root.md`
3. Fill in: project name, description, structure, commands
4. Present to user for review before saving

If CLAUDE.md exists but lacks CE sections:
> "Your CLAUDE.md exists but doesn't have CE sections (Commander's Intent, Domain knowledge pointer, Context discipline). Want me to suggest additions?"

If yes: propose additions as an Edit, not a rewrite.

### 3.3 Domain map (sonnet subagent)

Generate `.claude/docs/index.md` with project scan:

Subagent instructions:
```
Scan the project and generate a domain map following the template at
templates/docs/index.md. For each section:

API Surface:
- Search for routes in src/app/api/, app/api/, pages/api/, routes/, or framework equivalent
- For each route: path, HTTP methods, auth type
- Format: [semantic name](relative/path) — method(s), auth type

Server Actions:
- Search for files with 'use server'
- List each exported action with path and purpose

Auth:
- Look for: auth.ts, session.ts, middleware.ts, proxy.ts, api-auth.ts
- Identify mechanism(s): JWT, session cookie, API key, OAuth
- Point to implementation file(s)

Data Model:
- Look for: prisma/schema.prisma, drizzle/, db-*.ts, models/, schema.ts, migrations/
- Point to schema/query files

Canonical Patterns:
- Best example of each type: API route, page/component, server action
- List as canonical reference

Environment Variables:
- Read .env.example, .env.template or extract from process.env. usage
- List each var with purpose (not value)

Omit sections the project doesn't have.
Return the complete index.md content.
```

Present to user for review before saving.

### 3.4 GitHub labels (inline, idempotent)

Only if GITHUB_MODE=true:

```bash
gh label create "priority:urgent" --color "B60205" --description "Urgente" || true
gh label create "priority:high" --color "D93F0B" --description "Alta" || true
gh label create "priority:normal" --color "0E8A16" --description "Normal" || true
gh label create "priority:low" --color "C2E0C6" --description "Baixa" || true
gh label create "size:S" --color "C2E0C6" --description "Pequeno" || true
gh label create "size:M" --color "FEF2C0" --description "Médio" || true
gh label create "size:L" --color "F9D0C4" --description "Grande" || true
gh label create "ai-generated" --color "1D76DB" --description "PR criado por agente AI" || true
```

### 3.5 GitHub milestones (inline, idempotent)

Only if GITHUB_MODE=true:

Read `.claude/state/milestones/` for existing milestone docs:
1. For each milestone doc, check if GitHub Milestone exists
2. If not: create via `gh api repos/{owner}/{repo}/milestones --method POST`
3. Ensure `[Backlog]` Milestone exists

### 3.6 Projects V2 (inline, idempotent)

Only if PROJECTS_MODE=true.

Reference: `skills/shared/github-detection.md` — section "Projects V2".

#### Create/find Project

```bash
EXISTING=$(gh project list --owner {owner} --format json | jq -r '.projects[] | select(.title == "CE: {repo-name}") | .number')
if [ -z "$EXISTING" ]; then
  PROJECT_NUMBER=$(gh project create --owner {owner} --title "CE: {repo-name}" --format json | jq -r '.number')
else
  PROJECT_NUMBER=$EXISTING
fi
```

#### Link to repository

```bash
gh project link $PROJECT_NUMBER --owner {owner} --repo {owner}/{repo}
```

#### Create custom fields (idempotent)

```bash
EXISTING_FIELDS=$(gh project field-list $PROJECT_NUMBER --owner {owner} --format json | jq -r '.fields[].name')

echo "$EXISTING_FIELDS" | grep -q "Priority" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Priority" --data-type SINGLE_SELECT \
    --single-select-options "Urgent,High,Normal,Low"

echo "$EXISTING_FIELDS" | grep -q "Size" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Size" --data-type SINGLE_SELECT \
    --single-select-options "S,M,L"

echo "$EXISTING_FIELDS" | grep -q "Start Date" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Start Date" --data-type DATE

echo "$EXISTING_FIELDS" | grep -q "Target Date" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Target Date" --data-type DATE
```

#### Cache field IDs

Query GraphQL and save to `.claude/state/project-cache.json`:

```bash
gh api graphql -f query='query($login: String!, $number: Int!) {
  user(login: $login) { projectV2(number: $number) { id fields(first: 20) { nodes {
    ... on ProjectV2SingleSelectField { id name options { id name } }
    ... on ProjectV2Field { id name }
  }}}}
}' -F login="{owner}" -F number=$PROJECT_NUMBER
```

#### First-time guidance

On first Project creation:
> "Project V2 created: {url}.
> Recommend configuring in UI:
> 1. **Workflows:** Settings → Workflows → 'Item added' → Status = Todo / 'Issue closed' → Status = Done
> 2. **Roadmap view:** + New view → Layout: Roadmap → Date fields: Start Date / Target Date
> 3. **Board view:** + New view → Layout: Board → Group by: Status"

### 3.7 CI setup (inline, with confirmation)

Only if: no CI + has package.json + has GitHub remote.

**Ask user before creating:**
> "Set up GitHub Actions CI (lint + test + build)?"

If yes:
1. Detect stack (package manager, Node version, available scripts in package.json)
2. Generate `.github/workflows/ci.yml` from `templates/ci/`
3. Ensure `ai-generated` label exists on GitHub
4. Report what was created

If no: skip.

### 3.8 Initial project scan (inline, only for new projects)

Only if `.claude/state/` was just created (first run):
- Read `README.md`, `CLAUDE.md`, `package.json` or equivalent
- Run `git log --oneline -20` for recent activity
- Run `git branch -a` for active branches
- List first-level directories

This provides context for the first `/bootstrap` session.

## Phase 4 — Report

```
CE initialized:
  ✅ CLAUDE.md — created from template
  ✅ Domain map — generated at .claude/docs/index.md
  ✅ State directory — created
  ✅ GitHub labels — 8 created
  ✅ CI — configured at .github/workflows/ci.yml

Run /bootstrap to load session context.
```

---

## Rules

- **Never modify existing files without asking.** CLAUDE.md, README.md — suggest changes, don't overwrite.
- **Idempotent.** Running /init twice produces the same result. No duplicate labels, no overwritten files.
- **User confirms before executing.** Phase 2 is the gate.
- **GitHub failures are non-fatal.** If gh fails, continue with local layers.
- **Domain map requires review.** Never save domain map without user seeing it first.
- **This is infra, not session.** /init never loads deep context, never does briefing, never aligns. That's /bootstrap's job.
