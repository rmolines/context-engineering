---
name: bootstrap
description: "Carregar estado do projeto, inicializar o que falta, alinhar sessão. Idempotente — sempre seguro de rodar. Detecta automaticamente se precisa inicializar ou recarregar. Usar: '/bootstrap' em qualquer projeto, a qualquer momento. '/bootstrap migrate-to-github' migra estado local para GitHub Issues/Milestones."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: "[migrate-to-github]"
model: haiku
effort: low
---

# /bootstrap — Context in

> Architecture reference: `ARCHITECTURE.md` § "Bootstrap — context in"
> This skill is idempotent — always safe to run.

**Input:** `$ARGUMENTS`

| Input | Mode |
|---|---|
| empty | DEFAULT — detect, initialize, load, align |
| `migrate-to-github` | MIGRATE — migrate local state to GitHub Issues/Milestones |

---

## Mode MIGRATE (migrate-to-github)

Migrates local state (legacy campaigns.md, plan files) to GitHub Issues/Milestones and new disk structure.

Reference: `skills/shared/github-detection.md` — run detection. If `GITHUB_MODE=false`: abort with clear message.

### Step 1 — Audit local state

1. Read `.claude/state/campaigns.md` (if exists) → list Milestones active + completed
2. Read `plan-*.md` in `.claude/state/` (if any):
   - Status `active` → list deliverables without `Issue: #N`
   - Status `completed` → count (history to migrate as closed Milestones)
3. Read `## Strategic Review Log` from campaigns.md (if exists)
4. Scan `.claude/state/milestones/` for any new-format docs already present
5. Present summary and ask for confirmation before creating anything

### Step 2 — Create Milestones (idempotent)

For each active campaign/milestone:
1. Check if Milestone `[CN] name` already exists on GitHub
2. If not: create via `gh api repos/{owner}/{repo}/milestones --method POST`
3. Create `[Backlog]` Milestone if not exists

For each completed campaign: create as closed Milestone.

### Step 3 — Create disk structure

For each Milestone (active + completed):
```
.claude/state/milestones/{slug}/milestone.md
```
Using template `templates/state/milestones/milestone.md`.
Populate with intent, success state, and signals from campaigns.md.

For each existing Issue on GitHub with a Milestone:
```
.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/
```
Create directory. If there's a legacy plan file referencing this issue, move relevant content to `plan.md` in the new location.

### Step 4 — Migrate legacy files

- `campaigns.md` → content distributed into individual `milestone.md` files. Archive original as `campaigns.md.archive`.
- `plan-*.md` → if linked to issues, content moves to `milestones/{slug}/issue-{N}/plan.md`. If not linked, stays as-is with deprecation note.
- Workstream `.md` files → if they map to an Issue, move to the Issue directory. If standalone, keep in `.claude/state/`.

### Step 5 — Rebuild STATE.md + report

Run the STATE.md rebuild from DEFAULT mode step 2.5. Report what was migrated.

---

## Mode DEFAULT

Idempotent. Detects what exists, initializes what's missing, reloads state.

## 1. Detect state

```
STATE.md         = .claude/state/STATE.md exists?
MILESTONES_DIR   = .claude/state/milestones/ exists?
DOMAIN_MAP       = .claude/docs/index.md exists?
CI               = .github/workflows/ci.yml exists?
HAS_PACKAGE_JSON = package.json exists?
HAS_REMOTE       = git remote get-url origin (success?)
```

## 2. Ensure structure (idempotent)

### STATE.md
- **If exists:** read and proceed to step 2.5
- **If not:** create `.claude/state/STATE.md`:

```markdown
# Project State

## Active

## Backlog

## Completed
```

### Initial discovery (only if STATE.md was just created)
- Read `README.md`, `CLAUDE.md`, `package.json`, `Cargo.toml`, `pyproject.toml` or equivalent
- Run `git log --oneline -20` for recent activity
- Run `git branch -a` for active branches
- List first-level directories for project structure

### Domain map
- **If exists:** skip (drift detection is in /persist)
- **If not:** generate `.claude/docs/index.md` with project scan:

**API Surface:**
- Search for routes in `src/app/api/`, `app/api/`, `pages/api/`, `routes/`, or framework equivalent
- For each route: path, HTTP methods, auth type
- Format: `- [semantic name](relative/path) — method(s), auth type`

**Server Actions:**
- Search for files with `'use server'`
- List each exported action with path and purpose

**Auth:**
- Look for: `auth.ts`, `session.ts`, `middleware.ts`, `proxy.ts`, `api-auth.ts`
- Identify mechanism(s): JWT, session cookie, API key, OAuth
- Point to implementation file(s)

**Data Model:**
- Look for: `prisma/schema.prisma`, `drizzle/`, `db-*.ts`, `models/`, `schema.ts`, `migrations/`
- Point to schema/query files

