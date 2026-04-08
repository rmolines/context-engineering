# Context Engineering — Architecture

> CE is a context management layer for Claude Code. It configures and optimizes native context layers, and creates new ones — so every session starts with the right context.
> This document is the canonical reference. Skills, templates, and rules derive from it.

## Foundation: Claude Code context layers

CE doesn't replace Claude Code's context architecture — it manages it. Understanding what's native vs what CE adds is essential.

### Native layers (managed by CE)

| Native layer | Loaded when | What CE does with it |
|---|---|---|
| `CLAUDE.md` (project root) | Always-on, every session | `/init` generates fact-first template with Commander's Intent |
| `.claude/rules/` | Auto (no `paths:`) or lazy (with `paths:`) | `/init` installs session rules (session-cycle, standards, context-docs) |
| `MEMORY.md` (auto-memory) | Always-on, first 200 lines | `/persist` writes cross-session learnings |
| `SessionStart` hook | On session start, resume, compact | Post-compact recovery (re-injects state) |
| Skill descriptions | Always-on (~250 chars each) | Plugin manifest registers CE skills |
| Subdirectory `CLAUDE.md` | Lazy (when Claude accesses dir) | Not managed by CE |

### CE layers (created by CE)

| CE layer | Where | Purpose | Managed by |
|---|---|---|---|
| State directory | `.claude/state/milestones/` | Rich context per Issue (discovery, plan, execution log) | `/discovery`, `/delivery`, `/persist` |
| Domain map | `.claude/docs/index.md` | Project's technical landscape (APIs, auth, schema, patterns) | `/init` (generates), `/persist` (drift detection) |
| STATE.md | `.claude/state/STATE.md` | Live snapshot of GitHub Issues/Milestones (session buffer) | `/bootstrap` (generates fresh each session) |
| GitHub infra | Labels, Milestones, Projects V2 | Human world: request tracking, delivery validation | `/init` (configures) |

### The relationship

```
┌─ Claude Code native ─────────────────────────────────────┐
│  CLAUDE.md    Rules    Memory    Hooks    Skills/Plugins  │
├─ CE manages ─────────────────────────────────────────────┤
│  ↑ configures and optimizes native layers                │
│  + creates: domain map, state tracking, milestone docs   │
│  + connects: GitHub Issues/Milestones as human interface │
└──────────────────────────────────────────────────────────┘
```

## Philosophy

### Core principle

> "Find the smallest set of high-signal tokens that maximize the likelihood of the desired outcome."

Context is a finite resource. More tokens != better results. After ~70% window usage, precision degrades. After ~85%, hallucinations increase. The goal is not to load everything — it's to load the **right thing at the right time**.

### Fact-first paradigm

Research consistently shows:
- **>50% of effective agent context is domain facts**, not behavioral instructions
- **Code examples produce 5x improvement** over rules alone
- **Always-on context (100% pass rate) outperforms active retrieval (79%)** for critical knowledge

Most projects over-index on instructions ("how to behave") and under-index on facts ("what exists"). The right balance: **facts first, instructions as minimum necessary.**

| Facts (domain knowledge) | Instructions (behavioral) |
|---|---|
| POST /api/leads creates a lead with Bearer auth | Always use conventional commits |
| Auth uses JWT in cookies for web, API keys for agents | Run /persist before ending session |
| DB is Neon Postgres, schema in db-*.ts | Follow explore-plan-execute cycle |

**The test:** if Claude would build the wrong thing without this info, it's a fact. If Claude would build the right thing but in a non-preferred style, it's an instruction.

### Pointer > prose

When documenting something that exists in code, point to the file with a short annotation. The code is the single source of truth — prose duplicates and drifts.

```markdown
# Bad: prose (drifts, wastes tokens)
The leads API accepts POST with JSON body containing name, domain, segment...

# Good: pointer (zero drift, compact)
- [leads CRUD](src/app/api/leads/route.ts) — Bearer auth, Zod validation
```

### Canonical patterns

AI agents perform better when they can pattern-match against existing code. Instead of writing rules about how code should look, point to reference implementations:

