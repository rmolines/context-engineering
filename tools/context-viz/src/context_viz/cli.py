"""CLI entry point and transcript discovery."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Default: only show sessions from the last 24 hours
DEFAULT_MAX_AGE_HOURS = 24
# Skip sessions with no real content (ghost sessions)
MIN_ENTRY_COUNT = 3


def _transcript_dir(project_dir: Path) -> Path:
    """Get the Claude transcript directory for a project."""
    encoded = str(project_dir).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded


def _relative_time(ts_str: str | None) -> str:
    """Convert ISO timestamp to human-friendly relative time."""
    if not ts_str:
        return "?"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            return "just now"
        if seconds < 3600:
            m = int(seconds / 60)
            return f"{m}m ago"
        if seconds < 86400:
            h = int(seconds / 3600)
            return f"{h}h ago"
        days = int(seconds / 86400)
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days}d ago"
        return dt.strftime("%b %d")
    except (ValueError, AttributeError):
        return "?"


def _format_tokens(tokens: int) -> str:
    """Format token count as compact string."""
    if tokens == 0:
        return "-"
    if tokens >= 1000:
        return f"{tokens / 1000:.0f}k"
    return str(tokens)



def _read_session_summary(jsonl_path: Path) -> dict:
    """Read minimal info from a JSONL to summarize the session."""
    session_id = jsonl_path.stem
    first_user_msg = ""
    total_tokens = 0
    entry_count = 0
    last_ts = None
    # Track the index of the last real message vs last close marker
    last_message_idx = -1
    last_close_marker_idx = -1

    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_count += 1
                entry_type = entry.get("type", "")
                ts = entry.get("timestamp")
                if ts:
                    last_ts = ts

                # Track message vs close marker positions
                if entry_type in ("user", "assistant"):
                    last_message_idx = entry_count
                if entry_type in ("last-prompt", "file-history-snapshot"):
                    last_close_marker_idx = entry_count

                if entry_type == "user":
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    if isinstance(content, str) and content and not first_user_msg:
                        first_user_msg = content[:80]

                if entry_type == "assistant":
                    usage = entry.get("message", {}).get("usage", {})
                    tokens = (
                        usage.get("input_tokens", 0)
                        + usage.get("cache_creation_input_tokens", 0)
                        + usage.get("cache_read_input_tokens", 0)
                    )
                    if tokens > total_tokens:
                        total_tokens = tokens
    except Exception:
        pass

    mtime = jsonl_path.stat().st_mtime

    # Determine status: closed only if close markers are AFTER last real message
    if last_close_marker_idx > last_message_idx and last_close_marker_idx >= 0:
        status = "closed"
    else:
        age_minutes = (time.time() - mtime) / 60
        status = "active" if age_minutes < 5 else "stale"

    return {
        "session_id": session_id,
        "path": jsonl_path,
        "first_msg": first_user_msg,
        "total_tokens": total_tokens,
        "entry_count": entry_count,
        "last_ts": last_ts,
        "mtime": mtime,
        "status": status,
    }


def list_sessions(
    project_dir: Path,
    max_age_hours: float | None = DEFAULT_MAX_AGE_HOURS,
    include_empty: bool = False,
) -> list[dict]:
    """List sessions for a project, sorted by most recent first.

    Args:
        project_dir: project directory
        max_age_hours: only include sessions from the last N hours (None = all)
        include_empty: include ghost sessions with < MIN_ENTRY_COUNT entries
    """
    tdir = _transcript_dir(project_dir)
    if not tdir.exists():
        return []

    now = time.time()
    jsonl_files = sorted(tdir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)

    # Pre-filter by mtime before reading content (fast)
    if max_age_hours is not None:
        cutoff = now - (max_age_hours * 3600)
        jsonl_files = [f for f in jsonl_files if f.stat().st_mtime >= cutoff]

    sessions = [_read_session_summary(f) for f in jsonl_files]

    # Filter out ghost sessions
    if not include_empty:
        sessions = [s for s in sessions if s["entry_count"] >= MIN_ENTRY_COUNT]

    return sessions


def find_transcript(project_dir: Path, session_id: str | None = None) -> Path | None:
    """Find a specific transcript or the most recent one."""
    tdir = _transcript_dir(project_dir)
    if not tdir.exists():
        return None

    if session_id:
        candidates = [f for f in tdir.glob("*.jsonl") if f.stem.startswith(session_id)]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            print(f"Ambiguous session ID '{session_id}', matches {len(candidates)} sessions:", file=sys.stderr)
            for c in candidates:
                print(f"  {c.stem}", file=sys.stderr)
            return None
        return None

    jsonl_files = list(tdir.glob("*.jsonl"))
    if not jsonl_files:
        return None
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)


STATUS_DISPLAY = {
    "active": ("●", "LIVE"),
    "stale": ("○", "STALE"),
    "closed": ("·", "DONE"),
}


def _print_session_list(sessions: list[dict]) -> None:
    """Print a formatted list of sessions."""
    if not sessions:
        print("No sessions found.")
        return

    print(f"{'#':<3} {'':>8} {'Tokens':>7}  {'When':<12} First Message")
    print("─" * 80)

    for i, s in enumerate(sessions):
        icon, status_label = STATUS_DISPLAY.get(s.get("status", "closed"), ("?", "?"))
        when = _relative_time(s.get("last_ts"))
        tokens = _format_tokens(s["total_tokens"])
        msg = s["first_msg"][:50] if s["first_msg"] else "(empty)"

        status_str = f"{icon} {status_label}" if status_label else f"{icon}       "
        print(f"{i:<3} {status_str:<8} {tokens:>7}  {when:<12} {msg}")


def _pick_session_interactive(sessions: list[dict]) -> Path | None:
    """Open a Textual TUI to pick a session."""
    from .widgets.session_picker import SessionPicker

    picker = SessionPicker(sessions)
    picker.run()
    return picker.selected_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="context-viz",
        description="Real-time context window visualizer for Claude Code sessions",
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        help="Path to a specific transcript JSONL file",
    )
    parser.add_argument(
        "--session-id",
        help="Session ID (or prefix) to find transcript for",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_sessions",
        help="List available sessions and exit",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all sessions (default: last 24h, skip empty)",
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Dump parsed blocks to stdout instead of launching TUI",
    )
    return parser.parse_args(argv)


def resolve_transcript(args: argparse.Namespace) -> Path | None:
    """Resolve transcript path from CLI arguments."""
    if args.transcript:
        if args.transcript.exists():
            return args.transcript
        print(f"Error: transcript not found: {args.transcript}", file=sys.stderr)
        return None

    if args.session_id:
        transcript = find_transcript(args.project_dir, args.session_id)
        if not transcript:
            print(f"Error: no session matching '{args.session_id}'", file=sys.stderr)
        return transcript

    max_age = None if args.all else DEFAULT_MAX_AGE_HOURS
    sessions = list_sessions(args.project_dir, max_age_hours=max_age, include_empty=args.all)
    if not sessions:
        print(f"Error: no sessions found for {args.project_dir}", file=sys.stderr)
        if not args.all:
            print("  (try --all to include older sessions)", file=sys.stderr)
        return None

    if len(sessions) == 1:
        return sessions[0]["path"]

    return _pick_session_interactive(sessions)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.list_sessions:
        max_age = None if args.all else DEFAULT_MAX_AGE_HOURS
        sessions = list_sessions(args.project_dir, max_age_hours=max_age, include_empty=args.all)
        _print_session_list(sessions)
        if not args.all:
            print(f"\n  Showing last {DEFAULT_MAX_AGE_HOURS}h. Use --all for full history.")
        return 0

    transcript_path = resolve_transcript(args)
    if not transcript_path:
        return 1

    if args.dump:
        return _dump_blocks(transcript_path, args.project_dir)

    from .app import ContextVizApp

    app = ContextVizApp(transcript_path=transcript_path, project_dir=args.project_dir)
    app.run()
    return 0


def _dump_blocks(transcript_path: Path, project_dir: Path) -> int:
    """Dump parsed blocks to stdout for debugging."""
    from .disk_scanner import DiskScanner
    from .transcript import TranscriptParser, TranscriptReader

    reader = TranscriptReader(transcript_path)
    reader.poll()

    parser = TranscriptParser()
    state = parser.parse(reader.entries)

    print(f"Session: {state.session_id}")
    print(f"Total input tokens: {state.total_input_tokens:,}")
    print(f"Used: {state.used_percentage:.1f}%")
    print(f"Compaction events: {len(state.compaction_events)}")
    print(f"Read files: {len(state.read_files)}")
    print()

    for block in state.blocks:
        compact_mark = " [COMPACTED]" if block.is_compacted else ""
        print(
            f"  {block.icon} [{block.category.value:12s}] "
            f"{block.estimated_tokens:>6,} tk  "
            f"{block.label}{compact_mark}"
        )

    print()

    last_compact_ts = state.compaction_events[-1].timestamp if state.compaction_events else None
    scanner = DiskScanner(project_dir)
    disk_files = scanner.scan(state.read_files, last_compact_ts)

    print("ON DISK:")
    for label, files in disk_files.items():
        total_tokens = sum(f.estimated_tokens for f in files)
        print(f"  {label:<30s} ~{total_tokens:,} tk")
        for f in files:
            print(f"    {f.status.icon} {f.path.name:<40s} {f.estimated_tokens:>6,} tk")

    return 0
