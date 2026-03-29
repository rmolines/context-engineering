"""Main Textual application."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Label, Static
from textual.worker import Worker

from .disk_scanner import DiskScanner
from .models import SessionState
from .transcript import TranscriptParser, TranscriptReader
from .widgets.disk_panel import DiskPanel
from .widgets.header_bar import HeaderBar
from .widgets.session_panel import SessionPanel


class ContextVizApp(App):
    """Context Window Visualizer for Claude Code sessions."""

    CSS_PATH = "app.tcss"
    TITLE = "context-viz"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_disk", "Disk"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, transcript_path: Path, project_dir: Path) -> None:
        super().__init__()
        self.transcript_path = transcript_path
        self.project_dir = project_dir
        self.reader = TranscriptReader(transcript_path)
        self.parser = TranscriptParser()
        self.scanner = DiskScanner(project_dir)
        self._show_disk = True
        self._state: SessionState | None = None

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        with Vertical(id="content"):
            yield SessionPanel(id="session-panel")
            yield DiskPanel(id="disk-panel")
        yield Footer()

    def on_mount(self) -> None:
        self._do_refresh()
        self.set_interval(2.0, self._do_refresh)

    def _do_refresh(self) -> None:
        self.reader.poll()
        state = self.parser.parse(self.reader.entries)
        self._state = state

        last_compact_ts = state.compaction_events[-1].timestamp if state.compaction_events else None
        disk_files = self.scanner.scan(state.read_files, last_compact_ts)

        self.query_one(HeaderBar).update_state(state)
        self.query_one(SessionPanel).update_state(state)
        self.query_one(DiskPanel).update_state(disk_files)

    def action_toggle_disk(self) -> None:
        self._show_disk = not self._show_disk
        disk = self.query_one("#disk-panel")
        disk.display = self._show_disk

    def action_refresh(self) -> None:
        self._do_refresh()
