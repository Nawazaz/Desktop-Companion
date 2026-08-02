"""
PomodoroTimer — counts down a work session, then a break session, ticking
once per second. Decoupled from the UI: you give it callback functions and
it calls them; it doesn't know about the companion window at all.
"""
from PySide6.QtCore import QObject, QTimer


class PomodoroTimer(QObject):
    def __init__(self, on_tick, on_phase_change, on_finished):
        """
        on_tick(remaining_seconds: int, phase: str) - called every second
        on_phase_change(phase: str, minutes: int) - called when work->break or start
        on_finished() - called when the whole work+break cycle completes
        """
        super().__init__()
        self.on_tick = on_tick
        self.on_phase_change = on_phase_change
        self.on_finished = on_finished

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        self.remaining = 0
        self.phase = None  # "work" or "break"
        self.break_minutes = 5

    def start(self, work_minutes: int = 25, break_minutes: int = 0):
        """break_minutes=0 means: just a plain countdown, no break phase after."""
        self.break_minutes = break_minutes
        self.phase = "work"
        self.remaining = work_minutes * 60
        self.on_phase_change("work", work_minutes)
        self.timer.start(1000)

    def stop(self):
        self.timer.stop()
        self.phase = None

    def is_running(self):
        return self.timer.isActive()

    def _tick(self):
        self.remaining -= 1
        self.on_tick(self.remaining, self.phase)

        if self.remaining <= 0:
            if self.phase == "work" and self.break_minutes > 0:
                self.phase = "break"
                self.remaining = self.break_minutes * 60
                self.on_phase_change("break", self.break_minutes)
            else:
                self.timer.stop()
                self.phase = None
                self.on_finished()