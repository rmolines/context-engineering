# Session Cycle — Explore → Plan → Execute

For non-trivial tasks, follow this cycle before acting:

## 1. Explore
- Read relevant code and understand context before proposing changes
- If there's a knowledge gap (unknown API, new lib, project patterns): research first
- If the task is ambiguous: ask clarifying questions
- Don't assume — verify

## 2. Plan
- Decompose the task into concrete steps before executing
- For tasks with 3+ steps or architectural risk: write the plan and get approval
- Each step should be independently verifiable
- Identify what can be parallelized via subagents

## 3. Execute
- One step at a time. Validate before moving to the next
- Delegate parallel or verbose work to subagents
- If a step fails: diagnose the cause before retrying

The cycle adapts to complexity: a simple bugfix can be explore-execute directly. A large refactor needs all 3 steps with a written plan.