```markdown
## Canonical patterns
- API route: src/app/api/leads/route.ts (auth, validation, response format)
- Server Action: src/app/actions/auth.ts (form action + Zod)
```

### The four strategies

| Strategy | What it means | Native mechanism | CE extension |
|---|---|---|---|
| **Write** | Persist state outside the window | MEMORY.md, CLAUDE.md | STATE.md, milestone docs, execution logs |
| **Select** | Retrieve only what's relevant | Subdirectory CLAUDE.md, `paths:` rules | `/bootstrap` deep loading, progressive disclosure |
| **Compress** | Summarize to save tokens | (manual) | Pointer > prose doctrine, domain map |
| **Isolate** | Separate concerns across agents | Subagent fresh windows | Validator subagent pattern, worktree isolation |

### CLAUDE.md budget

Target: <200 lines per file. Recommended allocation:

```
Identity & Direction     ~10 lines   (facts)
Canonical Patterns       ~8  lines   (facts)
Domain Map Pointer       ~2  lines   (fact)
Structure                ~10 lines   (facts)
Stack & Conventions      ~15 lines   (mixed)
Commands                 ~10 lines   (facts)
Context Discipline       ~5  lines   (instructions)
                        ─────────
Total                   ~60 lines    (~75% facts, ~25% instructions)
```

## Mental model: Context sources & routing

CE is a context router. It knows where each type of context lives and how to move it between sources and sessions. Skills are the routers.

### Context sources

| Source | What lives there | Loaded by |
|---|---|---|
| GitHub Issues | Specs, acceptance criteria | /bootstrap (GraphQL) |
| GitHub Issue comments | Session history, continuation context | /bootstrap (GraphQL) |
| GitHub Milestones | Goals, intent, signals | /bootstrap (gh api) |
| GitHub PRs | Delivery state, CI status | /bootstrap |
| Local: discovery.md | Deep research, alternatives, analysis | /bootstrap (per Issue) |
| Local: plan.md | Agent decomposition (ephemeral) | /delivery (temp only) |
| Local: domain map | Project technical landscape | Always-on pointer |
| Native: CLAUDE.md | Project identity, canonical patterns | Always-on |
| Native: rules/ | Behavioral constraints | Always-on |
| Native: memory/ | User preferences, feedback | Always-on (index) |
| Native: hooks/ | Lifecycle automation | Always-on |
| External: WebSearch | Live docs, API refs, changelogs | /delivery step 2.5 (grounding) |

### Routing criteria

Where does each type of context go?

| Criterion | → Source | Example |
|---|---|---|
| Navigability — humans browse it | GitHub | Issue specs, milestone goals |
| Durability — survives sessions | GitHub (permanent) or local (archive) | Session comments, discovery.md |
| Verbosity — too detailed for GitHub | Local disk | discovery.md (full research), plan.md |
| Frequency — loaded every session | Native Claude Code | CLAUDE.md, rules, memory |
| Ephemerality — only this session | In-context only | Plan deliverables (D1, D2, D3) |

### Skills as routers

| Skill | Direction | What it does |
|---|---|---|
| /bootstrap | Sources → Session | Reads GitHub + local, assembles briefing |
| /persist | Session → Sources | Routes learnings to correct source |
| /discovery | Intent → GitHub Issue | Creates self-sufficient spec |
| /delivery | GitHub Issue → PR | Consumes spec, produces delivery |

### Draft convention

An Issue without `## Acceptance Criteria` is a draft. Bootstrap classifies it as "needs discovery". Lifecycle: draft → `/discovery #N` → spec → `/delivery #N` → PR → done. Creating a draft is frictionless: tell the agent "note that we need X" and it creates a minimal Issue in [Backlog].

### Handoff artifact: the Issue

The Issue is the context contract between discovery and delivery. It's the output of discovery (human + Claude) and the input of delivery (Claude alone). An Issue must be **self-sufficient**: everything the delivery agent needs must be there.

### Delivery artifact: the PR

The PR is the delivery back to the stakeholder. It contains code + a validation report that maps what was built against what was requested.

## Nomenclature

Aligned with GitHub's official terminology:

