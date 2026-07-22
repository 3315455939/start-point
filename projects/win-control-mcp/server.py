"""
win-control —— 通用 Windows 操作员 MCP server（挂到 Claude Code CLI）
设计目标：用户提任意需求，当场执行，不预设具体软件。
双引擎混合：
  1) UI 自动化引擎（主力）：用 Windows UI Automation 枚举窗口控件（名字+精确矩形），
     模型按"名字"挑控件，点它真实矩形，不靠猜像素。覆盖标准桌面软件。
  2) 视觉引擎（兜底）：遇到画布/游戏/未暴露控件的界面，截图给多模态模型看图决策。
后端模型：多模态大模型（支持图片），经 MCP 接 Claude Code。
依赖：mcp, pyautogui, pygetwindow, Pillow, uiautomation, pyperclip
"""

import os
import subprocess
from pathlib import Path
import time

import pyautogui
import pygetwindow as gw
import pyperclip
import uiautomation as auto
from PIL import Image as PILImage
from mcp.server.fastmcp import FastMCP, Image

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

mcp = FastMCP("win-control")

SHOT_DIR = Path(os.environ.get("WIN_CONTROL_SHOT_DIR", str(Path.home() / ".win-control" / "shots")))
SHOT_DIR.mkdir(parents=True, exist_ok=True)

# 只关心可交互控件，避免枚举爆炸
INTERACTIVE = {
    "ButtonControl", "EditControl", "ComboBoxControl", "ListItemControl",
    "MenuItemControl", "HyperlinkControl", "CheckBoxControl", "RadioButtonControl",
    "TreeItemControl", "TabItemControl", "DocumentControl", "SliderControl",
    "PaneControl", "GroupControl",
}
MAX_CONTROLS = 300
MAX_DEPTH = 6


# ---------- 缓存 ----------
_controls_cache = {}  # key: str -> (monotonic_ts, (controls_list, id_to_obj_map))
_CACHE_TTL = 2.0  # 秒


def _cache_key(window_title: str) -> str:
    """生成缓存键；前台窗口用 NativeWindowHandle。"""
    if window_title:
        return window_title
    try:
        fg = auto.GetForegroundControl()
        return str(fg.NativeWindowHandle or "")
    except Exception:
        return ""


def _walk_controls(window_title: str):
    """一次遍历控件树，同时返回结构化列表和 id→控件对象 映射。
    带短 TTL 缓存，避免连续操作（list→click）重复遍历。"""
    key = _cache_key(window_title)
    now = time.monotonic()
    if key in _controls_cache:
        ts, cached = _controls_cache[key]
        if now - ts < _CACHE_TTL:
            return cached

    win = _resolve_window(window_title)
    out = []
    id_to_obj = {}
    counter = 0

    def walk(ctrl, depth):
        nonlocal counter
        if len(out) >= MAX_CONTROLS:
            return
        try:
            children = ctrl.GetChildren()
        except Exception:  # noqa: BLE001
            return
        for child in children:
            ctype = child.ControlTypeName
            if ctype in INTERACTIVE:
                r = child.BoundingRectangle
                out.append({
                    "id": counter,
                    "type": ctype,
                    "name": child.Name or "",
                    "rect": [r.left, r.top, r.right, r.bottom],
                })
                id_to_obj[counter] = child
                counter += 1
            if depth < MAX_DEPTH:
                walk(child, depth + 1)

    walk(win, 0)
    result = (out, id_to_obj)
    _controls_cache[key] = (now, result)
    return result


# ---------- 内部工具 ----------
def _resolve_window(window_title: str):
    """按标题找窗口；为空则返回前台窗口。"""
    if window_title:
        win = auto.WindowControl(searchDepth=1, SubName=window_title)
        if win.Exists(0, 0):
            return win
    return auto.GetForegroundControl()


def _find_control(controls, control_id, name, control_type):
    """在控件列表中按 id 或 名字+类型 匹配，返回控件信息 dict 或 None。"""
    if control_id is not None and control_id >= 0:
        for c in controls:
            if c["id"] == control_id:
                return c
    if name:
        nl = name.lower()
        for c in controls:
            if nl in (c["name"] or "").lower():
                if not control_type or control_type.lower() in c["type"].lower():
                    return c
    return None


def _paste_text(text: str):
    """用剪贴板粘贴文本（支持中文，不依赖输入法）。"""
    old = pyperclip.paste()
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    pyperclip.copy(old)


# ---------- 工具定义 ----------
@mcp.tool()
def list_windows() -> str:
    """列出当前所有打开的窗口标题，帮模型知道能操作什么。"""
    titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
    return "当前窗口:\n" + "\n".join(f"- {t}" for t in titles[:80])


@mcp.tool()
def focus_window(title: str) -> str:
    """按标题把某个窗口提到前台并聚焦。"""
    wins = gw.getWindowsWithTitle(title)
    if not wins:
        return f"未找到标题含 '{title}' 的窗口"
    win = wins[0]
    try:
        win.activate()
        time.sleep(0.3)  # 等窗口切到前台再返回
    except Exception as e:
        return f"聚焦失败: {e}"
    _controls_cache.clear()  # 窗口切换后缓存失效
    return f"已聚焦: {win.title}"


