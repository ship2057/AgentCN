"""
AgentCN v0.0.2607 入口模块：解析命令行，启动 GUI 或 CLI
"""
import sys
import logging

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    if "--cli" in sys.argv:                         # CLI 模式
        from cli.agent_cli import run_cli            # 导入 CLI 入口
        run_cli()
    else:                                           # GUI 模式
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()