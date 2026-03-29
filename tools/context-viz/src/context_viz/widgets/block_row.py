"""Single block row widget."""

from __future__ import annotations

from textual.widgets import Static

from ..models import BlockCategory, ContextBlock


def _format_tokens(tokens: int) -> str:
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k"
    return str(tokens)


class BlockRow(Static):
    """Renders a single context block as a row."""

    def __init__(self, block: ContextBlock) -> None:
        self.block = block
        # Build display text
        tokens_str = _format_tokens(block.estimated_tokens)
        bar_width = min(40, max(1, block.estimated_tokens // 200))
        bar = "█" * bar_width

        text = f"  {block.icon} {bar:<40s} {tokens_str:>6s} tk  {block.label}"

        super().__init__(text)

        # Apply CSS classes
        self.add_class("block-row")
        if block.is_compacted:
            self.add_class("compacted")
        elif block.category == BlockCategory.STATIC:
            self.add_class("static")
        elif block.category == BlockCategory.INJECTED:
            self.add_class("injected")
        else:
            self.add_class("conversation")
