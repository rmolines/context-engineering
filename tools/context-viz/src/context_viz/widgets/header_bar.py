"""Header bar widget showing session overview."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, ProgressBar, Static

from ..models import SessionState


class HeaderBar(Static):
    """Top bar showing model, usage %, token count, and cost."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Label("--", id="header-model")
            yield Label("0%", id="header-usage")
            yield ProgressBar(total=100, show_eta=False, show_percentage=False, id="header-progress")
            yield Label("0/200k tk", id="header-tokens")

    def update_state(self, state: SessionState) -> None:
        self.query_one("#header-model", Label).update(state.session_id[:8])

        pct = state.used_percentage
        self.query_one("#header-usage", Label).update(f"{pct:.0f}%")

        progress = self.query_one("#header-progress", ProgressBar)
        progress.update(progress=pct)

        total_k = state.total_input_tokens / 1000
        max_k = state.context_window_size / 1000
        self.query_one("#header-tokens", Label).update(f"{total_k:.0f}k/{max_k:.0f}k tk")
