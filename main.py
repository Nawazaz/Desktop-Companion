"""
Desktop Companion — main application.

A frameless, always-on-top, translucent character that floats on the
desktop, can be dragged, chats via an LLM brain, shows mood on its face,
and lives in the system tray.
"""
import sys
import os
import re

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QSystemTrayIcon, QMenu, QStyle
)
from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtCore import Qt, QPoint

from llm_brain import CompanionBrain
from app_launcher import open_app
from speech_bubble import SpeechBubble
from pomodoro import PomodoroTimer
from settings_window import SettingsDialog

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OPEN_PATTERN = re.compile(r"^\s*open\s+(.+)$", re.IGNORECASE)
EXIT_WORDS = {"exit", "quit", "close", "exit app", "quit app", "close app"}
SIMPLE_TIMER_PATTERN = re.compile(
    r"^\s*start\s+(?:a\s+)?timer"
    r"(?:\s+(?:for\s+)?(\d+)\s*(?:min(?:utes)?)?)?"
    r"\s*$",
    re.IGNORECASE,
)
POMODORO_PATTERN = re.compile(
    r"^\s*start\s+(?:a\s+)?(?:pomodoro|study\s+session)"
    r"(?:\s+(?:for\s+)?(\d+)(?:\s*(?:min(?:utes)?)?)?)?"
    r"(?:\s*[/,]?\s*(\d+)\s*(?:min(?:utes)?)?\s*break)?"
    r"\s*$",
    re.IGNORECASE,
)
STOP_TIMER_PATTERN = re.compile(r"^\s*(?:stop|cancel)\s+(?:the\s+)?(?:pomodoro|timer)\s*$", re.IGNORECASE)

# Layout constants - keep these in sync with the actual sprite PNG size.
# If you regenerate sprites at a different resolution, update SPRITE_SIZE
# to match, and everything else below adjusts automatically.
SPRITE_SIZE = 200
TOP_MARGIN = 5
TIMER_LABEL_HEIGHT = 24
INPUT_HEIGHT = 32
WINDOW_WIDTH = SPRITE_SIZE + 20          # a little breathing room each side
WINDOW_HEIGHT = TOP_MARGIN + SPRITE_SIZE + TIMER_LABEL_HEIGHT + INPUT_HEIGHT + 10


def force_quit():
    """QApplication.quit() only stops the Qt event loop - it doesn't kill
    background threads spun up by chromadb/onnxruntime, which can leave the
    process hanging. os._exit() forces an immediate, unconditional exit."""
    os._exit(0)


