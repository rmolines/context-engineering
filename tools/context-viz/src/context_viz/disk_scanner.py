"""Scan known directories for available context files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import DiskFile, FileStatus
from .tokens import estimate_tokens_from_size


class DiskScanner:
    """Scans known directories for markdown files that could be loaded into context."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self._dirs = self._build_dirs()

    def _build_dirs(self) -> list[tuple[str, Path]]:
        """Build list of (label, path) for directories to scan."""
        encoded = str(self.project_dir).replace("/", "-")
        memory_dir = Path.home() / ".claude" / "projects" / encoded / "memory"

        dirs = [
            ("research/", self.project_dir / "research"),
            (".claude/state/", self.project_dir / ".claude" / "state"),
            (".claude/discoveries/", self.project_dir / ".claude" / "discoveries"),
            ("memory/", memory_dir),
        ]
        return dirs

    def scan(
        self, read_files: set[str], last_compaction_ts: datetime | None = None
    ) -> dict[str, list[DiskFile]]:
        """Scan directories and return files with their status.

        Args:
            read_files: set of absolute file paths that were Read in the session
            last_compaction_ts: timestamp of last compaction event (if any)
        """
        result = {}

        for label, dir_path in self._dirs:
            if not dir_path.exists():
                continue

            files = []
            for f in sorted(dir_path.glob("*.md")):
                if f.name.startswith(".") or f.name == "MEMORY.md":
                    continue

                abs_path = str(f.resolve())
                status = self._determine_status(abs_path, read_files, last_compaction_ts)

                files.append(
                    DiskFile(
                        path=f,
                        size_bytes=f.stat().st_size,
                        estimated_tokens=estimate_tokens_from_size(f.stat().st_size),
                        status=status,
                        last_modified=datetime.fromtimestamp(f.stat().st_mtime),
                    )
                )

            if files:
                result[label] = files

        return result

    def _determine_status(
        self,
        abs_path: str,
        read_files: set[str],
        last_compaction_ts: datetime | None,
    ) -> FileStatus:
        if abs_path not in read_files:
            return FileStatus.NEVER_USED
        if last_compaction_ts is not None:
            # If compaction happened, files read before it are "was_used"
            # We can't know exactly when each file was read without more tracking,
            # so conservatively mark all read files as WAS_USED if any compaction occurred
            return FileStatus.WAS_USED
        return FileStatus.IN_SESSION