@mcp.tool()
def list_controls(window_title: str = "") -> str:
    """枚举目标窗口（默认前台窗口）里的可交互控件：返回 id / 类型 / 名字 / 矩形。
    模型据此按'名字'挑控件，再用 click_control / type_into 操作，避免靠截图猜坐标。"""
    controls, _ = _walk_controls(window_title)
    if not controls:
        return "未枚举到控件（该窗口可能未暴露 UI 自动化，或需先 focus_window）。"
    lines = [f"窗口控件（共 {len(controls)} 个）:"]
    for c in controls:
        l, t, r, b = c["rect"]
        lines.append(f"[{c['id']}] {c['type']} | 名字={c['name'] or '(无)'} | 矩形=({l},{t})-({r},{b})")
    return "\n".join(lines)


@mcp.tool()
def click_control(control_id: int = -1, name: str = "", control_type: str = "", window_title: str = "") -> str:
    """按 id 或 名字 点击某个控件（点它真实矩形，最稳）。优先用 id。"""
    controls, id_to_obj = _walk_controls(window_title)
    c = _find_control(controls, control_id, name, control_type)
    if not c:
        return f"没找到匹配的控件（id={control_id} name={name}）。可先 list_controls 看可用控件。"
    target = id_to_obj.get(c["id"])
    if not target:
        return "定位控件对象失败（控件可能已失效，请重新 list_controls）。"
    try:
        target.Click()
    except Exception as e:
        return f"点击控件失败: {e}"
    return f"已点击控件 [{c['id']}] {c['type']} '{c['name']}'"


@mcp.tool()
def type_into(control_id: int = -1, name: str = "", text: str = "", window_title: str = "") -> str:
    """把文本输入到指定控件（中文走剪贴板粘贴，最稳）。"""
    controls, id_to_obj = _walk_controls(window_title)
    c = _find_control(controls, control_id, name, "")
    if not c:
        return f"没找到目标控件（id={control_id} name={name}）。"
    target = id_to_obj.get(c["id"])
    if not target:
        return "定位控件对象失败（控件可能已失效，请重新 list_controls）。"
    try:
        target.SetFocus()
    except Exception as e:
        return f"聚焦控件失败: {e}"
    _paste_text(text)
    return f"已向控件 [{c['id']}] '{c['name']}' 输入: {text[:60]}"


@mcp.tool()
def click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """在屏幕坐标 (x,y) 点击（视觉兜底用，精确目标优先用 click_control）。"""
    pyautogui.click(x=x, y=y, button=button, clicks=clicks)
    return f"已在 ({x},{y}) 用 {button} 点击 {clicks} 次"


@mcp.tool()
def double_click(x: int, y: int) -> str:
    """双击屏幕坐标。"""
    pyautogui.doubleClick(x=x, y=y)
    return f"已在 ({x},{y}) 双击"


@mcp.tool()
def right_click(x: int, y: int) -> str:
    """右键点击屏幕坐标。"""
    pyautogui.rightClick(x=x, y=y)
    return f"已在 ({x},{y}) 右键"


@mcp.tool()
def type_text(text: str) -> str:
    """在当前焦点处输入文本（中文走剪贴板粘贴）。"""
    _paste_text(text)
    return f"已输入: {text[:60]}"


@mcp.tool()
def hotkey(keys: str) -> str:
    """按组合键，如 'ctrl+c'、'win+r'、'alt+f4'。"""
    pyautogui.hotkey(*[k.strip() for k in keys.split("+")])
    return f"已按组合键: {keys}"


@mcp.tool()
def scroll(direction: str = "down", clicks: int = 3) -> str:
    """滚动鼠标滚轮。direction: down/up。"""
    pyautogui.scroll(-clicks if direction == "down" else clicks)
    return f"已向 {direction} 滚动 {clicks} 格"


@mcp.tool()
def drag(x1: int, y1: int, x2: int, y2: int) -> str:
    """从 (x1,y1) 拖到 (x2,y2)。"""
    pyautogui.moveTo(x1, y1)
    pyautogui.dragTo(x2, y2, duration=0.4)
    return f"已从 ({x1},{y1}) 拖到 ({x2},{y2})"


@mcp.tool()
def screenshot(window_title: str = "") -> Image:
    """截取全屏或指定窗口（视觉兜底用）。多模态模型可看图决定下一步。"""
    img = pyautogui.screenshot()
    if window_title:
        wins = gw.getWindowsWithTitle(window_title)
        if wins:
            try:
                win = wins[0]
                left, top = win.topleft
                width, height = win.size
                # 跳过最小化或屏幕外的窗口（topleft 可能是负几万）
                if left > -10000 and top > -10000 and width > 0 and height > 0:
                    img = img.crop((left, top, left + width, top + height))
            except Exception:  # noqa: BLE001
                pass  # 裁剪失败则保留全屏截图
    path = SHOT_DIR / "shot.png"
    img.save(path)
    return Image(path=str(path))


@mcp.tool()
def read_clipboard() -> str:
    """读取剪贴板当前文本内容。"""
    return pyperclip.paste() or "(空)"


@mcp.tool()
def open_app(target: str) -> str:
    """启动程序：target 可为 exe 路径或命令名（notepad / chrome / wechat ...）。"""
    if os.path.exists(target):
        subprocess.Popen([target])
        return f"已按路径启动: {target}"
    try:
        subprocess.Popen(target, shell=True)
        return f"已尝试启动命令: {target}"
    except Exception as e:  # noqa: BLE001
        return f"启动失败: {e}"


@mcp.tool()
def run_command(command: str, shell: bool = True) -> str:
    """在 PowerShell/CMD 执行命令并返回输出。"""
    try:
        proc = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=120)
        return f"[exit {proc.returncode}]\n{proc.stdout or ''}\n{proc.stderr or ''}"
    except Exception as e:  # noqa: BLE001
        return f"执行异常: {e}"


if __name__ == "__main__":
    mcp.run()