class Companion(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._drag_pos = None

        self.brain = CompanionBrain()

        # position near bottom-right of the screen on first launch
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - WINDOW_WIDTH - 40, screen.height() - WINDOW_HEIGHT - 60)

        sprite_x = (WINDOW_WIDTH - SPRITE_SIZE) // 2
        self.sprite = QLabel(self)
        self.sprite.setGeometry(sprite_x, TOP_MARGIN, SPRITE_SIZE, SPRITE_SIZE)
        self.set_mood("idle")

        self.close_btn = QPushButton("X", self)
        self.close_btn.setGeometry(WINDOW_WIDTH - 30, TOP_MARGIN, 25, 25)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 100);
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(0, 0, 0, 180); }
        """)
        self.close_btn.clicked.connect(force_quit)
        self.close_btn.raise_()

        self.timer_label = QLabel("", self)
        self.timer_label.setGeometry(10, TOP_MARGIN + SPRITE_SIZE, WINDOW_WIDTH - 20, TIMER_LABEL_HEIGHT)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px; background: transparent;")

        self.pomodoro = PomodoroTimer(
            on_tick=self._on_timer_tick,
            on_phase_change=self._on_timer_phase_change,
            on_finished=self._on_timer_finished,
        )
        self.timer_mode = "timer"  # "timer" or "pomodoro" - set whenever one is started

        self.input_box = QLineEdit(self)
        self.input_box.setGeometry(10, TOP_MARGIN + SPRITE_SIZE + TIMER_LABEL_HEIGHT, WINDOW_WIDTH - 20, INPUT_HEIGHT)
        self.input_box.setPlaceholderText("Say something, press Enter...")
        self.input_box.returnPressed.connect(self.send_message)

        self._setup_tray()
        self.bubble = SpeechBubble()
        self.settings_dialog = None
        self.show()

    # ---------- mood / sprite ----------

    def set_mood(self, mood):
        path = os.path.join(ASSETS_DIR, f"{mood}.png")
        if os.path.exists(path):
            self.sprite.setPixmap(QPixmap(path))
        else:
            print(f"Missing sprite: {path}")

    def say(self, text):
        """Show the companion's reply in a speech bubble above its head."""
        sprite_x = (WINDOW_WIDTH - SPRITE_SIZE) // 2
        top_center_local = QPoint(sprite_x + SPRITE_SIZE // 2, TOP_MARGIN)
        global_point = self.mapToGlobal(top_center_local)
        self.bubble.show_message(text, global_point.x(), global_point.y())

    # ---------- chat ----------

    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return
        self.input_box.clear()

        # "exit"/"quit"/"close" typed in chat fully quits the app
        if text.lower().strip() in EXIT_WORDS:
            print(f"You: {text}")
            print("Companion: Bye for now!")
            force_quit()
            return

        # "start pomodoro" / "start pomodoro 25/5 break" - work+break cycle
        match = POMODORO_PATTERN.match(text)
        if match:
            work_minutes = int(match.group(1)) if match.group(1) else 25
            break_minutes = int(match.group(2)) if match.group(2) else 5
            self.timer_mode = "pomodoro"
            self.pomodoro.start(work_minutes, break_minutes)
            print(f"You: {text}")
            print(f"Companion: Starting a {work_minutes} minute focus session!\n")
            return

        # "start timer 10" - plain countdown, no break, for anything (cooking,
        # workouts, breaks, whatever) not just studying
        match = SIMPLE_TIMER_PATTERN.match(text)
        if match:
            minutes = int(match.group(1)) if match.group(1) else 10
            self.timer_mode = "timer"
            self.pomodoro.start(minutes, break_minutes=0)
            print(f"You: {text}")
            print(f"Companion: Starting a {minutes} minute timer!\n")
            return

        # "stop timer" / "cancel pomodoro"
        if STOP_TIMER_PATTERN.match(text):
            was_running = self.pomodoro.is_running()
            self.pomodoro.stop()
            self.timer_label.setText("")
            self.set_mood("idle")
            print(f"You: {text}")
            msg = "Timer stopped." if was_running else "No timer was running."
            print(f"Companion: {msg}\n")
            self.say(msg)
            return

        # "open X" commands are handled directly - no LLM call, instant and reliable
        match = OPEN_PATTERN.match(text)
        if match:
            app_name = match.group(1).strip()
            self.set_mood("thinking")
            QApplication.processEvents()

            success, message = open_app(app_name)
            print(f"You: {text}")
            print(f"Companion: {message}\n")
            self.say(message)
            self.set_mood("happy" if success else "sleepy")
            return

        # otherwise, normal AI conversation
        self.set_mood("thinking")
        QApplication.processEvents()

        reply, mood = self.brain.chat(text)

        print(f"You: {text}")
        print(f"Companion ({mood}): {reply}\n")
        self.say(reply)
        self.set_mood(mood)

    # ---------- pomodoro timer ----------

    def _on_timer_phase_change(self, phase, minutes):
        if phase == "work":
            self.set_mood("timer")
            if self.timer_mode == "pomodoro":
                self.say(f"Focus time! {minutes} minutes, you've got this.")
            else:
                self.say(f"Timer started: {minutes} minutes.")
        else:  # break (pomodoro only - plain timers never reach this phase)
            self.set_mood("happy")
            self.say(f"Nice work! Take a {minutes} minute break.")

    def _on_timer_tick(self, remaining_seconds, phase):
        mins, secs = divmod(max(remaining_seconds, 0), 60)
        if self.timer_mode == "pomodoro":
            label = "Focus" if phase == "work" else "Break"
        else:
            label = "Timer"
        self.timer_label.setText(f"{label}: {mins:02d}:{secs:02d}")

    def _on_timer_finished(self):
        self.timer_label.setText("")
        self.set_mood("happy" if self.timer_mode == "timer" else "idle")
        if self.timer_mode == "pomodoro":
            self.say("Pomodoro complete! Great job today.")
        else:
            self.say("Time's up!")

    # ---------- settings ----------

    def open_settings(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog()
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    # ---------- system tray ----------

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        menu = QMenu()
        show_action = QAction("Show Companion", self)
        show_action.triggered.connect(self._show_and_raise)
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(force_quit)
        menu.addAction(show_action)
        menu.addAction(settings_action)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._show_and_raise()

    def _show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    # ---------- dragging ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def contextMenuEvent(self, event):
        """Right-clicking the character itself shows the same menu as the
        tray icon - the tray icon can be hard to find/hidden in the overflow
        arrow, so this is a more discoverable way to reach Settings/Quit."""
        menu = QMenu(self)
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(force_quit)
        menu.addAction(settings_action)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    companion = Companion()
    sys.exit(app.exec())
