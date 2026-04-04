---
name: discovery
description: "Upstream: transforma pedido cru em Issue especificada no GitHub. Colaborativo (humano + Claude). Fases: entender intent (PM), propor experiência (Designer), validar com humano, spec técnica (Tech Lead), criar Issue. Pesquisa interna (codebase) e externa (web/docs). Triggers: '/discovery', 'quero X', 'preciso de', 'faz um discovery', 'vamos especificar', 'define isso', 'cria issue pra'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch
argument-hint: "[pedido | #issue-number]"
---

# /discovery — Upstream: problem → spec

> Architecture reference: `ARCHITECTURE.md` § "Discovery — upstream"
> This skill is collaborative — the human is always involved.

**Input:** `$ARGUMENTS`

| Input | Mode |
|---|---|
| rough request text | CREATE — new discovery from scratch |
| `#N` (issue number) | REFINE — enrich an existing Issue that lacks full spec |

---

## Mode CREATE

### Step 1 — Understand intent (PM role)

Parse the rough request. The human is a stakeholder, not a PM — the request may be vague, emotional, or solution-oriented rather than problem-oriented.

**Inline (no subagent):**

1. Identify what the human actually wants (the underlying need, not the literal words)
2. Read context:
   - `.claude/state/STATE.md` — what's active, what was recently done
   - `.claude/state/milestones/` — which Milestones exist, signals
   - `.claude/docs/index.md` — domain map (if exists)
3. Cross-reference with active Milestones: does this request advance one?

**Ask clarifying questions** with AskUserQuestion — but only the 2-3 questions that actually matter. Don't interrogate. Examples:
- "Is this for [user type] or internal tooling?"
- "Should this replace X or work alongside it?"
- "Is there a deadline or priority?"

If the request is already clear: skip questions, move to step 2.

### Step 2 — Research (subagents, parallel)

Two axes, always. Even simple requests benefit from quick research.

**Internal research (haiku subagent):**
- Grep codebase for related code, patterns, existing implementations
- Read canonical patterns from domain map
- Check git log for recent changes in the area
- If GITHUB_MODE=true: `gh issue list` for related open Issues

**External research (sonnet subagent via claude-code-guide or web search):**
- Docs for APIs, libraries, frameworks involved
- State of the art, best practices, reference implementations
- Current versions, breaking changes, deprecations
- **Claude Code mechanics** — if the task involves skills, hooks, settings, or any Claude Code feature, ALWAYS research via claude-code-guide subagent before proposing anything. Don't assume you know how it works.

**Mandatory external research triggers:**
- Task involves a tool/framework/API → research current docs (versions change)
- Task involves Claude Code features (skills, hooks, MCP, settings) → claude-code-guide subagent
- You're uncertain about how something works → research, don't guess

**Complexity tiers:**

| Complexity | Internal | External |
|---|---|---|
| Simple (bug, config) | Inline grep, no subagent | Skip (unless uncertainty exists) |
| Medium (feature) | Haiku subagent | Sonnet subagent |
| Complex (architecture) | Sonnet subagent (deep) | Sonnet subagent(s) |

Each subagent returns a **concise synthesis**, not a data dump.

### Step 3 — Propose experience (Designer role)

**Inline (this is conversational — the human validates).**

Based on intent (step 1) + research (step 2), propose:

1. **User flow** — what the end user sees/does, step by step
   - Not wireframes — describe in words: "User clicks X, sees Y, enters Z"
   - Include the happy path AND the main alternative paths

2. **States** — every screen/component has states:
   - Loading (what does the user see while waiting?)
   - Empty (first time, no data yet)
   - Error (what fails? how does the user recover?)
   - Success (the happy path result)

3. **Edge cases** — things that aren't obvious:
   - Concurrent users, race conditions
   - Permissions / access control
   - Offline, slow network, timeout
   - Data limits (empty, 1, 1000, 100000)

4. **Consistency check** — against existing patterns:
   - Does the project have a design system? Reference its blocks.
   - How do similar features in the project handle this?
   - Would this surprise a user who knows the existing product?

Present this to the human clearly. This is the **UX validation gate**.

### Step 4 — Validate with human ◀── GATE

Use AskUserQuestion:

