#!/bin/bash
# post-compact-hook.sh — Re-injeta contexto essencial após compaction
#
# Uso: SessionStart hook com matcher "compact"
# Claude Code invoca este script com JSON no stdin quando a sessão
# foi iniciada após um /compact. O script emite additionalContext
# com STATE.md, domain map e lembrete do CLAUDE.md.
#
# Instalação:
#   cp templates/post-compact-hook.sh .claude/hooks/post-compact.sh
#   chmod +x .claude/hooks/post-compact.sh
#   Adicionar entrada em .claude/settings.json (ver templates/hooks-config.json)

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

CONTEXT=""

# --- STATE.md ---
# Se existe state ativo, re-injeta para evitar amnésia pós-compaction
STATE_FILE="${CWD}/.claude/state/STATE.md"
if [ -f "$STATE_FILE" ]; then
  STATE_CONTENT=$(cat "$STATE_FILE")
  CONTEXT="${CONTEXT}## Project State (re-injected after compaction)

${STATE_CONTENT}

"
fi

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
