from typing import Callable, Optional


class ProgressReporter:
    """Context-aware progress reporter for node execution."""

    def __init__(self):
        self._callback: Optional[Callable[[float, str], None]] = None

    def set_callback(self, callback: Callable[[float, str], None]):
        """Set the callback for progress updates."""
        self._callback = callback

    def update(self, current: int, total: int, message: str = ""):
        """Report progress."""
        if self._callback:
            progress = current / total if total > 0 else 0
            self._callback(progress, message)

    def update_percent(self, percent: float, message: str = ""):
        """Report progress as percentage (0.0 to 1.0)."""
        if self._callback:
            self._callback(percent, message)


class StreamReporter:
    """Context-aware stream reporter for streaming text content."""

    def __init__(self):
        self._callback: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Callable[[str], None]):
        """Set the callback for stream updates."""
        self._callback = callback

    def emit(self, chunk: str):
        """Emit a text chunk to the stream."""
        if self._callback and chunk:
            self._callback(chunk)
