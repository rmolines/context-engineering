"""Transcript JSONL reader and parser."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import BlockCategory, CompactionEvent, ContextBlock, SessionState
from .tokens import OVERHEAD_PER_MESSAGE, estimate_tokens

# Tools that inject context (user deliberately pulled these in)
INJECTED_TOOLS = {"Read", "Agent", "WebSearch", "WebFetch", "Grep", "Glob"}

# Tools that are part of normal conversation flow
CONVERSATION_TOOLS = {"Bash", "Edit", "Write", "TodoWrite", "NotebookEdit"}

# Tools to skip (meta/framework, not context-relevant)
SKIP_TOOLS = {
    "EnterPlanMode",
    "ExitPlanMode",
    "EnterWorktree",
    "ExitWorktree",
    "AskUserQuestion",
    "Skill",
    "CronCreate",
    "CronDelete",
    "CronList",
}


def _parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp from JSONL entry."""
    ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts)


def _extract_label(tool_name: str, tool_input: dict) -> str:
    """Generate a human-readable label for a tool call."""
    match tool_name:
        case "Read":
            fp = tool_input.get("file_path", "")
            return f"Read: {Path(fp).name}" if fp else "Read"
        case "Agent":
            desc = tool_input.get("description", "")
            return f"Agent: {desc[:40]}" if desc else "Agent"
        case "WebSearch":
            q = tool_input.get("query", "")
            return f"Web: {q[:40]}" if q else "WebSearch"
        case "WebFetch":
            url = tool_input.get("url", "")
            return f"Fetch: {url[:40]}" if url else "WebFetch"
        case "Grep":
            pat = tool_input.get("pattern", "")
            return f"Grep: {pat[:30]}" if pat else "Grep"
        case "Glob":
            pat = tool_input.get("pattern", "")
            return f"Glob: {pat[:30]}" if pat else "Glob"
        case "Bash":
            cmd = tool_input.get("command", "")
            return f"Bash: {cmd[:30]}" if cmd else "Bash"
        case "Edit":
            fp = tool_input.get("file_path", "")
            return f"Edit: {Path(fp).name}" if fp else "Edit"
        case "Write":
            fp = tool_input.get("file_path", "")
            return f"Write: {Path(fp).name}" if fp else "Write"
        case _:
            return tool_name


def _categorize_tool(tool_name: str) -> BlockCategory | None:
    """Determine category for a tool call."""
    if tool_name in INJECTED_TOOLS:
        return BlockCategory.INJECTED
    if tool_name in CONVERSATION_TOOLS:
        return BlockCategory.CONVERSATION
    if tool_name in SKIP_TOOLS:
        return None
    # MCP tools and unknown — treat as injected (they bring context in)
    if tool_name.startswith("mcp__"):
        return BlockCategory.INJECTED
    return BlockCategory.CONVERSATION


