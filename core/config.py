"""
全局配置管理：统一管理路径、模型地址等（AgentCN v0.0.2607）
"""
import os, json

CONFIG_FILE = os.path.join(os.path.expanduser("~/.agentcn"), "config.json")    # 配置目录改为 .agentcn

DEFAULT_CONFIG = {
    "llama_base_url": "http://localhost:8080",
    "projects_dir": os.path.join(os.path.expanduser("~"), "AgentCNProjects"),  # 默认项目目录
    "max_memory_entries": 1000,
    "max_context_chars": 2000
}

def load_config() -> dict:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return {**DEFAULT_CONFIG, **cfg}