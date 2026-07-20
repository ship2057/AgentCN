"""
屏幕脉冲插件（AgentCN）：截图 OCR + UIA 树，多平台适配
"""
import json, os, platform
from PIL import ImageGrab, Image
import pytesseract
import uiautomation as auto
from plugins.base import IPlugin

# 按需配置 Tesseract 路径
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ScreenPulsePlugin(IPlugin):
    @property
    def name(self) -> str:
        return "screen_pulse"

    def execute(self, params: dict, context: dict) -> str:
        mode = params.get("mode", "full")
        out_dir = context.get("project_path", os.getcwd())
        snap_path = os.path.join(out_dir, "screen_snapshot.json")

        try:
            if mode == "full":
                if platform.system() == "Windows":
                    img = ImageGrab.grab()
                elif platform.system() == "Darwin":
                    import subprocess
                    tmp = os.path.join(out_dir, "tmp_screenshot.png")
                    subprocess.call(["screencapture", "-x", tmp])
                    img = Image.open(tmp)
                    os.remove(tmp)
                else:
                    return "Full screenshot not supported on this OS"
            else:
                win = auto.GetForegroundControl()
                if not win:
                    return "No foreground window found"
                rect = win.BoundingRectangle
                full = ImageGrab.grab()
                img = full.crop((rect.left, rect.top, rect.right, rect.bottom))
        except Exception as e:
            return f"Screenshot error: {e}"

        lang = 'eng'
        try:
            if 'chi_sim' in pytesseract.get_languages():
                lang = 'eng+chi_sim'
        except:
            pass

        try:
            text = pytesseract.image_to_string(img, lang=lang)
        except pytesseract.TesseractNotFoundError:
            return "Tesseract not installed or not in PATH."
        except Exception as e:
            return f"OCR error: {e}"

        tree = self._tree()
        snap = {"mode": mode, "ocr_text": text.strip(), "controls": tree}
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2, ensure_ascii=False)
        return f"Snapshot saved to {snap_path}"

    def _tree(self, max_depth=5):
        def traverse(c, d):
            if d > max_depth:
                return None
            try:
                node = {
                    "type": c.ControlTypeName or "?",
                    "name": c.Name or "",
                    "class": c.ClassName or "",
                    "rect": {"l": c.BoundingRectangle.left, "t": c.BoundingRectangle.top,
                             "w": c.BoundingRectangle.width(), "h": c.BoundingRectangle.height()}
                }
                kids = []
                for ch in c.GetChildren():
                    kid = traverse(ch, d+1)
                    if kid:
                        kids.append(kid)
                if kids:
                    node["children"] = kids
                return node
            except:
                return None
        root = auto.GetRootControl()
        return traverse(root, 0) or {}