**Canonical Patterns:**
- Best example of each type: API route, page/component, server action
- List as canonical reference

**Environment Variables:**
- Read `.env.example`, `.env.template` or extract from `process.env.` usage
- List each var with purpose (not value)

Omit sections the project doesn't have. Use subagents to parallelize if large.
Present to user for review before saving.

### Milestones directory
- **If exists:** skip
- **If not and GITHUB_MODE=true:** create from GitHub Milestones (step 2.5 handles)
- **If not and GITHUB_MODE=false:** create empty `.claude/state/milestones/`

### CI (only if: no CI + has package.json + has GitHub remote)
**Ask user before creating.** CI setup is a side effect — don't surprise.
> "Project has no CI configured. Set up GitHub Actions (lint + test + build)?"
If yes:
1. Detect stack (package manager, Node version, available scripts)
2. Generate `.github/workflows/ci.yml` from `templates/ci/`
3. Ensure `ai-generated` label exists on GitHub
4. Inform user
If no: skip.

## 2.5. GitHub sync

**Run only if** project has GitHub remote AND `gh auth status` succeeds. If any check fails: skip silently and proceed with local flow (steps 3+).

Reference: `skills/shared/github-detection.md` — run detection.

### Labels (idempotent)

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

### Milestones (idempotent)

Read `.claude/state/milestones/` for existing milestone docs:
1. For each milestone doc, check if GitHub Milestone exists
2. If not: create via `gh api repos/{owner}/{repo}/milestones --method POST`
3. Ensure `[Backlog]` Milestone exists

### Projects V2 (if PROJECTS_MODE=true)

Reference: `skills/shared/github-detection.md` — section "Projects V2".

If `PROJECTS_MODE=false`: skip silently.

#### Create/find Project (idempotent)

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

# Priority
echo "$EXISTING_FIELDS" | grep -q "Priority" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Priority" --data-type SINGLE_SELECT \
    --single-select-options "Urgent,High,Normal,Low"

# Size
echo "$EXISTING_FIELDS" | grep -q "Size" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Size" --data-type SINGLE_SELECT \
    --single-select-options "S,M,L"

# Start Date (for Roadmap view)
echo "$EXISTING_FIELDS" | grep -q "Start Date" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Start Date" --data-type DATE

# Target Date (for Roadmap view)
echo "$EXISTING_FIELDS" | grep -q "Target Date" || \
  gh project field-create $PROJECT_NUMBER --owner {owner} \
    --name "Target Date" --data-type DATE
```

Note: Status field is created by default (Todo, In Progress, Done).
Milestone is a native GitHub field — no custom field needed.

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

If cache exists and `projectNumber` matches: verify fields haven't changed. If changed, regenerate.

#### Add Issues to board

For each open Issue not yet on the board:
```bash
ITEM_ID=$(gh project item-add $PROJECT_NUMBER --owner {owner} --url {issue_url} --format json | jq -r '.id')
gh project item-edit --id $ITEM_ID --project-id $PROJECT_ID \
  --field-id $SIZE_FIELD_ID --single-select-option-id $SIZE_OPTION
```

#### First-time guidance

On first Project creation:
> "Project V2 created: {url}.
> Recommend configuring in UI:
> 1. **Workflows:** Settings → Workflows → 'Item added' → Status = Todo / 'Issue closed' → Status = Done
> 2. **Roadmap view:** + New view → Layout: Roadmap → Date fields: Start Date / Target Date
> 3. **Board view:** + New view → Layout: Board → Group by: Status"

### STATE.md — rebuild cache

Regenerate STATE.md from GitHub:

1. Fetch open Issues:
   ```bash
   gh issue list --state open --json number,title,milestone,labels --limit 200
   ```
2. Fetch recently closed Issues (30 days):
   ```bash
   gh issue list --state closed --json number,title,milestone,labels,closedAt --limit 50
   ```
3. Generate STATE.md:

```markdown
# Project State
<!-- Generated from GitHub at YYYY-MM-DDTHH:MM:SSZ — do not edit manually -->
<!-- Regenerated by /bootstrap. Source of truth: GitHub Issues/Milestones. -->

## Active
- #N título — Milestone: [CN], size:Y

## Backlog
- #N título