> **Here's the proposed experience. Does this make sense?**
>
> [summary of user flow, states, key edge cases]
>
> Options:
> - **Looks good** — proceed to technical spec
> - **Adjust** — tell me what to change
> - **Rethink** — the approach is wrong, let's reconsider

If "Adjust": apply changes and re-present (loop step 3-4).
If "Rethink": go back to step 1 with new understanding.
If "Looks good": proceed to step 5.

**This gate is mandatory.** Never skip to technical spec without UX approval.

### Step 5 — Technical spec (Tech Lead role)

Translate the approved UX into an implementable specification.

**Inline or subagent (sonnet) depending on complexity:**

1. **Implementation approach:**
   - Which files to create/modify
   - Which canonical patterns to follow (from domain map)
   - Dependencies (libs, APIs, existing code)

2. **Data model changes** (if any):
   - New tables, columns, relations
   - Migration strategy

3. **API changes** (if any):
   - New endpoints or modifications
   - Request/response shapes
   - Auth requirements

4. **Test strategy:**
   - What to test (unit, integration, e2e)
   - Key scenarios to cover

5. **Risks and trade-offs:**
   - What could go wrong
   - Alternatives considered and why rejected

### Step 6 — Create Issue in GitHub

**If GITHUB_MODE=false:** save spec to `.claude/state/backlog/issue-pending-{slug}.md` using template `templates/state/issue/discovery.md`. Inform the user it's saved locally.

**If GITHUB_MODE=true:**

1. Identify Milestone:
   - If request maps to active Milestone → use it
   - If not → ask user: "Which Milestone, or Backlog?"

2. Create Issue:
   ```bash
   gh issue create \
     --title "{concise title}" \
     --body "$(cat <<'EOF'
   ## Intent
   {what and why, stakeholder language — from step 1}

   ## UX Flow
   {approved flow from step 3-4}

   ### States
   - **Loading:** {description}
   - **Empty:** {description}
   - **Error:** {description}
   - **Success:** {description}

   ## Technical Spec
   {from step 5 — approach, files, deps}

   ## Acceptance Criteria
   - [ ] {criterion 1 — verifiable}
   - [ ] {criterion 2 — verifiable}
   - [ ] {criterion 3 — verifiable}

   ## Design Notes
   {edge cases, consistency checks, states}

   ## Research Context
   {key findings, links, trade-offs — from step 2}

   ---
   *Created via /discovery*
   EOF
   )" \
     --milestone "{milestone title}" \
     --label "{appropriate labels}"
   ```

3. If PROJECTS_MODE=true: add to Project board with appropriate fields (Priority, Size).

4. Save discovery doc locally:
   ```
   .claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/discovery.md
   ```
   Using template `templates/state/issue/discovery.md`. Include all research, decisions, and context that's too detailed for the Issue body.

5. Report to user:
   ```
   Issue #N created: "{title}"
   Milestone: {milestone}
   Acceptance criteria: N items

   Ready for /delivery #N when you want to build it.
   ```

---

## Mode REFINE

For Issues that already exist but lack full spec (e.g., created manually in GitHub).

### Step 1 — Read existing Issue

```bash
gh issue view $ISSUE_NUMBER --json title,body,milestone,labels,comments
```

Identify what's missing: intent? UX flow? acceptance criteria? technical spec?

### Step 2 — Fill gaps

Run the relevant steps from CREATE mode:
- Missing intent → Step 1 (understand)
- Missing UX flow → Steps 2-4 (research, propose, validate)
- Missing acceptance criteria → Step 5 (technical spec) + derive criteria
- Missing everything → Run full CREATE flow

### Step 3 — Update Issue

```bash
gh issue edit $ISSUE_NUMBER --body "{updated body with full spec}"
```

Create/update local discovery doc at `.claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/discovery.md`.

---

## Rules

- **Never skip the UX gate (step 4).** The human must approve the experience before it becomes spec.
- **The Issue must be self-sufficient.** Everything the delivery agent needs must be in the Issue body.
- **Acceptance criteria are mandatory.** An Issue without criteria is not a spec.
- **Research is always dual-axis.** Internal (codebase) + external (docs/web), even if one axis is lightweight.
- **The human is a stakeholder, not a PM.** Don't expect refined input. Do the refinement work.
- **Save everything locally.** The discovery.md has richer context than the Issue body — it's the agent's extended memory.
