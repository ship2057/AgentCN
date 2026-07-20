"""
技能管理插件（AgentCN）
"""
from plugins.base import IPlugin
from core.context_manager import ContextManager

class SkillManagerPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "skill_manager"

    def execute(self, params: dict, context: dict) -> str:
        action = params.get("action", "")
        project_path = context.get("project_path", "")
        if not project_path:
            return "Error: no project path in context"
        cm = ContextManager(project_path)
        if action == "export":
            name = params.get("skill_name", "")
            if not name:
                return "Error: skill_name required"
            path = cm.export_skill(name)
            return f"Skill '{name}' exported to {path}"
        elif action == "dispatch":
            name = params.get("skill_name", "")
            if not name:
                return "Error: skill_name required"
            ok = cm.load_skill(name)
            return f"Skill '{name}' loaded" if ok else f"Skill '{name}' not found"
        else:
            return f"Unknown action: {action}"