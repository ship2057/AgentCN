"""
上下文管理器：项目隔离、记忆存储、技能管理（AgentCN v0.0.2607）
"""
import os, json, shutil
from typing import List, Optional
from datetime import datetime
from core.config import load_config

AGENTCN_HOME = os.path.expanduser("~/.agentcn")            # 改为 .agentcn
SKILLS_DIR = os.path.join(AGENTCN_HOME, "skills")
PROJECTS_CONFIG = os.path.join(AGENTCN_HOME, "current_project.json")

class ContextManager:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.agent_dir = os.path.join(self.project_path, ".agent")
        os.makedirs(self.agent_dir, exist_ok=True)
        self.config = load_config()

    # ---------- 记忆读写 ----------
    def get_compressed_context(self, max_chars: int = None) -> str:
        if max_chars is None:
            max_chars = self.config.get("max_context_chars", 2000)
        memory_file = os.path.join(self.agent_dir, "memory.jsonl")
        if not os.path.exists(memory_file):
            return ""
        context = ""
        with open(memory_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):            # 最新优先
            try:
                mem = json.loads(line)
            except json.JSONDecodeError:
                continue
            summary = mem.get("summary", "")
            if len(context) + len(summary) > max_chars:
                break
            context = summary + "\n" + context
        return context.strip()

    def append_memory(self, summary: str, keywords: List[str], files: Optional[List[str]] = None) -> None:
        memory_file = os.path.join(self.agent_dir, "memory.jsonl")
        entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "keywords": keywords,
            "files": files or []
        }
        max_entries = self.config.get("max_memory_entries", 1000)
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) >= max_entries:
                archive_dir = os.path.join(self.agent_dir, "archives")
                os.makedirs(archive_dir, exist_ok=True)
                archive_name = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jsonl"
                archive_path = os.path.join(archive_dir, archive_name)
                with open(archive_path, "a", encoding="utf-8") as af:
                    af.writelines(lines[:len(lines)//2])
                with open(memory_file, "w", encoding="utf-8") as wf:
                    wf.writelines(lines[len(lines)//2:])
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ---------- 技能管理 ----------
    def export_skill(self, skill_name: str) -> str:
        os.makedirs(SKILLS_DIR, exist_ok=True)
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if os.path.exists(skill_dir):
            shutil.rmtree(skill_dir)
        shutil.copytree(self.agent_dir, skill_dir)
        return skill_dir

    def load_skill(self, skill_name: str) -> bool:
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.exists(skill_dir):
            return False
        for root, dirs, files in os.walk(skill_dir):
            rel_path = os.path.relpath(root, skill_dir)
            target_dir = self.agent_dir if rel_path == "." else os.path.join(self.agent_dir, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(target_dir, file)
                shutil.copy2(src, dst)
        return True

def save_current_project(project_path: str):
    os.makedirs(AGENTCN_HOME, exist_ok=True)
    with open(PROJECTS_CONFIG, "w", encoding="utf-8") as f:
        json.dump({"current_project": project_path}, f)

def load_current_project() -> str:
    if os.path.exists(PROJECTS_CONFIG):
        try:
            with open(PROJECTS_CONFIG, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("current_project", os.getcwd())
        except:
            pass
    return os.getcwd()