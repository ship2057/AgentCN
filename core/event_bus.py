"""
事件总线：基于 PySide6 信号，用于线程安全通信（AgentCN）
"""
from PySide6.QtCore import QObject, Signal

class EventBus(QObject):
    new_chunk = Signal(str)          # 新 token
    error_occurred = Signal(str)     # 错误
    finished = Signal()              # 流结束
    ghost_click = Signal(int, int)   # 幽灵鼠标动画坐标

bus = EventBus()                     # 全局单例