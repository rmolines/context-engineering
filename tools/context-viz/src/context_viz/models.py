"""Data models for context visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class BlockCategory(Enum):
    """Category of a context block."""

    STATIC = "static"  # CLAUDE.md, rules, memories, hooks
    INJECTED = "injected"  # Read, Agent, WebSearch, Grep, Glob
    CONVERSATION = "conversation"  # user/assistant messages, Bash, Edit, Write


@dataclass
class ContextBlock:
    """A single block in the context window."""

    category: BlockCategory
    label: str
    estimated_tokens: int
    timestamp: datetime
    turn_index: int = 0
    tool_name: str | None = None
    file_path: str | None = None
    is_compacted: bool = False

    @property
    def icon(self) -> str:
        if self.is_compacted:
            return "░"
        return "■"


class FileStatus(Enum):
    """Status of an on-disk file relative to the session."""

    IN_SESSION = "in_session"  # read and still in context (after last compaction)
    WAS_USED = "was_used"  # read but likely compacted
    NEVER_USED = "never_used"  # available but never touched

    @property
    def icon(self) -> str:
        match self:
            case FileStatus.IN_SESSION:
                return "■"
            case FileStatus.WAS_USED:
                return "●"
            case FileStatus.NEVER_USED:
                return "○"


@dataclass
class DiskFile:
    """A file on disk that could be loaded into context."""

    path: Path
    size_bytes: int
    estimated_tokens: int
    status: FileStatus
    last_modified: datetime


@dataclass
class CompactionEvent:
    """A detected compaction event."""

    timestamp: datetime
    tokens_before: int
    tokens_after: int


@dataclass
class SessionState:
    """Full state of a session for rendering."""

    session_id: str
    blocks: list[ContextBlock] = field(default_factory=list)
    compaction_events: list[CompactionEvent] = field(default_factory=list)
    read_files: set[str] = field(default_factory=set)

    # Token counts from the transcript
    total_input_tokens: int = 0
    context_window_size: int = 200_000

    # Computed
    @property
    def static_tokens(self) -> int:
        return sum(b.estimated_tokens for b in self.blocks if b.category == BlockCategory.STATIC)

    @property
    def injected_tokens(self) -> int:
        return sum(
            b.estimated_tokens for b in self.blocks if b.category == BlockCategory.INJECTED and not b.is_compacted
        )

    @property
    def conversation_tokens(self) -> int:
        return sum(
            b.estimated_tokens for b in self.blocks if b.category == BlockCategory.CONVERSATION and not b.is_compacted
        )

    @property
    def used_percentage(self) -> float:
        if self.context_window_size == 0:
            return 0.0
        return (self.total_input_tokens / self.context_window_size) * 100

    @property
    def compact_threshold(self) -> int:
        return int(self.context_window_size * 0.835)
