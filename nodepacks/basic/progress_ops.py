import time
from typing import Callable, Optional


class _ProgressReporter:
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


class ProgressOpp:
    def __init__(self):
        self._progress_reporter = _ProgressReporter()

    def __call__(self, count: int) -> int:
        """
        Process items with progress reporting.

        Args:
            count: Number of items to process

        Returns:
            Sum of processed items
        """
        results = []
        for i in range(count):
            time.sleep(5)
            results.append(i * 2)
            self._progress_reporter.update(
                i + 1, count, f"Processing item {i + 1}/{count}"
            )
        return sum(results)
