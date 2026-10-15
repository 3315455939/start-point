个人自动化助理
===============

简介
----
这是一个桌面辅助工具集合，按前端/后端分层：

- 前端：`frontend/主页面.html`（浏览器）、`frontend/桌面整理（独立版）.html`（整理独立页）、`frontend/desktop_tool_gui.py`（Tkinter GUI）。
- 后端：`backend/` 包（详见下文）。
- 中控：`backend/controller.py`（命令行入口，调用 `backend` 模块）。

状态说明
----
已清理项目中的重复/过时副本：所有后端实现位于 `backend/`，所有前端资源位于 `frontend/`。

目录（重要文件）
-----------------

`frontend/desktop_tool_gui.py` — Tkinter GUI 前端，处理交互与展示，调用 `backend` 模块完成业务逻辑。
- `backend/controller.py` — CLI 中控，提供子命令 `weather` / `reminder` / `organizer`（可通过 `python -m backend.controller` 运行）。
- `backend/` — 后端功能包（唯一实现位置）：
   - `weather_module.py`：天气查询 + 历史存储（OpenWeatherMap）。
   - `reminder_module.py`：`ReminderManager`，提醒 CRUD、检查与通知。
   - `organizer_module.py`：桌面扫描、预览、整理与撤销；包含 favorites 持久化。
- `requirements.txt` — 依赖清单（requests, plyer, winshell）。
- `organize_desktop.bat` — Windows 批处理实现（参考/备用）。

运行
----

1. 安装依赖：

   pip install -r requirements.txt

2. 启动 GUI：

- 直接运行（推荐）：

  python frontend/desktop_tool_gui.py

- 或进入 `frontend/` 目录后运行：

  cd frontend
  python desktop_tool_gui.py

3. 使用命令行中控：

   python -m backend.controller weather --city 北京
   python -m backend.controller reminder list
   python -m backend.controller organizer preview

注意事项
---------

- 桌面整理会移动文件：运行前请备份桌面重要数据。
- 如果 `winshell` 无法安装或不可用，整理模块会回退到 `~/Desktop` 路径。
- `plyer` 的通知在不同平台上表现不同，GUI 同时使用弹窗以保证可见性。

后续建议
---------

- 将所有持久化路径与配置集中管理（便于测试与迁移）。
- 为整理功能提供“模拟/预览”模式（当前已有预览，但建议更突出）。
- 增加单元测试并使 `controller.py` 成为可安装的 CLI 包。
