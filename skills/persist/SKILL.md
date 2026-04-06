---
name: persist
description: "Persistir estado da sessão via GitHub Issue comments. Usar ao finalizar uma tarefa, antes de /clear, ou ao encerrar sessão. Salva progresso, decisões e contexto para que sessões futuras continuem de onde parou. Auto-invocar quando o usuário disser: 'vou encerrar', 'sessão nova', 'contexto limpo', 'vou fechar', 'até a próxima', 'vamos terminar', 'terminar a sessão', 'terminar o trabalho', 'parar por aqui', 'vou parar'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: ""
model: haiku
effort: low
---

# /persist — Context out

> Architecture reference: `ARCHITECTURE.md` § "Persist — context out"
> Saves session learnings so future sessions continue where this one left off.

## Step 0 — Hygiene (inline, fast)

Run git diagnostics in parallel before any context work:

```bash
git diff --stat
git diff --cached --stat
git status --short
git worktree list
git branch -vv
```

Process results. All actions are opt-in — never delete or commit silently.

### Uncommitted changes
If `git diff --stat` or `git diff --cached --stat` shows changes:
> "N files with uncommitted changes. Commit before persisting?"
- If yes: stage all modified tracked files, auto-generate conventional commit message from diff summary, commit.
- If no: continue.

### Untracked files
If `git status --short` shows `??` entries:
- **Ignore:** `.claude/` and all its contents (local state, expected untracked)
- For remaining untracked files, present list:
  > "N untracked files: {list}. Commit, or skip?"
  - If commit: stage and commit with `chore: add {description}` message.
  - If skip: continue.

### Orphan worktrees
If `git worktree list` shows entries beyond the main working tree:
- For each extra worktree, check: `git log main..{branch} --oneline`
- If no unmerged commits:
  > "Worktree {name} is fully merged. Remove?"
  - If yes: `git worktree remove {path}` + `git branch -d {branch}`
- If has unmerged commits:
  > "Worktree {name} has N unmerged commits: {list}. Remove anyway?"
  - If yes: `git worktree remove --force {path}` + `git branch -D {branch}`
  - If no: keep.

### Branches gone
If `git branch -vv` shows `[gone]` entries, present list:
> "N branches with deleted remote: {list}. Clean up?"
- If yes: `git branch -d {branch}` for each (use `-D` if `-d` fails).

### Skip condition
If all 4 checks find nothing actionable: output `✓ Repo clean` and proceed to Step 2.

### Error handling
If any git command fails: skip that check silently, continue with remaining checks.
**Hygiene never blocks the persist flow.**

## Step 2 — Triage (inline, fast)

Reflect on the session. Run `git diff --stat` + `git log --oneline -10` to complement.

Classify what needs persisting:

