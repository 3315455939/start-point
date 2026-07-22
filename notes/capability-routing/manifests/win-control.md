# win-control MCP

仅用于：用户明确要求 Windows 桌面操控（打开应用、点击窗口、截图、输入文本、剪贴板操作）。
不要用于：后台自动化、批量无确认操作、未明确授权的窗口操控。

## 基本信息

- **能力 ID:** win-control
- **名称:** Windows 桌面操控 MCP Server
- **类型:** MCP
- **平台:** Claude Code
- **来源:** 本地 MCP 项目（`win-control-mcp`）
- **能力槽:** 控制 Windows 窗口/点击/输入/截图/剪贴板/应用启动

## 存储决策

- **资产管理:** mcp-config
- **管理状态:** active（触发收窄）
- **健康状态:** healthy
- **风险:** medium（可操作桌面 UI、读写剪贴板）
- **隔离:** 否
- **依赖:** Windows 原生 UI Automation

## 路由

- **触发条件:** 用户明确说"打开/点击/截图/窗口/输入"等桌面操作关键词
- **禁用条件:** 勿用于后台自动化、批量操作、未确认的窗口操控
- **替代方案:** 无直接替代（唯一桌面操控入口）
- **Registry 条目:** `registry/level2-registry.md#win-control`
- **总管型标记:** 是（16 工具全量可见，需截断安全改写）

## 激活

- **激活方式:** MCP Server 已配置，会话启动自动连接
- **停用方式:** 从 MCP 配置中移除
- **回滚方式:** 重新添加 MCP 配置

## 工具清单（16个）

`click`, `click_control`, `double_click`, `drag`, `focus_window`, `hotkey`, `list_controls`, `list_windows`, `open_app`, `read_clipboard`, `right_click`, `run_command`, `screenshot`, `scroll`, `type_into`, `type_text`

## 安全

- **License:** 自有项目
- **权限范围:** Windows UI Automation、剪贴板读写、进程启动、PowerShell 执行
- **是否涉及凭据:** 否
- **副作用:** 可修改桌面状态、执行命令、读写剪贴板
