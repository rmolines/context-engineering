"""Token estimation utilities."""

CHARS_PER_TOKEN = 4.0
OVERHEAD_PER_MESSAGE = 20  # structural JSON overhead per entry


def estimate_tokens(text: str) -> int:
    """Estimate token count from text using ~4 chars/token heuristic."""
    if not text:
        return 0
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def estimate_tokens_from_size(size_bytes: int) -> int:
    """Estimate tokens from file size in bytes."""
    return max(1, int(size_bytes / CHARS_PER_TOKEN))
