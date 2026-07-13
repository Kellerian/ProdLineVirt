"""Periodic tick scheduler for per-code transfer timing checks."""

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer


class CodeScheduler:
    """QTimer wrapper that invokes a callback on a fixed short tick interval.

    Used to poll code queue readiness (~10 ms) independently of ``spInterval``
    configured in widget UI.
    """

    SCHEDULER_TICK_MS: int = 10

    def __init__(self) -> None:
        """Initialize the internal timer with the default tick interval."""
        self._timer = QTimer()
        self._timer.setInterval(self.SCHEDULER_TICK_MS)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._callback: Callable[[], None] | None = None

    def start(self, process_callback: Callable[[], None]) -> None:
        """Connect ``process_callback`` and start periodic ticks.

        If a callback was already connected, it is replaced before ticking
        resumes.

        :param process_callback: Callable invoked on each timer timeout.
        """
        if self._callback is not None:
            self._timer.timeout.disconnect(self._callback)
        self._callback = process_callback
        self._timer.timeout.connect(process_callback)
        self._timer.start()

    def stop(self) -> None:
        """Stop periodic ticks and disconnect the active callback."""
        self._timer.stop()
        if self._callback is not None:
            self._timer.timeout.disconnect(self._callback)
            self._callback = None
