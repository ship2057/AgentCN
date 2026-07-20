"""
聊天显示组件（AgentCN）：流式更新，自动前缀
"""
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

class ChatDisplay(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 11))
        self.setStyleSheet("color: #d4d4d4; background-color: #1e1e1e;")
        self._assistant_started = False

    def append_user(self, text: str):
        self._assistant_started = False
        self.moveCursor(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#569cd6"))
        cursor = self.textCursor()
        cursor.insertText(f"You: {text}\n", fmt)
        self.ensureCursorVisible()

    def append_assistant_message(self, text: str):
        self._assistant_started = False
        self.moveCursor(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#d4d4d4"))
        cursor = self.textCursor()
        cursor.insertText(f"Agent: {text}\n", fmt)
        self.ensureCursorVisible()

    def append_assistant_chunk(self, chunk: str):
        self.moveCursor(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#d4d4d4"))
        cursor = self.textCursor()
        if not self._assistant_started:
            cursor.insertText("Agent: ", fmt)
            self._assistant_started = True
        cursor.insertText(chunk, fmt)
        self.ensureCursorVisible()