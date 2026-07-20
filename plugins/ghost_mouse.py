"""
幽灵鼠标插件（AgentCN）：YAML 工作流，带焦点恢复和重试
"""
import yaml, time
from plugins.base import IPlugin
import uiautomation as auto
from core.event_bus import bus

class GhostMousePlugin(IPlugin):
    @property
    def name(self) -> str:
        return "ghost_mouse"

    def execute(self, params: dict, context: dict) -> str:
        yaml_path = params.get("yaml_path", "")
        if not yaml_path:
            return "No yaml_path"
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                steps = yaml.safe_load(f)
        except Exception as e:
            return f"YAML error: {e}"
        if not isinstance(steps, list):
            return "Invalid format"

        for step in steps:
            action = step.get("action")
            target = step.get("target", {})
            try:
                if action == "click":
                    self._click(target)
                elif action == "type":
                    self._type(target, step.get("text", ""))
                elif action == "wait":
                    time.sleep(step.get("seconds", 1))
                else:
                    pass
            except Exception as e:
                return f"Step error: {e}"
        return "Workflow done"

    def _find_control(self, target: dict):
        for attempt in range(5):
            try:
                depth = target.get("depth", 10) + attempt
                c = auto.Control(Depth=depth,
                                 ClassName=target.get("class_name", ""),
                                 Name=target.get("name", ""))
                if c.Exists(2):
                    try:
                        top = c.GetTopLevelControl()
                        if top:
                            top.SetFocus()
                            time.sleep(0.1)
                    except:
                        pass
                    return c
            except:
                time.sleep(0.5)
        raise RuntimeError(f"Control not found: {target}")

    def _click(self, target):
        c = self._find_control(target)
        rect = c.BoundingRectangle
        x = rect.left + rect.width() // 2
        y = rect.top + rect.height() // 2
        bus.ghost_click.emit(x, y)
        c.Click()
        time.sleep(0.2)

    def _type(self, target, text):
        c = self._find_control(target)
        c.Click()
        c.SendKeys(text)