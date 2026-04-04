---
name: persist
description: "Persistir estado da sessão atual pro disco. Usar ao finalizar uma tarefa, antes de /clear, ou ao encerrar sessão. Salva progresso, decisões e contexto para que sessões futuras continuem de onde parou. Auto-invocar quando o usuário disser: 'vou encerrar', 'sessão nova', 'contexto limpo', 'vou fechar', 'até a próxima', 'vamos terminar', 'terminar a sessão', 'terminar o trabalho', 'parar por aqui', 'vou parar'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
argument-hint: ""
model: haiku
effort: low
---

# /persist — Context out

> Architecture reference: `ARCHITECTURE.md` § "Persist — context out"
> Saves session learnings so future sessions continue where this one left off.

## Step 1 — Triage (inline, fast)

Reflect on the session. Run `git diff --stat` + `git log --oneline -10` to complement.

Classify what needs persisting:

| Type | Condition | Action |
|------|-----------|--------|
| **Execution log** | Worked on an Issue (discovery or delivery) | Update/create execution-log.md in Issue directory |
| **Milestone signal** | Session advanced a Milestone or revealed something unexpected | Append signal to milestone.md + sync to GitHub |
| **Memory** | New learning about user, project, or non-obvious feedback | Save/update in `~/.claude/projects/.../memory/` |
| **Direction** | Product direction decision (thesis, principles, macro architecture) | Suggest to user (don't edit automatically) |
| **Domain drift** | API, auth, schema, or actions code changed but `.claude/docs/` not updated | Alert and suggest domain map update |

**GitHub mode:** If `GITHUB_MODE=true` (see `skills/shared/github-detection.md`), Milestone signal and Execution log gain GitHub sync (details below).

**Aggressive skip:** if the session was one-off (quick bugfix, question answered, exploration without decisions), say "nothing to persist" and stop. Don't force bureaucracy on sessions that don't need it.

## Step 2 — Execute in parallel

For each type marked as relevant in triage:

### Execution log (inline or haiku subagent)

If the session worked on a specific Issue:

1. Find the Issue directory: `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/`
2. If directory doesn't exist: create it
3. If `execution-log.md` doesn't exist: create from template `templates/state/issue/execution-log.md`
4. Append session entry:

```markdown
### YYYY-MM-DD — Session N

**What was done:**
- {action 1}
- {action 2}

**Problems encountered:**
- {problem and resolution}

**Decisions made:**
- {decision and rationale}
```

### Execution log → GitHub Issue comment (if GITHUB_MODE=true)

Offer (don't force) to register session context as comment on the relevant Issue:

1. Check if the Issue has a number (is on GitHub)
2. If yes, ask:
   > "Register session context as comment on Issue #N ({title})?"
3. If yes:
   ```bash
   gh issue comment N --body "$(cat <<'EOF'
   ## Session update [YYYY-MM-DD]

   **What was done:** {summary}
   **Decisions:** {key decisions}
   **Next session:** {continuation context}
   **Key files:** {relevant paths}
   EOF
   )"
   ```

If no open Issues were worked on: don't offer.

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

## Step 3 — Continuation prompt + summary

Generate a copyable block for next session:

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

Show user what was saved (1-2 lines) + the prompt above.