class TranscriptReader:
    """Incrementally reads a JSONL transcript file."""

    def __init__(self, path: Path):
        self.path = path
        self._offset = 0
        self._entries: list[dict] = []

    def poll(self) -> list[dict]:
        """Read new entries since last poll. Returns only new entries."""
        new_entries = []
        try:
            with open(self.path) as f:
                f.seek(self._offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        new_entries.append(entry)
                        self._entries.append(entry)
                    except json.JSONDecodeError:
                        continue
                self._offset = f.tell()
        except FileNotFoundError:
            pass
        return new_entries

    @property
    def entries(self) -> list[dict]:
        return self._entries


class TranscriptParser:
    """Parses transcript entries into context blocks and session state."""

    def __init__(self):
        self._tool_use_map: dict[str, dict] = {}  # tool_use_id -> {name, input}
        self._usage_history: list[tuple[datetime, int]] = []
        self._turn_index = 0

    def parse(self, entries: list[dict]) -> SessionState:
        """Parse all entries into a SessionState."""
        state = SessionState(session_id="")
        self._tool_use_map.clear()
        self._usage_history.clear()
        self._turn_index = 0

        for entry in entries:
            entry_type = entry.get("type")

            if not state.session_id:
                state.session_id = entry.get("sessionId", "")

            if entry_type == "user":
                self._process_user(entry, state)
            elif entry_type == "assistant":
                self._process_assistant(entry, state)
            elif entry_type == "progress":
                self._process_progress(entry, state)

        # Detect compaction events
        state.compaction_events = self._detect_compaction()

        # Mark compacted blocks
        if state.compaction_events:
            last_compaction = state.compaction_events[-1].timestamp
            for block in state.blocks:
                if block.timestamp < last_compaction and block.category != BlockCategory.STATIC:
                    block.is_compacted = True

        # Set total tokens from last usage
        if self._usage_history:
            _, last_tokens = self._usage_history[-1]
            state.total_input_tokens = last_tokens

        return state

    def _process_user(self, entry: dict, state: SessionState) -> None:
        message = entry.get("message", {})
        content = message.get("content", "")
        ts = _parse_timestamp(entry.get("timestamp", "1970-01-01T00:00:00Z"))

        if isinstance(content, str) and content:
            # User text message
            self._turn_index += 1
            label = f"User: {content[:50]}"
            tokens = estimate_tokens(content) + OVERHEAD_PER_MESSAGE
            state.blocks.append(
                ContextBlock(
                    category=BlockCategory.CONVERSATION,
                    label=label,
                    estimated_tokens=tokens,
                    timestamp=ts,
                    turn_index=self._turn_index,
                )
            )
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "tool_result":
                    self._process_tool_result(item, ts, state)

    def _process_tool_result(self, item: dict, ts: datetime, state: SessionState) -> None:
        tool_use_id = item.get("tool_use_id", "")
        tool_info = self._tool_use_map.get(tool_use_id)
        if not tool_info:
            return

        tool_name = tool_info["name"]
        tool_input = tool_info["input"]
        category = _categorize_tool(tool_name)
        if category is None:
            return

        # Estimate tokens from the result content
        result_content = item.get("content", "")
        if isinstance(result_content, list):
            result_content = " ".join(str(c.get("text", "")) for c in result_content if isinstance(c, dict))
        elif not isinstance(result_content, str):
            result_content = str(result_content)

        result_tokens = estimate_tokens(result_content) + OVERHEAD_PER_MESSAGE

        label = _extract_label(tool_name, tool_input)

        state.blocks.append(
            ContextBlock(
                category=category,
                label=label,
                estimated_tokens=result_tokens,
                timestamp=ts,
                turn_index=self._turn_index,
                tool_name=tool_name,
                file_path=tool_input.get("file_path"),
            )
        )

        # Track read files for disk scanner
        if tool_name == "Read" and tool_input.get("file_path"):
            state.read_files.add(tool_input["file_path"])

    def _process_assistant(self, entry: dict, state: SessionState) -> None:
        message = entry.get("message", {})
        content = message.get("content", [])
        ts = _parse_timestamp(entry.get("timestamp", "1970-01-01T00:00:00Z"))

        # Track usage for compaction detection
        usage = message.get("usage", {})
        input_tokens = (
            usage.get("input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
        )
        if input_tokens > 0:
            self._usage_history.append((ts, input_tokens))

        if not isinstance(content, list):
            return

        has_text = False
        text_content = ""

        for item in content:
            if not isinstance(item, dict):
                continue

            if item.get("type") == "tool_use":
                # Register for later linkage with tool_result
                self._tool_use_map[item["id"]] = {
                    "name": item["name"],
                    "input": item.get("input", {}),
                }

            elif item.get("type") == "text":
                text = item.get("text", "").strip()
                if text:
                    has_text = True
                    text_content += text

        # Only create a text block if there's meaningful text (not just whitespace before tool calls)
        if has_text and len(text_content) > 10:
            tokens = estimate_tokens(text_content) + OVERHEAD_PER_MESSAGE
            label = f"Claude: {text_content[:50]}"
            state.blocks.append(
                ContextBlock(
                    category=BlockCategory.CONVERSATION,
                    label=label,
                    estimated_tokens=tokens,
                    timestamp=ts,
                    turn_index=self._turn_index,
                )
            )

    def _process_progress(self, entry: dict, state: SessionState) -> None:
        data = entry.get("data", {})
        progress_type = data.get("type", "")
        ts = _parse_timestamp(entry.get("timestamp", "1970-01-01T00:00:00Z"))

        if progress_type == "hook_progress":
            hook_event = data.get("hookEvent", "")
            # Only the first SessionStart hook matters (it injects CLAUDE.md etc.)
            if hook_event == "SessionStart" and not any(
                b.category == BlockCategory.STATIC for b in state.blocks
            ):
                state.blocks.append(
                    ContextBlock(
                        category=BlockCategory.STATIC,
                        label=f"Hook: {hook_event}",
                        estimated_tokens=100,  # placeholder, refined later
                        timestamp=ts,
                        turn_index=0,
                    )
                )

    def _detect_compaction(self) -> list[CompactionEvent]:
        """Detect compaction events from usage history drops."""
        events = []
        for i in range(1, len(self._usage_history)):
            prev_ts, prev_tokens = self._usage_history[i - 1]
            curr_ts, curr_tokens = self._usage_history[i]
            # >30% drop with meaningful token count indicates compaction
            if prev_tokens > 10_000 and curr_tokens < prev_tokens * 0.7:
                events.append(
                    CompactionEvent(
                        timestamp=curr_ts,
                        tokens_before=prev_tokens,
                        tokens_after=curr_tokens,
                    )
                )
        return events
