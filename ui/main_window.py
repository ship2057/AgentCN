"""
主窗口（AgentCN v0.0.2607）：项目树、聊天、输入，非阻塞健康检查，QSS 加载
"""
import os, time, logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QTreeWidget, QTreeWidgetItem, QLineEdit, QPushButton,
                               QStatusBar, QLabel)
from PySide6.QtCore import Qt, QThread, Signal
from core.event_bus import bus
from core.config import load_config
from ui.widgets.chat_display import ChatDisplay
from ui.widgets.ghost_overlay import GhostOverlay
from services.llama_stream import LlamaStream
from core.plugin_loader import load_plugins
from core.context_manager import ContextManager, save_current_project, load_current_project

logger = logging.getLogger(__name__)

class HealthCheckWorker(QThread):
    result_signal = Signal(bool)
    def run(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async def check():
                try:
                    async with LlamaStream() as s:
                        return await s.health_check()
                except:
                    return False
            ok = loop.run_until_complete(check())
        except:
            ok = False
        finally:
            loop.close()
        self.result_signal.emit(ok)

class StreamWorker(QThread):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def run(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._stream())
        except Exception as e:
            bus.error_occurred.emit(str(e))
        finally:
            loop.close()
            bus.finished.emit()

    async def _stream(self):
        try:
            async with LlamaStream() as stream:
                if not await stream.health_check():
                    bus.error_occurred.emit("LLaMA offline")
                    return
                async for token in stream.stream_chat(self.message):
                    bus.new_chunk.emit(token)
        except Exception as e:
            bus.error_occurred.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.setWindowTitle("AgentCN v0.0.2607")                       # 窗口标题改为 AgentCN v0.0.2607
        self.resize(1000, 700)
        self.plugins = load_plugins()
        self.current_project_path = load_current_project()
        self.context_manager = ContextManager(self.current_project_path)
        self.char_count = 0
        self.stream_start_time = 0.0
        self.ghost_overlay = GhostOverlay()
        self.active_workers = set()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Projects")
        self.project_tree.setMaximumWidth(200)
        self._populate_projects()
        self.project_tree.itemClicked.connect(self._on_project_clicked)
        main_layout.addWidget(self.project_tree)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.chat_display = ChatDisplay()
        right_layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入消息或 /命令")
        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self.send_message)
        self.speed_label = QLabel("速度: 0 chars/s")
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(self.speed_label)
        right_layout.addLayout(input_layout)

        main_layout.addWidget(right_widget)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("离线")

        bus.new_chunk.connect(self.on_new_chunk)
        bus.error_occurred.connect(self.on_error)
        bus.finished.connect(self.on_finished)
        bus.ghost_click.connect(self._on_ghost_click)

        self.health_worker = HealthCheckWorker()
        self.health_worker.result_signal.connect(self._update_health_status)
        self.health_worker.start()

        self._load_qss()

    def _load_qss(self):
        qss_path = os.path.join(os.path.dirname(__file__), "resources", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _populate_projects(self):
        self.project_tree.clear()
        added = set()
        added.add(os.path.abspath(self.current_project_path))
        current_item = QTreeWidgetItem(self.project_tree, [os.path.basename(self.current_project_path)])
        current_item.setData(0, Qt.UserRole, self.current_project_path)
        current_item.setSelected(True)

        projects_dir = self.config.get("projects_dir", "")
        if projects_dir and os.path.isdir(projects_dir):
            for entry in os.listdir(projects_dir):
                full = os.path.join(projects_dir, entry)
                if os.path.isdir(full) and os.path.abspath(full) not in added:
                    item = QTreeWidgetItem(self.project_tree, [entry])
                    item.setData(0, Qt.UserRole, full)
                    added.add(os.path.abspath(full))

    def _on_project_clicked(self, item, col):
        path = item.data(0, Qt.UserRole)
        if path and os.path.isdir(path):
            self.current_project_path = path
            self.context_manager = ContextManager(path)
            save_current_project(path)
            self.status.showMessage(f"当前项目: {os.path.basename(path)}", 3000)

    def _update_health_status(self, online: bool):
        self.status.showMessage("在线" if online else "离线")

    def send_message(self):
        text = self.input_line.text().strip()
        if not text:
            return
        if text.startswith("/"):
            self._execute_command(text)
            self.input_line.clear()
        else:
            self._stop_active_workers()
            self.chat_display.append_user(text)
            self.input_line.clear()
            self.char_count = 0
            self.stream_start_time = time.time()
            worker = StreamWorker(text)
            worker.finished.connect(lambda w=worker: self._worker_done(w))
            self.active_workers.add(worker)
            worker.start()

    def _stop_active_workers(self):
        for w in list(self.active_workers):
            if w.isRunning():
                w.terminate()
                w.wait()
            self.active_workers.discard(w)

    def _worker_done(self, worker):
        self.active_workers.discard(worker)

    def _execute_command(self, text: str):
        parts = text[1:].strip().split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1] if len(parts) > 1 else ""
        ctx = {"project_path": self.current_project_path}

        if cmd == "search" and arg:
            p = self.plugins.get("web_search")
            if p:
                self.chat_display.append_user(f"/search {arg}")
                self.chat_display.append_assistant_message(p.execute({"query": arg}, ctx))
        elif cmd == "skill" and arg:
            sub = arg.split(maxsplit=1)
            action, name = sub[0], sub[1] if len(sub)>1 else ""
            p = self.plugins.get("skill_manager")
            if p:
                self.chat_display.append_user(f"/skill {action} {name}")
                self.chat_display.append_assistant_message(p.execute({"action": action, "skill_name": name}, ctx))
        elif cmd == "workflow" and arg:
            p = self.plugins.get("ghost_mouse")
            if p:
                self.chat_display.append_user(f"/workflow {arg}")
                self.chat_display.append_assistant_message(p.execute({"yaml_path": arg}, ctx))
        elif cmd == "screen":
            mode = arg if arg in ("window", "full") else "full"
            p = self.plugins.get("screen_pulse")
            if p:
                self.chat_display.append_user(f"/screen {mode}")
                self.chat_display.append_assistant_message(p.execute({"mode": mode}, ctx))
        else:
            self.chat_display.append_assistant_message(f"未知命令: /{cmd}")

    def on_new_chunk(self, chunk: str):
        self.chat_display.append_assistant_chunk(chunk)
        self.char_count += len(chunk)
        elapsed = time.time() - self.stream_start_time
        if elapsed > 0:
            speed = self.char_count / elapsed
            self.speed_label.setText(f"速度: {speed:.1f} chars/s")

    def on_error(self, msg: str):
        self.chat_display.append_assistant_message(f"\n[错误] {msg}")

    def on_finished(self):
        self.chat_display.append_assistant_chunk("\n")
        self.status.showMessage("在线")

    def _on_ghost_click(self, x, y):
        self.ghost_overlay.animate_click(x, y)