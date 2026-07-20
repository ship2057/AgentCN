"""
动态插件加载器：支持热重载（AgentCN 开发模式）
"""
import os, sys, importlib, inspect
from typing import Dict
from plugins.base import IPlugin

def load_plugins(reload: bool = False) -> Dict[str, IPlugin]:
    plugins: Dict[str, IPlugin] = {}
    plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
    if not os.path.exists(plugin_dir):
        return plugins
    for filename in os.listdir(plugin_dir):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        module_name = filename[:-3]
        full_name = f"plugins.{module_name}"
        if reload and full_name in sys.modules:
            del sys.modules[full_name]
        try:
            module = importlib.import_module(full_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, IPlugin) and obj is not IPlugin:
                    instance = obj()
                    plugins[instance.name] = instance
        except Exception as e:
            print(f"Plugin {module_name} load failed: {e}")
    return plugins