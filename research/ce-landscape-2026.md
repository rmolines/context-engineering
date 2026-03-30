# Context Engineering Landscape — March 2026

> Research consolidation: patterns, tools, and evidence for evolving AI coding assistant context systems.

## Key Findings

### 1. Facts > Instructions
The Codified Context paper (arxiv 2602.20478, 283 sessions, 108k LOC C# system) found that >50% of effective content in agent specifications is concrete domain knowledge (endpoints, failure modes, code patterns), not behavioral instructions. AI agents perform significantly better when given facts about the domain than rules about how to behave.

**Source:** https://arxiv.org/abs/2602.20478

### 2. Always-On Context Outperforms Active Retrieval
Vercel's internal evals showed AGENTS.md (compressed 8KB index always in context) achieved 100% pass rate, while skills-based retrieval (progressive disclosure) maxed at 79%. Without explicit instruction to use skills, they performed no better than having no documentation at all.

**Implication:** Critical domain knowledge must be always-on, not behind a retrieval step. Skills work for detailed how-to, but the map of "what exists" must be upfront.

**Source:** https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals

### 3. Code Examples > Written Rules (5x improvement)
The ReadMe.LLM paper (arxiv 2504.09798) measured: rules alone ~30% accuracy, function signatures + examples 64%, rules + functions + examples 88-100%. LLMs are pattern matchers — showing canonical code from the project is more effective than describing conventions in prose.

**Source:** https://arxiv.org/abs/2504.09798

### 4. Single-File Manifests Don't Scale
Both the Codified Context paper and InfoQ analysis (March 2026) conclude that single-file approaches (CLAUDE.md, AGENTS.md) break down beyond modest codebases. The solution is layered: compact always-on constitution + domain-expert agents/docs + cold-memory knowledge base.

**Sources:**
- https://arxiv.org/abs/2602.20478
- https://www.infoq.com/news/2026/03/agents-context-file-value-review/

### 5. Post-Compaction Context Recovery
Pattern emerging in early 2026: SessionStart hooks with `compact` matcher re-inject essential context after Claude compacts conversation history. Solves "post-compaction rule amnesia" in long sessions. Context buffer reduced to ~33K tokens (16.5% of total context).

**Source:** https://medium.com/@porter.nicholas/claude-code-post-compaction-hooks-for-context-renewal-7b616dcaa204

### 6. AGENTS.md Impact Data
Presence of AGENTS.md associated with 29% reduction in median runtime and 17% reduction in output token consumption (arxiv 2601.20404). 60k+ projects adopted. Now under Linux Foundation as open standard.

**Sources:**
- https://arxiv.org/html/2601.20404v1
- https://agents.md/

## Landscape: Tools & Approaches

### Knowledge Graphs for Code

| Tool | Mechanism | Trade-offs |
|------|-----------|------------|
| **Potpie AI** | Ingests repo → Neo4j graph of functions, classes, deps. RAG agent queries graph. | Deep understanding but cloud-based, external dependency |
| **GitLab Knowledge Graph** | CLI parses repo locally → graph DB exposed via MCP. Local-first. | Tied to GitLab ecosystem |
| **CodeGraphContext** | Open-source MCP server + CLI. AST analysis → graph DB. | Lightweight, MCP-native |

### Auto-Generated Documentation

| Tool | Mechanism | Trade-offs |
|------|-----------|------------|
| **RepoAgent** (OpenBMB) | Topological-order doc generation + pre-commit hook updates | Living docs via git hooks, but LLM cost per commit |
| **CodeWiki** (FSoft) | Hierarchical decomposition + multi-agent + multi-modal. 68.79% quality. | Batch process, large output |
| **DocAgent** (Meta) | 5 specialized agents: Reader, Searcher, Writer, Verifier, Orchestrator | Factually correct by design, complex pipeline |

### Directory-as-Documentation Standards

| Standard | Mechanism | Adoption |
|----------|-----------|----------|
| **AGENTS.md** | Markdown at root + subdirs, cascading like .gitignore | 60k+ repos, Linux Foundation |
| **Codebase Context Spec** | `.context/` dir with `index.md` + YAML frontmatter | Low adoption, rich format |
| **VS Code/Copilot** | PRODUCT.md + ARCHITECTURE.md + CONTRIBUTING.md trilogy | Official Microsoft guidance |

### Context Injection Strategies

| Strategy | When | How |
|----------|------|-----|
| **CLAUDE.md cascade** | Every session | Auto-loaded, hierarchical |
| **SessionStart hooks** | Session start/resume/compact | Script stdout → system message |
| **PreToolUse/PostToolUse hooks** | Before/after tool calls | Pattern matching → skill injection |
| **MCP servers** | On demand | External knowledge exposed as tools/resources |
| **Post-compaction hooks** | After context compaction | Re-inject essential pointers |

### MCP Knowledge Layer Servers

| Server | Focus |
|--------|-------|
| **mcp-knowledge-graph** | Entities + Relations + Observations |
| **MemoryGraph** | Graph DB for coding agent patterns |
| **Zep Knowledge Graph** | Temporal knowledge graphs |
| **NeoCoder** | Neo4j as dynamic instruction manual |

## Applicable Patterns (for our CE system)

### Immediate (low effort, high impact)
1. **Post-compaction hook** — re-inject STATE.md pointers after compaction
2. **Canonical patterns in CLAUDE.md** — point to reference files, not rules
3. **Domain map (.claude/docs/)** — structured pointers to code, not prose
4. **Rule: facts > instructions** — global rule for any project

### Near-term (medium effort)
5. **Bootstrap scan** — auto-generate domain map from code analysis
6. **Drift detection in /persist** — alert when code changes but docs don't
7. **Domain-expert skills** — skills with pre-loaded domain facts (Tier 2 pattern)

### Future (high effort, exploratory)
8. **MCP knowledge graph** — local graph DB exposed via MCP
9. **Pre-commit doc regeneration** — RepoAgent-style living docs
10. **Codebase graph analysis** — AST-based dependency mapping

## References

- Codified Context paper: https://arxiv.org/abs/2602.20478
- Codified Context implementation: https://github.com/arisvas4/codified-context-infrastructure
- AGENTS.md spec: https://agents.md/
- AGENTS.md impact study: https://arxiv.org/html/2601.20404v1
- AGENTS.md lessons from 2500 repos: https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/
- Vercel AGENTS.md vs Skills eval: https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
- Vercel Plugin for Claude Code: https://vercel.com/docs/agent-resources/vercel-plugin
- ReadMe.LLM paper: https://arxiv.org/abs/2504.09798
- RepoAgent: https://github.com/OpenBMB/RepoAgent
- CodeWiki: https://github.com/FSoft-AI4Code/CodeWiki
- DocAgent (Meta): https://github.com/facebookresearch/DocAgent
- Codebase Context Spec: https://github.com/Agentic-Insights/codebase-context-spec
- VS Code Context Engineering Guide: https://code.visualstudio.com/docs/copilot/guides/context-engineering-guide
- Post-compaction hooks: https://medium.com/@porter.nicholas/claude-code-post-compaction-hooks-for-context-renewal-7b616dcaa204
- post_compact_reminder: https://github.com/Dicklesworthstone/post_compact_reminder
- Context Engineering overview (Faros AI): https://www.faros.ai/blog/context-engineering-for-developers
- context-engineering-intro: https://github.com/coleam00/context-engineering-intro
- State of CE 2026 (SwirlAI): https://www.newsletter.swirlai.com/p/state-of-context-engineering-in-2026
- Martin Fowler on CE for coding agents: https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html
- Claude Code hooks reference: https://code.claude.com/docs/en/hooks
- Claude Code best practices: https://code.claude.com/docs/en/best-practices
- Potpie AI: https://potpie.ai/
- GitLab Knowledge Graph: https://docs.gitlab.com/user/project/repository/knowledge_graph/
- CodeGraphContext: https://github.com/CodeGraphContext/CodeGraphContext
- Augment Code Context Engine: https://www.augmentcode.com/guides/context-engine-vs-rag-5-technical-showdowns-for-code-ai