## Completed (last 30 days)
- #N título — closed YYYY-MM-DD via PR #M
```

If no Issues on GitHub: keep existing STATE.md (don't overwrite with empty).

### Disk structure — ensure Issue directories

For each open Issue:
1. Determine Milestone slug (or `backlog/`)
2. Check if `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/` exists
3. If not: create directory (files are created by /discovery and /delivery, not bootstrap)

For each Milestone without a local doc:
1. Create `.claude/state/milestones/{slug}/milestone.md` from template
2. Populate with Milestone description from GitHub

### Milestone docs — sync signals

For each Milestone that has a local `milestone.md`:
1. Read GitHub Milestone description via `gh api`
2. If there are signals in GitHub not in local doc: add them
3. If there are signals in local doc not in GitHub: sync to GitHub (append to description)

### Change detection

Compare current Issues with previous STATE.md to detect changes since last session.

If GITHUB_MODE=true and changes detected:
```
⚡ Changes since last session:
- N new Issues: #N "title", #M "title"
- N closed Issues: #N "title" (via PR #M)
- N updated Issues
```

### Stale Issues (if GITHUB_MODE=true)

```bash
gh issue list --state open --json number,title,updatedAt --limit 100
```

Filter Issues with `updatedAt` > 30 days ago:
```
⚠ Stale Issues (30+ days):
- #N title — last activity: YYYY-MM-DD (Nd)
Action: close, move to backlog, or update with context.
```

Don't auto-close — just inform.

## 3. Load deep context

This is the most important step. The sync (steps 1-2.5) is infrastructure.
**This step is what makes the session useful.**

### 3.1. Read active Milestone docs

For each active Milestone (open on GitHub):
1. Read `.claude/state/milestones/{slug}/milestone.md`
2. Extract: intent, success state, **last 5 signals** (most recent first)
3. This tells the agent: what are we trying to achieve and what have we learned

### 3.2. Read in-progress Issue context

For each open Issue that has local docs:
1. Check `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/` for:
   - `discovery.md` → decisions, UX flow, technical spec, acceptance criteria
   - `plan.md` → decomposition, which deliverables are done/pending
   - `execution-log.md` → last session entry, problems encountered, decisions made
2. Classify each Issue:

| State | How to detect | Priority |
|---|---|---|
| **Ready for delivery** | Has discovery.md with acceptance criteria, no open PR | High — can be worked on now |
| **Delivery in progress** | Has plan.md with pending deliverables, or open PR | High — has momentum |
| **Blocked** | Execution log mentions blocker, or stale >7 days with plan | Medium — needs attention |
| **Needs discovery** | No discovery.md, or discovery.md without acceptance criteria | Low — needs human |
| **Just created** | No local docs at all | Low — needs triage |

### 3.3. Read continuation context

Check for the most recent signal across all execution-log.md files:
- Find the entry with the latest date
- Extract: "Next session" / "Próxima sessão" / "Next steps" field
- This is what the previous session's /persist left as handoff

### 3.4. Read domain map

If `.claude/docs/index.md` exists: read it. This gives the agent the project's technical landscape (APIs, auth, schema, patterns).

## 4. Briefing

**Present a concise, actionable briefing. Not a data dump — a squad standup.**

Format:

```
📋 Briefing

[Continuation from last session]
Last session (YYYY-MM-DD): {what was done}
Left off at: {continuation context from execution-log}

[Ready for action]
- #N "title" — ready for /delivery (spec complete, no blockers)
- #N "title" — delivery in progress, N/M deliverables done

[Needs attention]
- #N "title" — blocked: {reason}
- #N "title" — stale (Nd since last activity)

[Needs discovery]
- #N "title" — no spec yet, needs /discovery

[Milestones]
- [CN] Name — N open / N closed, momentum: {high|low}
  Last signal: "{most recent signal}"
```

**Rules for the briefing:**
- Only show sections that have content (don't show empty sections)
- "Ready for action" items first — these are what the user can act on
- Include the *why* for blocked items, not just the status
- Continuation context is the most valuable line — put it at the top
- If nothing is in progress, say so: "Clean slate — no active work."

## 5. Align

**Don't just ask "what are we doing?" — propose based on what you know.**

### If there's continuation context:
> "Last session left off at: {context}. Continue with that?"

### If there's no continuation but there are ready Issues:
> "Issue #N ({title}) is ready for delivery — spec complete, no blockers. Start there?"

### If everything is in discovery or blocked:
> "No Issues ready for delivery. Options:
> - `/discovery` on #N to complete its spec
> - Unblock #M by {action}
> - Something new?"

### If clean slate (no open Issues):
> "No active work. What's on your mind?"

**After user responds:**

Based on response, **load the relevant deep context**:
- If working on Issue #N → read its full discovery.md, plan.md, execution-log.md and summarize
- If working on a Milestone → show all its Issues with states and suggest which to tackle
- If new request → suggest `/discovery "{request}"` to create a spec'd Issue
- If exploration → proceed directly, no Issue needed

Confirm:
```
Session aligned:
- Working on: #N "title" (Milestone: [CN])
- Context loaded: {what was read}
- Suggested approach: {/discovery or /delivery or direct work}
```
