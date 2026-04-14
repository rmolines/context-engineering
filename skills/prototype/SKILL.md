---
name: prototype
description: "UI-first prototyping: pesquisa competidores, coleta código de referência (não screenshots), gera opções iterativas (3→1→3), constrói frontend shell com mocks. Após /discovery, antes de /delivery. Colaborativo."
when_to_use: "Use when an Issue has significant UI and the user wants to validate the design before building backend. Triggers: '/prototype #N', 'prototipar', 'monta o front', 'faz o protótipo', 'UI first', 'design primeiro', 'frontend shell'."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion, WebSearch, WebFetch, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__javascript_tool, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__tabs_context_mcp
argument-hint: "#issue-number"
model: sonnet
effort: high
---

# /prototype — UI-first: reference → options → shell

> Architecture reference: `ARCHITECTURE.md` § "Prototype — midstream"
> This skill is collaborative — the human picks, refines, and approves at every visual gate.

**Input:** `$ARGUMENTS` — GitHub Issue number (e.g., `#10`)

**Position in lifecycle:**
```
/discovery → Issue (spec)
  ↓
/prototype #N  ← this skill
  ↓
/delivery #N   (backend integration — trivial with approved frontend)
```

---

## Step 1 — Load context

Read the Issue spec:

```bash
gh issue view $ISSUE_NUMBER --json title,body,milestone,labels
```

If the Issue is not found or `gh` is not available: work with the spec provided inline by the user. Inform that GitHub sync (Step 8) will be skipped.

Parse:
- **Intent** — what the product does, who it's for
- **UX Flow** — screens, user decisions, states
- **Domain** — what space this product operates in

Read project context:
- `CLAUDE.md` — stack, conventions, canonical patterns
- If CLAUDE.md doesn't specify UI stack: check `package.json` to determine framework (Next.js, Vite, etc.) and CSS solution (Tailwind, CSS modules, styled-components) before proceeding.
- Existing UI code (if any) — to match patterns, component library, tokens

If the Issue lacks UX Flow: **abort**. Return:
> "Issue #N has no UX flow. Run `/discovery #N` to define it first."

## Step 2 — Map the space (sonnet subagent)

**Goal:** Understand who else operates in this space and what they look like.

Subagent receives: Issue intent + domain.

1. **Identify 5-8 competitors/players** in the same space via WebSearch
   - Direct competitors (same problem)
   - Adjacent players (similar UX patterns, different domain)
   - Aesthetic references (sites known for exceptional design in this category)

2. **For each, capture:**
   - URL
   - What they do (1 line)
   - Why they're relevant as reference (UX pattern? visual style? interaction model?)

**Return to parent:** ranked list of references with URLs and relevance notes.

## Step 3 — Harvest code references (sonnet subagents, parallel)

**Goal:** Collect actual code (HTML/CSS) from reference sites — not screenshots. Claude understands code far better than images.

Spawn 1 subagent per reference site (3-5 sites, parallel). Each subagent:

1. Navigate to the reference URL via `claude-in-chrome` or `WebFetch`
2. Extract the relevant sections:
   - Page structure (HTML skeleton)
   - Key component patterns (nav, cards, forms, CTAs)
   - Design tokens in use (colors, fonts, spacing — from computed styles or CSS)
   - Interaction patterns (hover states, transitions, animations)
3. Save extracted reference to project:
   ```
   .claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/references/
     {site-slug}.md
   ```
   Format:
   ```markdown
   # {Site Name} — Reference
   URL: {url}
   Relevance: {why this reference matters}

   ## Tokens extracted
   - Colors: {palette}
   - Typography: {fonts, sizes, weights}
   - Spacing: {scale}

   ## Key patterns
   {HTML/CSS snippets of relevant components}
   ```

**Return to parent:** summary of what was harvested (sites, tokens found, notable patterns).

**Also search for aesthetic/inspiration references:**
- Pinterest boards, Dribbble, Behance for the product category
- Design blogs with relevant case studies
- If a site blocks direct access (auth walls, anti-scraping): use WebSearch to find publicly shared examples (e.g., "dribbble {product-category} dashboard design") instead of retrying the blocked site.

## Step 4 — Define problems per screen (inline)

**Before designing anything, define what each screen solves.**

For each screen in the UX Flow:

1. **User problem:** What decision does the user need to make here?
2. **Information hierarchy:** What's most important → least important?
3. **Actions:** What can the user do? Primary vs secondary.
4. **Content:** Write plausible copy (not lorem ipsum) — realistic text that respects the actual product.

Present to the user for validation.

### Step 4 — Gate: problem definition ◀── GATE

Use AskUserQuestion:

> **Here's the problem definition for each screen. Does this make sense?**
>
> [screen-by-screen: problem, hierarchy, actions, sample copy]
>
> - **Looks good** — proceed to design options
> - **Adjust** — tell me what to change

## Step 5 — Generate 3 options with criteria

**Each option has explicit design intent — not "3 random variations".**

Define 3 criteria-driven directions. Examples:
- **Option A** — Maximum information density (power users, dashboard feel)
- **Option B** — Minimal/focused (consumer product, guided flow)
- **Option C** — Bold/editorial (brand-forward, storytelling layout)

