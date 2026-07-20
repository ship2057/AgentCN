"""
命令行界面（AgentCN v0.0.2607）：chat, project, skill, workflow
"""
import argparse, asyncio, os, logging
from services.llama_stream import LlamaStream
from core.plugin_loader import load_plugins
from core.context_manager import ContextManager, save_current_project

logger = logging.getLogger(__name__)

async def chat_command(message: str, interactive: bool = False):
    if interactive:
        print("AgentCN interactive chat (type /exit to quit)")
        while True:
            msg = input("You: ").strip()
            if msg == "/exit":
                break
            await _chat_once(msg)
    else:
        await _chat_once(message)

async def _chat_once(message: str):
    async with LlamaStream() as s:
        if not await s.health_check():
            print("LLaMA offline")
            return
        print("Assistant: ", end="", flush=True)
        async for token in s.stream_chat(message):
            print(token, end="", flush=True)
        print()

def project_command(args):
    if args.action == "create":
        os.makedirs(args.path, exist_ok=True)
        print(f"Created: {args.path}")
    elif args.action == "switch":
        if os.path.isdir(args.path):
            save_current_project(args.path)
            print(f"Switched to {args.path}")
        else:
            print("Path does not exist")

def skill_command(args):
    cm = ContextManager(args.project or os.getcwd())
    if args.action == "export":
        cm.export_skill(args.name)
        print(f"Skill '{args.name}' exported.")
    elif args.action == "dispatch":
        ok = cm.load_skill(args.name)
        print("Loaded" if ok else "Skill not found")

def workflow_command(args):
    plugins = load_plugins()
    ghost = plugins.get("ghost_mouse")
    if ghost:
        res = ghost.execute({"yaml_path": args.yaml}, {"project_path": args.project or os.getcwd()})
        print(res)
    else:
        print("Plugin not found")

def run_cli():
    parser = argparse.ArgumentParser("agentcn")                           # 命令名改为 agentcn
    sub = parser.add_subparsers(dest="command")

    chat_parser = sub.add_parser("chat")
    chat_parser.add_argument("message", nargs="?", default="")
    chat_parser.add_argument("-i", "--interactive", action="store_true", help="交互式聊天")

    project_parser = sub.add_parser("project")
    project_parser.add_argument("action", choices=["create", "switch"])
    project_parser.add_argument("path")

    skill_parser = sub.add_parser("skill")
    skill_parser.add_argument("action", choices=["export", "dispatch"])
    skill_parser.add_argument("name")
    skill_parser.add_argument("--project")

    wf_parser = sub.add_parser("workflow")
    wf_parser.add_argument("yaml")
    wf_parser.add_argument("--project")

    args = parser.parse_args()
    if args.command == "chat":
        if args.interactive:
            asyncio.run(chat_command("", interactive=True))
        else:
            if not args.message:
                print("请提供消息或使用 -i 进入交互模式")
            else:
                asyncio.run(chat_command(args.message))
    elif args.command == "project":
        project_command(args)
    elif args.command == "skill":
        skill_command(args)
    elif args.command == "workflow":
        workflow_command(args)
    else:
        parser.print_help()