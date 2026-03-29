"""Session context panel — Vision 1."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, Static

from ..models import BlockCategory, ContextBlock, SessionState
from .block_row import BlockRow, _format_tokens

# Sections that show compact summary + top N instead of all blocks
COMPACT_SECTIONS = {BlockCategory.CONVERSATION, BlockCategory.INJECTED}
TOP_N = 5


class SessionPanel(Static):
    """Renders the session context as a vertical list of proportional blocks."""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="session-scroll"):
            yield Label("STATIC", classes="section-header")
            yield Static(id="static-blocks")
            yield Label("INJECTED", classes="section-header")
            yield Static(id="injected-blocks")
            yield Label("CONVERSATION", classes="section-header")
            yield Static(id="conv-blocks")
            yield Label("", id="pointer-bar")
            yield Static(id="free-space")
            yield Label("── auto-compact threshold ──", id="compact-threshold")

    def update_state(self, state: SessionState) -> None:
        """Re-render all blocks from session state."""
        # Group blocks by category
        static_blocks = [b for b in state.blocks if b.category == BlockCategory.STATIC]
        injected_blocks = [b for b in state.blocks if b.category == BlockCategory.INJECTED]
        conv_blocks = [b for b in state.blocks if b.category == BlockCategory.CONVERSATION]

        # Update each section
        self._update_section("#static-blocks", static_blocks, BlockCategory.STATIC)
        self._update_section("#injected-blocks", injected_blocks, BlockCategory.INJECTED)
        self._update_section("#conv-blocks", conv_blocks, BlockCategory.CONVERSATION)

        # Update pointer bar
        pct = state.used_percentage
        total_k = state.total_input_tokens / 1000
        threshold_k = state.compact_threshold / 1000
        self.query_one("#pointer-bar", Label).update(
            f"◄── {total_k:.0f}k tk ({pct:.0f}%) ──  threshold: {threshold_k:.0f}k ──►"
        )

        # Update compact threshold
        remaining_k = (state.compact_threshold - state.total_input_tokens) / 1000
        if remaining_k > 0:
            self.query_one("#compact-threshold", Label).update(
                f"── auto-compact in ~{remaining_k:.0f}k tk ──"
            )
        else:
            self.query_one("#compact-threshold", Label).update(
                "── AUTO-COMPACT THRESHOLD REACHED ──"
            )

    def _update_section(
        self, container_id: str, blocks: list[ContextBlock], category: BlockCategory
    ) -> None:
        container = self.query_one(container_id, Static)
        container.remove_children()

        if not blocks:
            container.mount(Label("  (empty)", classes="block-row"))
            return

        # Show compacted blocks as a single summary
        compacted = [b for b in blocks if b.is_compacted]
        active = [b for b in blocks if not b.is_compacted]

        if compacted:
            total_compacted = sum(b.estimated_tokens for b in compacted)
            tokens_str = _format_tokens(total_compacted)
            summary = Static(
                f"  ░ {'░' * 20:<40s} {tokens_str:>6s} tk  [{len(compacted)} blocks compacted]",
                classes="block-row compacted",
            )
            container.mount(summary)

        # Compact mode for CONVERSATION and INJECTED: summary bar + top 5
        if category in COMPACT_SECTIONS and len(active) > TOP_N:
            self._render_compact(container, active, category)
        else:
            for block in active:
                container.mount(BlockRow(block))

    def _render_compact(
        self, container: Static, blocks: list[ContextBlock], category: BlockCategory
    ) -> None:
        """Render a section as: summary bar + top N by tokens."""
        total_tokens = sum(b.estimated_tokens for b in blocks)
        tokens_str = _format_tokens(total_tokens)

        # Count meaningful items
        if category == BlockCategory.CONVERSATION:
            user_count = sum(1 for b in blocks if b.label.startswith("User:"))
            claude_count = sum(1 for b in blocks if b.label.startswith("Claude:"))
            tool_count = len(blocks) - user_count - claude_count
            parts = []
            if user_count:
                parts.append(f"{user_count} user")
            if claude_count:
                parts.append(f"{claude_count} claude")
            if tool_count:
                parts.append(f"{tool_count} tool")
            detail = " · ".join(parts)
        else:
            detail = f"{len(blocks)} items"

        # Summary bar
        bar_width = min(40, max(1, total_tokens // 500))
        bar = "█" * bar_width
        summary = Static(
            f"  {bar:<40s} {tokens_str:>6s} tk  {detail}",
            classes="block-row",
        )
        container.mount(summary)

        # Top N by token count
        top = sorted(blocks, key=lambda b: b.estimated_tokens, reverse=True)[:TOP_N]
        header = Static(
            f"  {'':>42s} top {TOP_N} by tokens:",
            classes="block-row top-header",
        )
        container.mount(header)

        for block in top:
            container.mount(BlockRow(block))
