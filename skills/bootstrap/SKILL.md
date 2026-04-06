---
name: bootstrap
description: "Carregar contexto da sessão. Query live ao GitHub, deep context loading, briefing, alinhamento. Rodar no início de cada sessão. '/bootstrap' carrega e alinha. '/bootstrap migrate-to-github' migra estado local para GitHub Issues/Milestones."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: "[migrate-to-github]"
model: haiku
effort: low
---

# /bootstrap — Session context in

> Architecture reference: `ARCHITECTURE.md` § "Bootstrap — context in"
> This skill is idempotent — always safe to run.
> For project setup (dirs, domain map, GitHub labels, CI), use `/init` instead.

**Input:** `$ARGUMENTS`

| Input | Mode |
|---|---|
| empty | DEFAULT — load context, briefing, align |
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

### Step 5 — Report migration

Report what was migrated (Issues created, Milestones created, disk directories created).

---

## Mode DEFAULT

Loads session context. Does NOT initialize — for setup, use `/init`.

## 1. Detect

```
CE_INITIALIZED = .claude/state/ exists?
HAS_REMOTE     = git remote get-url origin (success?)
GH_AUTH        = gh auth status (success?)
```

If NOT CE_INITIALIZED:
> "CE not set up in this project. Run `/init` first."
> Abort.

Reference: `skills/shared/github-detection.md` — run GitHub detection.

## 2. Live sync

**Run only if** GITHUB_MODE=true. If any check fails: skip silently and proceed with local flow (step 3).

### GitHub — live query

Fetch all open Issues with their last 5 comments in a single GraphQL call:

1. Extract owner/repo from remote:
   ```bash
   git remote get-url origin
   # e.g. https://github.com/owner/repo.git → OWNER=owner, REPO=repo
   ```

2. Fetch open Issues with comments (GraphQL):
   ```bash
   gh api graphql -f query='
     query($owner: String!, $repo: String!) {
       repository(owner: $owner, name: $repo) {
         issues(first: 100, states: OPEN) {
           edges {
             node {
               number
               title
               body
               milestone { title }
               labels(first: 10) { nodes { name } }
               comments(last: 5) {
                 edges { node { body createdAt } }
               }
             }
           }
           pageInfo { hasNextPage endCursor }
         }
       }
     }
   ' -f owner="$OWNER" -f repo="$REPO"
   ```
   If `pageInfo.hasNextPage` is true: repeat with `after: $endCursor` until all Issues are fetched.

3. Fetch recently closed Issues (REST — simple list is sufficient here):
   ```bash
   gh issue list --state closed --json number,title,milestone,labels,closedAt --limit 50
   ```

### Open PRs — lifecycle check

Fetch open PRs to detect pending merges:

```bash
gh pr list --state open --json number,title,headRefName,labels,createdAt,isDraft --limit 50
```

Cross-reference PRs with Issues:
- Match via branch naming: regex `/^agent\/(\d+)-/` extracts Issue number from branch `agent/25-foo`
- Match via PR body: parse `Closes #N` or `Fixes #N`
- For each PR, classify:

| State | How to detect | Flag |
|---|---|---|
| **Fresh** | Created <3 days ago | info only |
| **Stale** | Created >3 days ago, CI passed | ⚠ yellow — suggest merge |
| **CI failed** | Last check failed | 🔴 red — suggest diagnosis |
| **Draft** | `isDraft: true` | info only |

If zero open PRs: skip this section entirely (no visible change to existing flow).
If GITHUB_MODE=false: skip silently.

No file is written to disk. The GraphQL response and PR list are the session's view of project state — held in memory for steps 3 and 4.

### Disk structure — ensure Issue directories

For each open Issue from the GraphQL response:
1. Determine Milestone slug (or `backlog/`)
2. Check if `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/` exists
3. If not: create directory. Only `discovery.md` is bootstrapped here (when Issue has `## Acceptance Criteria` in body). `plan.md` and `execution-log.md` are created by `/discovery` and `/delivery`, not bootstrap.

For each Milestone without a local doc:
1. Create `.claude/state/milestones/{slug}/milestone.md` from template
2. Populate with Milestone description from GitHub

