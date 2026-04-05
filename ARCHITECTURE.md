# Context Engineering — Architecture v2

> Two worlds, one system: human intent flows through GitHub, agent execution flows through local state.
> This document is the canonical architecture reference. Skills, templates, and rules derive from it.

## Mental model: Two worlds

The system serves two audiences with different needs:

| | Human world | Agent world |
|---|---|---|
| **Where** | GitHub (Issues, PRs, Milestones, Project) | Local disk (`.claude/state/`, `.claude/docs/`) |
| **Purpose** | Request, track, validate | Decompose, execute, remember |
| **Language** | Intent, behavior, acceptance criteria | Batches, deps, git strategy, files |
| **Audience** | Stakeholder (you) | Claude agents across sessions |
| **Nature** | Permanent record | Operational context + historical archive |

The human is a **stakeholder**, not a PM. Requests arrive rough — "quero refresh tokens", "tá lento". Claude absorbs PM + Designer + Tech Lead + Dev + QA roles.

### Handoff artifact: the Issue

The Issue is the contract between worlds. It's the output of discovery (human + Claude) and the input of delivery (Claude alone). An Issue must be **self-sufficient**: everything the delivery agent needs must be there.

### Delivery artifact: the PR

The PR is the delivery back to the human. It contains code + a validation report that maps what was built against what was requested.

## Nomenclature

Aligned with GitHub's official terminology:

| Concept | GitHub term | CE usage |
|---|---|---|
| Goal/objective | **Milestone** | Groups related Issues. Description carries intent, success state, signals |
| Request/task | **Issue** | Spec from discovery: intent, UX flow, acceptance criteria |
| Quick capture | **Draft Issue** | Backlog idea that lives only in the Project, no repo yet |
| Delivery | **Pull Request** | Code + validation report, closes the Issue |
| Visual overview | **Project** (Board/Table/Roadmap layouts) | 1 Project per repo, views for perspectives |
| Category | **Label** | Classification (priority, type, area) |
| Sprint/cycle | **Iteration** (field) | Optional time-boxed work periods |
| Internal decomposition | — (no GitHub equivalent) | Plan file: batches, deps, git strategy (agent only) |

### What does NOT go to GitHub

- Deliverables (D1, D2, D3) — internal agent decomposition
- Plan files — execution orchestration
- Execution logs — troubleshooting history
- Domain maps — agent context

These live on disk as the agent's operational memory and historical archive.

## Core skills

Two for **context management** (cross-session memory), two for **work** (upstream + downstream):

| Skill | Domain | Who | Model | Effort |
|---|---|---|---|---|
| `/bootstrap` | Context in | Agent | haiku | low |
| `/persist` | Context out | Agent | haiku | low |
| `/discovery` | Upstream (problem → spec) | Human + Claude | inherited | — |
| `/delivery` | Downstream (spec → code) | Claude alone | sonnet | high |

### Bootstrap — context in

Loads project state, detects new Issues from GitHub, aligns session. Idempotent.

```
/bootstrap
  ├── detect GitHub mode (issues/milestones/project)
  ├── rebuild STATE.md from GitHub
  ├── sync milestone descriptions ↔ local milestone docs
  ├── detect stale issues (30+ days)
  ├── report changes since last session
  └── ask: "what are we doing this session?"
```

### Persist — context out

Saves session learnings. Signals, memory, domain drift detection.

```
/persist
  ├── triage: what changed this session?
  ├── milestone signals (append to milestone doc + GitHub description)
  ├── memory updates (preferences, decisions, references)
  ├── domain drift detection (API/auth/schema changes vs domain map)
  └── continuation prompt for next session
```

### Discovery — upstream

Collaborative. You + Claude explore the problem, research, define the solution. Output: Issue in GitHub.

```
/discovery "rough request"
  │
  ├── 1. Understand intent (PM role)
  │     Parse rough request, ask clarifying questions
  │     Research: internal (codebase, decisions) + external (docs, APIs, state of art)
  │
  ├── 2. Propose experience (Designer role)
  │     User flow: what the end user sees/does
  │     States: loading, empty, error, success
  │     Edge cases, consistency with existing patterns
  │     Reference: design system blocks if available
  │
  ├── 3. Validate with you ◀── GATE
  │     "Here's the proposed flow. Does this make sense?"
  │     You approve, adjust, or reject
  │
  ├── 4. Technical spec (Tech Lead role)
  │     Translate approved UX into implementable spec
  │     Research: internal (canonical patterns, deps) + external (lib docs, examples)
  │
  └── 5. Output: Issue in GitHub
        - Intent (what and why, stakeholder language)
        - UX flow (approved in step 3)
        - Technical spec (from step 4)
        - Acceptance criteria (verifiable checklist)
        - Design notes (states, edge cases, consistency)
        - Research context (links, decisions, trade-offs)
```

**Complexity tiers:**

| Complexity | Orchestrator | Subagents |
|---|---|---|
| Simple (bug, config tweak) | Inline | None — quick research, create Issue |
| Medium (new feature, clear scope) | Inline | Haiku: internal research. Sonnet: external research |
| Complex (architecture, multi-system) | Inline | Sonnet: deep internal research. Sonnet: external research. Haiku: extract data/patterns |

### Delivery — downstream

Autonomous. Claude picks up an Issue and delivers a PR. Runs in `context: fork`.