| Type | Condition | Action |
|------|-----------|--------|
| **Session comment** | Worked on an Issue (discovery or delivery) | Post structured comment to GitHub Issue (GITHUB_MODE=true) or append to `session-log.md` (fallback) |
| **Milestone signal** | Session advanced a Milestone or revealed something unexpected | Append signal to milestone.md + sync to GitHub |
| **Memory** | New learning about user, project, or non-obvious feedback | Save/update in `~/.claude/projects/.../memory/` |
| **Direction** | Product direction decision (thesis, principles, macro architecture) | Suggest to user (don't edit automatically) |
| **Domain drift** | API, auth, schema, or actions code changed but `.claude/docs/` not updated | Alert and suggest domain map update |

**GitHub mode:** If `GITHUB_MODE=true` (see `skills/shared/github-detection.md`), Milestone signal gains GitHub sync and session context is posted as Issue comment (details below).

**Aggressive skip:** if the session was one-off (quick bugfix, question answered, exploration without decisions), say "nothing to persist" and stop. Don't force bureaucracy on sessions that don't need it.

## Step 3 — Execute in parallel

For each type marked as relevant in triage:

### Session comment (MANDATORY if worked on Issue)

If the session worked on a specific Issue AND `GITHUB_MODE=true`:

Post a structured session comment immediately — this is **not opt-in**:

```bash
gh issue comment $ISSUE_NUMBER --body "$(cat <<'EOF'
## Session [YYYY-MM-DD]

**What was done:**
- {action 1}
- {action 2}

**Decisions:**
- {decision and rationale}

**Next session:**
- {concrete next step}

**Key files:**
- {relevant paths}
EOF
)"
```

Rules for the comment content:
- The `## Session [` prefix is the contract — `/bootstrap` uses it to filter session comments from human comments. Never change this prefix.
- "What was done": 5-8 bullets max. Details are in commit history. Summarize outcomes, not steps.
- "Next session": this is the primary continuation context that next bootstrap will read. Make it specific and actionable.
- "Decisions": only non-obvious choices that future sessions need to know. Skip if none.

**Multiple Issues:** if the session worked on 2+ Issues, post one comment per Issue with only the work done on THAT Issue.

**Fallback (GITHUB_MODE=false):** append to `.claude/state/session-log.md` using the same format. This preserves local continuity without GitHub.

**No Issue worked on:** skip this step entirely.

### Milestone signal (inline, fast)

If `.claude/state/milestones/` exists and has milestone docs:

1. Identify which Milestone the session advanced — infer from work done: commits, edited files, conversation context
2. If session maps to a Milestone → append dated signal to `milestone.md`:
   ```
   - [YYYY-MM-DD] {concrete observation from the session}
   ```
   Signals are emergent observations, not work summaries. Examples:
   - "local setup is the biggest bottleneck, not docs" (insight)
   - "pattern X doesn't scale for N>100" (discovery)
   - "user prioritized Y over Z despite spec saying otherwise" (divergence)

3. If session does NOT map to any Milestone → append to the most recent milestone doc:
   ```
   - [YYYY-MM-DD] ⚡ Session outside Milestones: {work description}. Possible emergent strategy.
   ```

4. Check divergence: if 3+ consecutive sessions don't map to any Milestone:
   > "Recent sessions haven't advanced any active Milestone. This may indicate the Milestones need review or a new direction has emerged. Review Commander's Intent?"

### Milestone signal → GitHub (if GITHUB_MODE=true)

After writing the signal locally:

1. Find the GitHub Milestone:
   ```bash
   gh api repos/{owner}/{repo}/milestones --jq '.[] | select(.title | startswith("[CN]")) | {number, description}'
   ```
2. Read current Milestone description
3. Append the dated signal to the `## Signals` section
4. Update:
   ```bash
   gh api repos/{owner}/{repo}/milestones/{number} \
     --method PATCH \
     --field description="{updated description}"
   ```
5. **Size limit:** if description > 900 chars, warn user that old signals should be archived. Don't truncate automatically.

If GitHub detection fails: skip silently (local signal already saved).

### Memory (haiku subagent)

Only if there's new learning that changes how future sessions operate:
- User preferences → `type: user` or `type: feedback`
- Non-obvious project decision → `type: project`
- Useful external reference → `type: reference`

**Update** existing memory instead of duplicating. Check MEMORY.md first.

Don't save: code state, paths, debug solutions — anything derivable from git.

### Domain drift detection (inline, fast)

If `.claude/docs/index.md` exists:
1. Run `git diff --stat` and check for changes in:
   - `src/app/api/` or `app/api/` or `pages/api/` (API routes)
   - Files with `'use server'` (server actions)
   - Auth files (`auth.ts`, `session.ts`, `api-auth.ts`, `proxy.ts`)
   - DB/schema files (`db-*.ts`, `schema.prisma`, `migrations/`)
   - `.env*` (environment variables)
2. If changes in those paths AND `.claude/docs/index.md` not modified this session:
   > **Domain map may be outdated.** Changes detected in [APIs/auth/schema/actions]. Update `.claude/docs/index.md`?

If `.claude/docs/index.md` doesn't exist: do nothing.

### Direction (inline, suggest only)

If a direction decision was made:
> "Project direction may have changed. Update Commander's Intent in CLAUDE.md?"

Only edit with explicit confirmation.

## Step 4 — Continuation prompt + summary

Generate a copyable block for next session. Note: if a session comment was posted to a GitHub Issue, this same context is now also stored there — next `/bootstrap` will load it automatically.

```
## Session continuation

### Context
<!-- What, which Issue/Milestone, key decisions — 2-3 sentences -->

### Next steps
<!-- Concrete actions in order -->

### Key files
<!-- Relevant paths -->

### Milestone
<!-- Which Milestone this session advanced, if any -->
```

Show user what was saved (1-2 lines) + the prompt above. If a session comment was posted to GitHub, add: "Also posted to Issue #N — next bootstrap will pick this up."
