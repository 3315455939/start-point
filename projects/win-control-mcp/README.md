# win-control —— 通用 Windows 操作员 MCP server

把你提的**任意需求**当场变成对 Windows 的操作。挂在已有 Claude Code CLI 上，
后端走 MCP → 多模态大模型（能看截图），全程本机运行。

## 设计：双引擎混合（为了"通用且稳"）
- **UI 自动化引擎（主力）**：用 Windows UI Automation 枚举当前窗口的控件（按钮/输入框/菜单…带名字+精确矩形）。
  模型按"名字"挑控件，server 点它真实矩形——不靠猜像素，标准桌面软件极少点歪。
- **视觉引擎（兜底）**：遇到画布/游戏/未暴露控件的界面，截屏给多模态模型看图决策点哪。

## 前置
- Windows 10/11，已装 Claude Code CLI（`claude --version` 正常）
- Python 3.10+（装 Claude Code 时通常已有；没有就 `winget install Python.Python.3.12`）

## 安装（PowerShell）
```powershell
cd C:\Users\你的用户名\win-control-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 注册到 Claude Code
```powershell
claude mcp add win-control -s user -- C:\Users\你的用户名\win-control-mcp\.venv\Scripts\python.exe C:\Users\你的用户名\win-control-mcp\server.py
claude mcp list        # 看到 win-control 为 connected 即成功
```

## 工具清单
| 工具 | 作用 | 引擎 |
|------|------|------|
| `list_windows()` | 列出所有窗口标题 | — |
| `focus_window(title)` | 把某窗口提到前台 | UI |
| `list_controls([title])` | 枚举窗口控件(id/类型/名字/矩形) | UI |
| `click_control(id/name)` | 按名字点真实控件矩形 | UI |
| `type_into(id/name, text)` | 向控件输入（中文走剪贴板） | UI |
| `click/double_click/right_click(x,y)` | 屏幕坐标点击 | 视觉兜底 |
| `type_text(text)` | 当前焦点输入（中文走剪贴板） | — |
| `hotkey(keys)` | 组合键 ctrl+c / win+r … | — |
| `scroll/drag` | 滚轮 / 拖拽 | 视觉兜底 |
| `screenshot([title])` | 截屏给模型看 | 视觉 |
| `read_clipboard()` | 读剪贴板文本 | — |
| `open_app(target)` | 启动程序 | — |
| `run_command(cmd)` | 跑命令行 | — |

## 通用使用范式（典型闭环）
1. `list_windows()` → 看有哪些窗口
2. `focus_window("微信")` → 前置目标窗口
3. `list_controls("微信")` → 拿到控件清单（带 id 和名字）
4. `click_control(name="文件传输助手")` 或 `type_into(name="搜索", text="张三")` → 操作
5. 遇到没暴露控件的界面 → `screenshot()` 让模型看图决定坐标，再用 `click(x,y)`

你只需用自然语言说需求，例如：
- "打开 Excel，新建工作簿，在 A1 写'销售额'，保存为 test.xlsx"
- "打开微信，给文件传输助手发'今晚开会'"
- "打开 Chrome 访问 baidu 并搜索天气"
- "把桌面截图里那个弹窗关掉"

## 注意事项
- **急停**：鼠标甩到屏幕左上角立即中止所有自动操作（FAILSAFE）。
- **中文输入**：全部走剪贴板粘贴，不依赖输入法，稳。
- **坐标点击不精确**：优先用 `click_control`/`type_into`（按名字），`click(x,y)` 仅作兜底。
- **部分软件屏蔽自动化**：银行/系统高危设置/游戏可能拦截 UI 自动化，此时退用 `screenshot` 视觉路线（精度略低）。
- **截图目录**：默认 `~/.win-control/shots`，可用 `WIN_CONTROL_SHOT_DIR` 改。