```
/delivery #10
  │
  ├── 1. Research (sonnet subagent)
  │     Read Issue spec, relevant code, external docs
  │     Return: technical context + risks
  │     ──▶ Notification checkpoint: "Approaching #10 as X in N parts"
  │
  ├── 2. Decompose (inline)
  │     Create internal plan (batches, deps, git strategy)
  │     This is agent infrastructure, not human-facing
  │
  ├── 3. Implement (subagents per deliverable)
  │     │
  │     ├── Simple deliverable → haiku subagent
  │     │   (config, rename, boilerplate, unit tests)
  │     │
  │     ├── Medium deliverable → sonnet subagent
  │     │   (new feature, refactor, integration)
  │     │
  │     └── Parallel deliverables → worktree isolation
  │
  │     ──▶ Architectural gate (if: new DB table, public API change, interface refactor)
  │         "Created this structure. OK to proceed?"
  │
  ├── 4. Validate (sonnet subagent — isolated)
  │     Receives ONLY: Issue #10 spec + git diff
  │     Does NOT inherit implementation context
  │     Returns: validation report (criteria × evidence)
  │     ──▶ Failure gate (if validation fails)
  │         "Criterion X not met. Fix or accept?"
  │
  └── 5. Deliver (inline)
        PR with validation report in body
        References: Closes #10
        CI runs as quality gate
```

**Checkpoint types:**

| Type | When | Blocks? |
|---|---|---|
| Notification | Decomposition done, shows approach | No — continues automatically |
| Architectural gate | New structure, public API change, irreversible decision | Yes — waits for approval |
| Failure gate | Validation failed, CI failed, blocker found | Yes — waits for decision |

## Disk structure

Mirrors GitHub hierarchy. Everything is permanent (historical archive + operational context).

```
.claude/
├── state/
│   ├── STATE.md                              # GitHub cache (regenerated by /bootstrap)
│   ├── milestones/                           # 1 dir per Milestone
│   │   ├── c1-dogfooding/
│   │   │   ├── milestone.md                  # intent, success state, signals, review log
│   │   │   ├── issue-10-refresh-tokens/
│   │   │   │   ├── discovery.md              # research, decisions, UX flow, context
│   │   │   │   ├── plan.md                   # decomposition, batches, git strategy
│   │   │   │   └── execution-log.md          # what happened, problems, solutions
│   │   │   └── issue-12-dark-mode/
│   │   │       ├── discovery.md
│   │   │       ├── plan.md
│   │   │       └── execution-log.md
│   │   └── c3-validacao-externa/
│   │       └── milestone.md
│   ├── backlog/                              # Issues/drafts without Milestone
│   │   └── issue-4-context-linting.md
│   └── project-cache.json                    # Project V2 field/option IDs
├── docs/
│   └── index.md                              # domain map (APIs, auth, schema, patterns)
└── memory/
    └── MEMORY.md                             # cross-session learnings
```

### Linking conventions

Every local doc includes a header linking to GitHub:

```markdown
<!-- Issue: #10 | Milestone: [C1] Dogfooding | PR: #15 -->
```

Every Issue in GitHub is self-sufficient (doesn't require reading local files). Local files are the agent's extended memory, not the source of truth for specs.

### GitHub detection layers

| Layer | Condition | Capability |
|---|---|---|
| `GITHUB_MODE=false` | No remote or gh not authenticated | Local only (`.claude/state/`) |
| `GITHUB_MODE=true` | Remote + gh auth OK | Issues, Milestones, Labels, PRs |
| `PROJECTS_MODE=true` | + `project` scope in gh auth | Project V2 board with custom fields |

Degradation is always silent. No GitHub = local operation, no errors.

## GitHub Project configuration

1 Project per repo, named `"CE: {repo-name}"`.

**Fields:**

| Field | Type | Purpose |
|---|---|---|
| Status | Single select (built-in) | Todo → In Progress → Done |
| Priority | Single select | Urgent, High, Normal, Low |
| Size | Single select | S, M, L (stakeholder estimate) |
| Iteration | Iteration field | Optional: time-boxed cycles |
| Start Date | Date | Roadmap positioning |
| Target Date | Date | Roadmap positioning |

**Views:**

| View | Layout | Purpose |
|---|---|---|
| Board | Board (by Status) | Day-to-day work tracking |
| Roadmap | Roadmap (Start/Target Date) | Timeline overview |
| By Milestone | Table (grouped by Milestone) | Campaign progress |

**Automations:**

| Workflow | Action |
|---|---|
| Item added | Status → Todo |
| Issue closed | Status → Done |
| PR merged | Status → Done |
| Auto-archive | Archive Done items after 14 days |

Milestone appears as marker in Roadmap view (native GitHub feature).

## Subagent model

Principle: the more expensive the model, the more it orchestrates and less it executes.

| Work type | Tier |
|---|---|
| Conversation with human, synthesis, decisions | Opus or Sonnet (inherited) |
| Implementation, technical reasoning | Sonnet |
| Mechanical: template, extraction, grep, formatting | Haiku |
| Validation (requires judgment) | Sonnet (isolated, no implementation context) |

The validator subagent is always isolated — it never inherits context from the implementer. It receives only the Issue spec and the git diff.

## End-to-end flow

```
 You (stakeholder)          Claude (squad)              GitHub
 ─────────────────          ──────────────              ──────
                            /bootstrap
                              loads context ◄──────── Issues, Milestones
                              "what are we doing?"

 "quero X" ──────────────►  /discovery
                              understands intent
                              researches (internal + external)
                              proposes UX flow
 "looks good" ◄────────────  validates with you
                              writes technical spec
                              creates Issue ─────────► Issue #10 (spec)

                            /delivery #10
                              reads Issue ◄──────────── Issue #10
                              decomposes (internal plan)
                              implements (subagents)
                              validates (isolated subagent)
                              opens PR ──────────────► PR #15 (code + report)
                              CI passes ─────────────► auto-merge
                              Issue closes ──────────► #10 Done

                            /persist
                              saves signals, memory
                              updates milestone doc
                              sync to GitHub ─────────► Milestone description

 checks board ◄──────────────────────────────────────── Project board updated
```
