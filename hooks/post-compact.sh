#!/bin/bash
# post-compact-hook.sh — Re-injeta contexto essencial após compaction
#
# Uso: SessionStart hook com matcher "compact"
# Claude Code invoca este script com JSON no stdin quando a sessão
# foi iniciada após um /compact. O script emite additionalContext
# com bootstrap reminder, domain map e lembrete do CLAUDE.md.
#
# Session state lives in GitHub (Issues, comments, Milestones).
# After compaction, user should run /bootstrap to reload context.

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

CONTEXT=""

# --- Session Context ---
# Remind user to run /bootstrap after compaction
CONTEXT="${CONTEXT}## Session Context

Run /bootstrap to refresh session context after compaction.

"

# --- Domain map ---
# Index de documentação do projeto — orientação rápida de onde fica o quê
DOMAIN_INDEX="${CWD}/.claude/docs/index.md"
if [ -f "$DOMAIN_INDEX" ]; then
  INDEX_CONTENT=$(cat "$DOMAIN_INDEX")
  CONTEXT="${CONTEXT}## Domain Map

${INDEX_CONTENT}

"
fi

# --- CLAUDE.md reminder ---
# Não re-injeta o conteúdo completo (Claude Code já o carrega), apenas
# emite um lembrete explícito para garantir que seja relido após compaction
CLAUDE_MD="${CWD}/CLAUDE.md"
if [ -f "$CLAUDE_MD" ]; then
  CONTEXT="${CONTEXT}## Context reminder

Re-read CLAUDE.md for full project context — it was loaded before compaction
and must be consulted again before acting.

"
fi

# Se não há nada a injetar, sair silenciosamente
if [ -z "$CONTEXT" ]; then
  exit 0
fi

# Emite o contexto como additionalContext para o SessionStart hook
CONTEXT="${CONTEXT}---
Context compaction detected. The above was re-injected to restore session continuity."

jq -n --arg ctx "$CONTEXT" '{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $ctx
  }
}'

exit 0