| Concept | GitHub term | CE usage |
|---|---|---|
| Goal/objective | **Milestone** | Groups related Issues. Description carries intent, success state, signals |
| Request/task | **Issue** | Spec from discovery: intent, UX flow, acceptance criteria |
| Quick capture | **Draft Issue** | Issue without ## Acceptance Criteria. Bootstrap classifies as "needs discovery". Lifecycle: draft → /discovery #N → spec → /delivery → done. |
| Delivery | **Pull Request** | Code + validation report, closes the Issue |
| Visual overview | **Project** (Board/Table/Roadmap) | 1 Project per repo |
| Internal decomposition | — | Plan file: batches, deps, git strategy (agent only) |

### What does NOT go to GitHub

- Deliverables (D1, D2, D3) — internal agent decomposition
- Plan files — execution orchestration
- Execution logs — troubleshooting history
- Domain maps — agent context

These are either ephemeral (D1/D2/D3) or too verbose for GitHub (plan files, execution logs) — routed to local disk by the verbosity criterion.

## Core skills

Three categories: **infra** (project setup), **context** (session memory), and **work** (upstream + downstream):

| Skill | Category | Who | Model | Effort |
|---|---|---|---|---|
| `/init` | Infra | Agent | sonnet | medium |
| `/bootstrap` | Context in | Agent | haiku | low |
| `/persist` | Context out | Agent | haiku | low |
| `/discovery` | Upstream (problem -> spec) | Human + Claude | inherited | -- |
| `/delivery` | Downstream (spec -> code) | Claude alone | sonnet | high |
| `/distill` | Meta (workflow -> skill) | Human + Claude | inherited | -- |

### Init — project setup

Configures CE in a project. Runs once (or to check health). Manages both native Claude Code layers and CE layers.

```
/init
  ├── diagnose all layers (native + CE)
  ├── report health (checkmarks)
  ├── propose fixes (with confirmation)
  └── execute: CLAUDE.md, domain map, dirs, GitHub, CI
```

### Bootstrap — context in

Loads session context. Runs at start of each session. Query live, never cache.

```
/bootstrap
  ├── detect GitHub mode + check /init ran
  ├── live sync (gh issue list, STATE.md buffer, issue dirs, milestone sync)
  ├── deep context loading (milestone docs, issue docs, continuation)
  └── briefing + align (standup format, propose action)
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
  ├── 1. Understand intent (PM role)
  ├── 2. Research: internal (codebase) + external (docs, APIs)
  ├── 3. Propose experience (Designer role)
  ├── 4. Validate with you <-- GATE
  ├── 5. Technical spec (Tech Lead role)
  └── 6. Create Issue in GitHub
```

### Delivery — downstream

Autonomous. Claude picks up an Issue and delivers a PR.

```
/delivery #10
  ├── 1. Research (sonnet subagent)
  ├── 1.5. Ground (sonnet subagent + WebSearch — skipped for pure internal work)
  │     --> Grounding gate (if critical premise invalidated)
  ├── 2. Decompose (internal plan)
  ├── 3. Implement (subagents per deliverable)
  │     --> Architectural gate (if irreversible decision)
  ├── 4. Validate (sonnet subagent -- isolated)
  │     --> Failure gate (if validation fails)
  └── 5. Deliver (PR with validation + grounding report)
```

**Checkpoint types:**

| Type | When | Blocks? |
|---|---|---|
| Notification | Decomposition done | No |
| Grounding gate | Critical external premise invalidated | Yes |
| Architectural gate | New structure, public API change | Yes |
| Failure gate | Validation failed, CI failed | Yes |

## Operational doctrine

### Three levels (NATO-inspired)

| Level | Artifact | Cadence (write) | Cadence (read) | Mechanism |
|---|---|---|---|---|
| Strategic | `CLAUDE.md` Commander's Intent | Rare (milestone/pivot) | Always-on | `/bootstrap` suggests review |
| Operational | GitHub Milestone description | Per session (signals) | `/bootstrap` + `/persist` | Backbrief + SITREP |
| Tactical | Plan files, execution logs | Per session | `/delivery` + `/bootstrap` | Checkpoint after each batch |

