# LLM-Maintained Knowledge Base Pattern

> Source: Andrej Karpathy, "LLM Knowledge Bases" (April 2026)
> Analysis date: 2026-04-03

## The Pattern

LLMs as **authors** of structured knowledge bases, not just consumers. The human curates sources and asks questions; the LLM compiles, organizes, links, and maintains.

```
raw sources → LLM compiler → structured wiki (.md) → LLM Q&A → outputs → (loop back into wiki)
```

### Key components

| Component | What it does |
|-----------|-------------|
| **Ingest** | Raw docs indexed into `raw/`, LLM "compiles" into .md wiki |
| **Auto-index** | LLM maintains index files + summaries (no fancy RAG needed at ~400K words) |
| **Cumulative loop** | Query outputs get filed back into wiki, enriching future queries |
| **Linting** | LLM health checks: inconsistencies, missing data, new connections |
| **Tools** | Custom CLIs (search, viz) exposed to LLM as tools |

### Karpathy's key insight

> "I thought I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining index files and brief summaries"

At the scale of ~100 articles / ~400K words, lightweight index files + summaries are sufficient for LLM navigation. This validates the "pointer > prose" principle.

## Connection to Context Engineering

The pattern maps directly to CE's session protocol:

| Karpathy's wiki | Context Engineering |
|-----------------|-------------------|
| Index files + summaries | `STATE.md` + `MEMORY.md` (lightweight pointers) |
| LLM compiles raw → wiki | `/distill` crystallizes sessions into skills/state |
| Queries enrich wiki | `/persist` updates signals from session work |
| Health check linting | **Not yet implemented** — see below |
| ~400K words navigable | ~200 lines always-on budget + on-demand deep reads |

### The cumulative loop

Both systems share the same flywheel: **usage generates context that improves future usage**.

- CE: `/discover` → work → `/persist` → next session's `/bootstrap` is richer
- Karpathy: query → output → file into wiki → next query has more to work with

### Where CE goes further

CE applies **proactive injection** — the system loads the right context before the LLM needs it. Karpathy's system is **reactive** — the LLM searches when asked. The difference: "the LLM knows how to find it" vs "the LLM already has it".

## The Linting Pattern (unexplored in CE)

Karpathy runs LLM "health checks" over the wiki:
- Find inconsistent data across articles
- Impute missing data (with web search)
- Discover connections between concepts for new article candidates
- Incrementally improve data integrity

This is the most valuable unexplored pattern for CE. Applied to a project's context layer:

- Detect stale state (campaigns with no signals for N sessions)
- Find orphaned plans (completed but not reflected in STATE.md)
- Identify missing context (code patterns not documented in CLAUDE.md)
- Suggest new campaigns from recurring session patterns

See: [CE backlog — context linting](../campaigns.md)

## Connection to Prometheus (Pantheon OS)

The architecture is isomorphic:

```
Karpathy:    raw/ sources → LLM compiler  → wiki     → LLM Q&A       → outputs
Prometheus:  firm sources → orchestrator  → context  → specialist agents → outputs
```

Prometheus is this pattern applied to investment banking workflows. The "heartbeat pattern" (proactive agents) is the production version of Karpathy's linting — but applied to deal flow:

- "Deal X has teaser but no financial model — Hefesto can generate?"
- "Investor Y replied 3 emails but isn't in pipeline — Hermes suggests adding?"
- "DD memo for deal Z contradicts dataroom on Q3 revenue"

The moat in both cases is the **accumulated context**, not the model or the tools.