The criteria come from: the product domain + the references harvested + the user problems defined.

For each option, implement as actual code:
- Working HTML/React with real component structure
- Styled with the project's detected stack (from Step 1)
- Using tokens/patterns extracted from references
- Plausible copy (from step 4), not lorem ipsum
- Responsive structure
- All data mocked but realistic

**Code organization:** create in a prototype directory:
```
prototype/
  option-a/
  option-b/
  option-c/
```

Or if using the project's component structure, create with a prototype prefix/flag.

### Step 5 — Gate: option selection ◀── GATE

Use AskUserQuestion:

> **3 options ready. Each takes a different approach:**
>
> - **Option A ({criteria}):** {1-line description of the visual approach}
> - **Option B ({criteria}):** {1-line description}
> - **Option C ({criteria}):** {1-line description}
>
> Start the dev server and review them in the browser.
>
> - **Pick one** — tell me which (A/B/C) and I'll generate 3 refinements
> - **None work** — tell me what's missing and I'll generate 3 new directions
> - **Mix** — "A's layout with C's typography" — I'll combine

## Step 6 — Refine (iterative loop)

User picks an option. Generate **3 sub-options** that refine the chosen direction:

- **Sub-A** — Conservative refinement (polish what's there)
- **Sub-B** — Push one element further (bolder colors, tighter spacing, different component)
- **Sub-C** — Rethink one aspect (different nav pattern, card layout, interaction)

### Step 6 — Gate: refinement ◀── GATE

Same pattern as step 5. User picks, loop continues until:
- User says "**this is it**" → proceed to step 7
- Max 3 refinement rounds (if still not converging, ask what's fundamentally off)

## Step 7 — Build the shell

Take the approved design and build the complete frontend shell:

1. **All screens** from the UX flow — implemented with the approved design direction
2. **All states** — loading, empty, error, success (from Issue spec)
3. **Navigation** — working routing between screens
4. **Responsive** — mobile + desktop
5. **Mocked data** — realistic but fake. Data layer clearly separated for easy backend integration.
6. **Interactions** — hover, transitions, animations that were in the approved design

Save as proper project code (not prototype directory). Clean up the prototype options directory.

### Step 7 — Gate: shell approval ◀── GATE

Use AskUserQuestion:

> **Frontend shell complete. All screens implemented with approved design.**
>
> Review in the browser:
> - All screens accessible via navigation
> - States: loading, empty, error, success
> - Responsive: resize to check mobile
>
> - **Approved** — ready for `/delivery #N` (backend integration)
> - **Needs changes** — tell me what to fix

## Step 8 — Handoff for delivery

Once the shell is approved:

1. Commit all changes to branch `agent/{N}-prototype-{issue-slug}`:
   ```bash
   git checkout -b agent/{N}-prototype-{issue-slug}
   git add -A && git commit -m "feat: frontend shell for #{N}"
   ```

2. If GitHub is available, comment on the Issue:
   ```bash
   gh issue comment $ISSUE_NUMBER --body "$(cat <<'EOF'
   ## Prototype — Approved

   **Design direction:** {chosen option + refinements applied}
   **References used:** {list of reference sites}
   **Screens:** {list of screens implemented}

   Frontend shell is in branch `agent/{N}-prototype-{issue-slug}`.
   Ready for /delivery #N (backend integration only).

   ---
   *Created via /prototype*
   EOF
   )"
   ```

3. Push the branch:
   ```bash
   git push -u origin agent/{N}-prototype-{issue-slug}
   ```

4. Report to user:
   > Shell approved and pushed. Run `/delivery #N` to integrate the backend.
   > The delivery agent will work on top of this branch — the frontend is the foundation, backend plugs in.

**No PR is opened here.** The prototype branch is the handoff artifact. `/delivery` opens the PR with the complete implementation (frontend + backend).

5. Clean up reference files (optional — keep if they're useful for delivery):
   ```
   .claude/state/milestones/{milestone-slug}/issue-{N}-{slug}/references/
   ```

---

## Rules

- **Code references > screenshots.** Always fetch actual HTML/CSS from reference sites. Claude understands code structure, not pixels.
- **Every option has explicit criteria.** Never "3 random variations". Each option represents a design thesis.
- **Plausible copy, never lorem ipsum.** If the product is a CRM, the placeholder says "Acme Corp — 3 deals in pipeline", not "Lorem ipsum dolor sit amet".
- **The user picks, Claude proposes.** This is collaborative — never skip a visual gate.
- **3 options → pick → 3 refinements.** This is the core loop. It replicates how designers work: diverge → converge → diverge → converge.
- **Frontend shell = complete UI with mocked data.** Not a wireframe. Not a partial. Every screen, every state, working navigation.
- **Backend is delivery's job.** The shell has a clear data layer boundary. `/delivery` plugs in the real backend.
- **Max 3 refinement rounds.** If not converging after 3 rounds, the problem definition (step 4) needs revisiting, not the design.
- **Fallback gracefully.** If a reference site blocks access, search for public examples instead of retrying. If GitHub is unavailable, work locally and skip sync steps.