### Milestone docs — sync signals

For each Milestone that has a local `milestone.md`:
1. Read GitHub Milestone description via `gh api`
2. If there are signals in GitHub not in local doc: add them
3. If there are signals in local doc not in GitHub: sync to GitHub (append to description)

### Change detection

If GITHUB_MODE=true, detect changes since last session by scanning session comments:
- A session comment is any comment whose body starts with `## Session [`
- Find Issues where the most recent session comment predates the current session start
- Find Issues that were closed since the last session comment date across all Issues

If changes are detected:
```
⚡ Changes since last session:
- N new Issues: #N "title", #M "title"
- N closed Issues: #N "title" (via PR #M)
- N Issues with new activity
```

### Stale Issues (if GITHUB_MODE=true)

Filter Issues from the GraphQL response where `updatedAt` > 30 days ago:
```
⚠ Stale Issues (30+ days):
- #N title — last activity: YYYY-MM-DD (Nd)
Action: close, move to backlog, or update with context.
```

Don't auto-close — just inform.

## 3. Load deep context

This is the most important step. The sync (steps 1-2) is infrastructure.
**This step is what makes the session useful.**

### 3.1. Read active Milestone docs

For each active Milestone (open on GitHub):
1. Read `.claude/state/milestones/{slug}/milestone.md`
2. Extract: intent, success state, **last 5 signals** (most recent first)
3. This tells the agent: what are we trying to achieve and what have we learned

### 3.2. Read in-progress Issue context

For each open Issue from the GraphQL response, classify using comments and body:

A **session comment** is any comment whose body starts with `## Session [`.

| State | How to detect | Priority |
|---|---|---|
| **Ready for delivery** | Issue body has `## Acceptance Criteria`, zero session comments | High — can be worked on now |
| **Delivery in progress** | Last session comment contains `Next session:` field | High — has momentum |
| **Blocked** | Last session comment contains `Blocked:` | Medium — needs attention |
| **Needs discovery** | Issue body lacks `## Acceptance Criteria` | Low — needs human |
| **Just created** | No body content beyond the title | Low — needs triage |

If the Issue directory exists locally and has a `discovery.md`, read it for deeper context (decisions, UX flow, technical spec).

### 3.3. Read continuation context

Scan the last session comment across all open Issues (from the GraphQL response):
- Find the most recent comment (by `createdAt`) that starts with `## Session [`
- Extract the `Next session:` field from that comment
- This is the handoff from the previous session's `/persist` — it IS the continuation context

No execution-log.md scanning needed. GitHub comments are the source of truth.

### 3.4. Read domain map

If `.claude/docs/index.md` exists: read it. This gives the agent the project's technical landscape (APIs, auth, schema, patterns).

## 4. Briefing + align

**Present a concise, actionable briefing, then propose next action.**

### Briefing format

```
📋 Briefing

[Continuation from last session]
Last session (YYYY-MM-DD): {what was done}
Left off at: {Next session: field from last session comment}

[Ready for action]
- #N "title" — ready for /delivery (spec complete, no blockers)
- #N "title" — delivery in progress, N/M deliverables done

[PRs awaiting merge]
- PR #50 "title" → #49 — opened Nd ago, branch: agent/49-slug
  ⚠ Stale: open >3 days
- PR #62 "title" → #N — opened 1d ago (fresh)

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
- "PRs awaiting merge" section only appears when there are open PRs. Omit entirely if zero.
- Include the *why* for blocked items, not just the status
- Continuation context is the most valuable line — put it at the top
- If nothing is in progress, say so: "Clean slate — no active work."

### Align — propose, don't just ask

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
- If working on Issue #N → read its full discovery.md (if present), show last 3 session comments from the GraphQL data, and summarize
- If working on a Milestone → show all its Issues with states and suggest which to tackle
- If new request → suggest `/discovery "{request}"` to create a spec'd Issue
- If exploration → proceed directly, no Issue needed

Confirm:
```
Session aligned:
- Working on: #N "title" (Milestone: [CN])
- Context loaded: {what was read — discovery.md, session comments, milestone doc}
- Suggested approach: {/discovery or /delivery or direct work}
```
