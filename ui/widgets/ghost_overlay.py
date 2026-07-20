"""
幽灵覆盖层（AgentCN）：透明置顶动画窗口
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QBrush

class GhostOverlay(QWidget):
    animation_done = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, 30, 30)
        self.step = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def animate_click(self, x, y):
        self.move(x-15, y-15)
        self.show()
        self.step = 0
        self.timer.start(50)

    def _tick(self):
        self.step += 1
        if self.step > 10:
            self.timer.stop()
            self.hide()
            self.animation_done.emit()
        else:
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        alpha = max(0, 200 - self.step * 20)
        p.setBrush(QBrush(QColor(255, 100, 100, alpha)))
        p.setPen(Qt.NoPen)
        r = max(2, 15 - self.step)
        p.drawEllipse(self.rect().center(), r, r)