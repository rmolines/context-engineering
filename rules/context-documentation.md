# Context Documentation — how to document and consume project context

## 1. Facts > instructions

When documenting a project (CLAUDE.md, standards, docs), prioritize concrete domain facts over behavioral instructions.

Facts: endpoints, schema, auth flows, env vars, existing patterns, what the product exposes.
Instructions: how to behave, which style to follow, which process to use.

The context budget (~200 lines always-on) should be mostly facts. Instructions are the minimum necessary to not break the process.

**Test:** if Claude would build the wrong thing without this info, it's a fact that belongs in context. If it would build the right thing but in a non-preferred style, it's an instruction.

## 2. Pointer > prose

When documenting something that exists in code, point to the file with a 3-5 word annotation. Don't duplicate in prose.

```
# ✗ Prose (drifts, wastes tokens)
The leads API accepts POST requests with a JSON body containing name, domain, segment...

# ✓ Pointer (zero drift, compact)
- [leads CRUD](src/app/api/leads/route.ts) — Bearer auth, Zod validation
```

Code is the source of truth. Prose duplicates and diverges. Pointers maintain a single source.

## 3. Canonical patterns

When creating something new in a project, find and replicate existing patterns before inventing.

Before implementing: ask "which existing file is the canonical reference for this?" and read that file first. Replicate the pattern (auth, error handling, response format, naming) instead of inventing ad-hoc.

If the project's CLAUDE.md lists canonical patterns — use them. If not — identify the best existing example and follow it.