### Commander's Intent

The military concept: communicate the desired end state, not the steps. In CE, `## Commander's Intent` in CLAUDE.md is always-on — every session, every agent sees it. 5-8 lines of product thesis.

### Backbrief and SITREP

Backbrief (in /bootstrap): subordinate repeats intent to commander for confirmation. SITREP (in /persist): situation report — updates signals, detects emergent strategy, suggests review when divergence accumulates.

### Emergent strategy detection

When sessions consistently perform work outside any Milestone, that signals emergent strategy. The system records it and suggests review. Milestones can be created, adjusted, or cancelled based on accumulated signals.

## Context layers — always-on vs progressive disclosure

### Always-on (~200 lines budget)

Auto-loaded at session start. Informs **every** decision.

| Layer | Mechanism | Native? | Content type |
|---|---|---|---|
| Project identity | CLAUDE.md root | Native | fact |
| Direction | CLAUDE.md Commander's Intent | Native | fact |
| Domain map pointer | CLAUDE.md (1-2 lines) | Native | fact |
| Canonical patterns | CLAUDE.md (5-8 lines) | Native | fact |
| Conventions | CLAUDE.md (~15 lines) | Native | mixed |
| Current state | STATE.md (via /bootstrap) | CE layer | fact |
| Process guardrails | `.claude/rules/` (~30 lines) | Native | instruction |
| User profile | MEMORY.md index | Native | fact |

**Note the balance:** ~70% facts, ~30% instructions.

### Progressive disclosure

Loaded on demand. If Claude would only err on **detail** without it, it's disclosure.

| Content | Where | When to load |
|---|---|---|
| Domain knowledge (full) | `.claude/docs/index.md` | Operating on APIs, auth, data |
| Milestone details | GitHub Milestone description (via gh api) | Working on specific Milestone |
| Issue context | `.claude/state/milestones/*/issue-*/` | Working on specific Issue |
| Execution history | `execution-log.md` | Resuming prior work |
| Research | `research/` | Needing prior research |

**The connecting mechanism is the pointer.** Always-on context contains summaries + links. Claude sees the map, reads the detail when acting.

### Post-compaction recovery

When Claude compacts conversation history (at ~83.5% context usage), CLAUDE.md survives (re-read from disk) but conversation details are lost. A SessionStart hook with `compact` matcher re-injects STATE.md content and domain map pointer.

## Disk structure

Mirrors GitHub hierarchy. Everything is permanent (historical archive + operational context).

```
.claude/
├── state/
│   ├── STATE.md                              # Session buffer (generated by /bootstrap)
│   ├── milestones/                           # 1 dir per Milestone
│   │   ├── c1-dogfooding/
│   │   │   ├── issue-10-refresh-tokens/
│   │   │   │   ├── discovery.md              # research, decisions, UX flow, context
│   │   │   │   ├── plan.md                   # decomposition, batches, git strategy
│   │   │   │   ├── execution-log.md          # execution history + decision markers (DECISION/DECISION-FAILED/DECISION-OVERRIDDEN)
│   │   │   │   └── execution-state.json     # checkpoint state (batch progress, plan hash) — deleted after PR
│   │   │   └── issue-12-dark-mode/
│   │   │       └── ...
│   │   └── c3-validacao-externa/
│   └── project-cache.json                    # Project V2 field/option IDs
├── docs/
│   └── index.md                              # domain map (APIs, auth, schema, patterns)
└── memory/
    └── MEMORY.md                             # cross-session learnings (native auto-memory)
```

### Linking conventions

Every local doc includes a header linking to GitHub:

```markdown
<!-- Issue: #10 | Milestone: [C1] Dogfooding | PR: #15 -->
```

Every Issue in GitHub is self-sufficient. Local files are the agent's extended memory, not the source of truth for specs.

### GitHub detection layers

| Layer | Condition | Capability |
|---|---|---|
| `GITHUB_MODE=false` | No remote or gh not authenticated | Local only |
| `GITHUB_MODE=true` | Remote + gh auth OK | Issues, Milestones, Labels, PRs |
| `PROJECTS_MODE=true` | + `project` scope in gh auth | Project V2 board with custom fields |

