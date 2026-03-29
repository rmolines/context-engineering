"""Disk context panel — Vision 2."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, Static

from ..models import DiskFile


def _format_tokens(tokens: int) -> str:
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k"
    return str(tokens)


class DiskPanel(Static):
    """Renders on-disk files available for context injection."""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="disk-scroll"):
            yield Label(" ON DISK (available to pull)", classes="section-header")
            yield Static(id="disk-content")

    def update_state(self, disk_files: dict[str, list[DiskFile]]) -> None:
        container = self.query_one("#disk-content", Static)
        container.remove_children()

        if not disk_files:
            container.mount(Label("  (no context files found)", classes="disk-file never-used"))
            return

        for label, files in disk_files.items():
            total_tokens = sum(f.estimated_tokens for f in files)
            header = Label(
                f"  {label:<35s} ~{_format_tokens(total_tokens)} tk total",
                classes="dir-header",
            )
            container.mount(header)

            for f in files:
                tokens_str = _format_tokens(f.estimated_tokens)
                css_class = f"disk-file {f.status.value.replace('_', '-')}"
                row = Static(
                    f"    {f.status.icon} {f.path.name:<40s} {tokens_str:>6s} tk",
                    classes=css_class,
                )
                container.mount(row)
