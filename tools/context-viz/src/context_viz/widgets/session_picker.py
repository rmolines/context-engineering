"""Interactive session picker TUI."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Header, Static

from ..cli import _format_tokens, _relative_time


class SessionPicker(App):
    """Pick a Claude Code session from a list."""

    TITLE = "context-viz"
    CSS = """
    #subtitle {
        dock: top;
        height: 1;
        padding: 0 2;
        background: $primary-darken-2;
        color: $text-muted;
    }
    DataTable {
        height: 1fr;
    }
    DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
    }
    #hint {
        dock: bottom;
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("enter", "select", "Select"),
    ]

    selected_path: Path | None = None

    def __init__(self, sessions: list[dict]) -> None:
        super().__init__()
        self.sessions = sessions

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"  {len(self.sessions)} sessions found. Arrow keys to navigate, Enter to select.", id="subtitle")
        yield DataTable(cursor_type="row")
        yield Static("  ● LIVE = active now   ○ STALE = not closed cleanly   · DONE = ended", id="hint")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("", "Tokens", "When", "First Message")

        for i, s in enumerate(self.sessions):
            status = s.get("status", "closed")
            icon = {"active": "●", "stale": "○", "closed": "·"}.get(status, "?")
            label = {"active": "LIVE", "stale": "STALE", "closed": "DONE"}.get(status, "?")
            status_str = f"{icon} {label}"
            tokens = _format_tokens(s["total_tokens"])
            when = _relative_time(s.get("last_ts"))
            msg = s["first_msg"][:60] if s["first_msg"] else "(empty)"

            table.add_row(status_str, tokens, when, msg, key=str(i))

    def action_select(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(self.sessions):
            self.selected_path = self.sessions[table.cursor_row]["path"]
        self.exit()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = int(event.row_key.value)
        if 0 <= idx < len(self.sessions):
            self.selected_path = self.sessions[idx]["path"]
        self.exit()