Degradation is always silent. No GitHub = local operation, no errors.

## GitHub Project configuration

1 Project per repo, named `"CE: {repo-name}"`.

**Fields:** Status (built-in), Priority, Size, Start Date, Target Date.

**Views:** Board (by Status), Roadmap (Start/Target Date), By Milestone (table).

**Automations:** Item added -> Todo, Issue closed -> Done, PR merged -> Done, Auto-archive after 14 days.

## Subagent model

The more expensive the model, the more it orchestrates and less it executes.

| Work type | Tier |
|---|---|
| Conversation with human, synthesis, decisions | Opus or Sonnet (inherited) |
| Implementation, technical reasoning | Sonnet |
| Mechanical: template, extraction, grep, formatting | Haiku |
| Grounding (premise verification + WebSearch) | Sonnet (receives research output + spec only) |
| Validation (requires judgment) | Sonnet (isolated, no implementation context) |

The validator subagent is always isolated — receives only the Issue spec and git diff.

## Skill lifecycle

```
/init (once) → set up CE layers in the project
  ↓
/bootstrap (each session) → load context, align
  ↓
/discovery → research + spec into Issue (optional)
  ↓
/delivery #N → implement Issue → PR
  ↓
/persist → save state + signals + detect drift
```

Skills are progressive disclosure — only the description (~250 chars) loads until invoked. Full content loads on demand.

## End-to-end flow

```
 You (stakeholder)          Claude (squad)              GitHub
 ─────────────────          ──────────────              ──────
                            /init (first time)
                              sets up CE layers
                              configures GitHub ────────► Labels, Milestones

                            /bootstrap
                              loads context ◄──────── Issues, Milestones
                              "what are we doing?"

 "quero X" ──────────────► /discovery
                              understands intent
                              researches
                              proposes UX flow
 "looks good" ◄──────────── validates with you
                              writes technical spec
                              creates Issue ─────────► Issue #10 (spec)

                            /delivery #10
                              reads Issue ◄──────────── Issue #10
                              researches (subagent)
                              grounds premises ◄──── WebSearch (docs, APIs)
                              decomposes (internal plan)
                              implements (subagents)
                              validates (isolated)
                              opens PR ──────────────► PR #15 (code + reports)
                              CI passes ─────────────► auto-merge
                              Issue closes ──────────► #10 Done

                            /persist
                              saves signals, memory
                              appends signal to GitHub Milestone description
                              sync to GitHub ─────────► Milestone description

 checks board ◄──────────────────────────────────────── Project board updated
```

## Constraints and anti-patterns

### Key constraints

- **CLAUDE.md target**: <200 lines per file for max adherence
- **Fact-first ratio**: ~70% facts, ~30% instructions in always-on context
- **Auto-compact trigger**: ~83.5% of context window
- **"Lost in the middle"**: critical info at start or end, never buried
- **Hook compliance**: 100% deterministic. Rule compliance: ~70%. Prefer hooks for critical behaviors
- **Always-on > retrieval**: 100% vs 79% pass rate for critical knowledge
- **Subagent isolation**: fresh 200K window, only final output returns
- **Skill injection**: only description in context until invoked
- **Code examples > rules**: 5x improvement when AI can pattern-match

### Anti-patterns

| Anti-pattern | Why it's bad | Do instead |
|---|---|---|
| @importing 200+ line docs | Eats budget every session | 5-8 line summary + pointer |
| Duplicate sources of truth | Conflicting state | One canonical location per info type |
| Prose describing code | Drifts immediately | Pointer to file + 3-5 word annotation |
| All instructions, no facts | Knows behavior not domain | Fact-first: domain knowledge before rules |
| Putting everything in CLAUDE.md | Exceeds 200-line target | Split: CLAUDE.md (stable) / STATE.md (dynamic) / docs (domain) |
| Saving code patterns to memory | Stale fast | Only save non-obvious decisions and rationale |
| Rules instead of examples | Ambiguous | Canonical patterns with file pointers |
