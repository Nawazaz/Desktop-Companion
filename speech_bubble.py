"""
SpeechBubble — a small floating, translucent bubble with a pointer tail,
shown above the companion whenever it has something to say. Auto-hides
after a few seconds (longer messages stay up a bit longer).
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPainterPath

MAX_WIDTH = 240
BUBBLE_COLOR = QColor(255, 255, 255, 235)
BORDER_COLOR = QColor(210, 210, 215, 255)
TEXT_COLOR = "#2a2a35"
TAIL_HEIGHT = 12


class SpeechBubble(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 13px; background: transparent;")
        self.label.setMaximumWidth(MAX_WIDTH - 24)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10 + TAIL_HEIGHT)
        layout.addWidget(self.label)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        body_rect = self.rect().adjusted(0, 0, 0, -TAIL_HEIGHT)
        path = QPainterPath()
        path.addRoundedRect(body_rect, 14, 14)

        # pointer tail at the bottom-center, aimed down at the character
        cx = self.width() / 2
        tail = QPainterPath()
        tail.moveTo(cx - 8, body_rect.bottom())
        tail.lineTo(cx + 8, body_rect.bottom())
        tail.lineTo(cx, body_rect.bottom() + TAIL_HEIGHT)
        tail.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(BUBBLE_COLOR)
        painter.drawPath(path)
        painter.drawPath(tail)

        painter.setPen(BORDER_COLOR)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    def show_message(self, text: str, anchor_x: int, anchor_y: int):
        """anchor_x/anchor_y = the screen position of the TOP-CENTER of the
        character sprite - the bubble positions itself just above that point,
        centered horizontally on it."""
        self.label.setText(text)
        self.adjustSize()

        x = anchor_x - self.width() // 2
        y = anchor_y - self.height()
        self.move(x, y)
        self.show()
        self.raise_()

        # keep short replies up for a few seconds, longer ones a bit longer
        duration_ms = min(4000 + len(text) * 40, 12000)
        self.hide_timer.start(duration_ms)
