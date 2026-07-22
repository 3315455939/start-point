# Level 2 Registry / 二级注册表

> 每个可路由能力一行。Agent 从 L1 命中类别后，只读本表命中行，再只读一张 L3 能力卡。

## Registry Rows

### baseline-direct

- **ID:** baseline-direct
- **能力槽:** 使用已有上下文信息直接完成任务
- **类型:** 内置
- **健康:** healthy
- **调用策略:** 默认首选
- **授权级别:** 普通记录
- **触发:** 已给信息足够完成任务时。**禁用条件:** 任务需要额外工具/联网/外部系统时不得强行走此路由
- **风险:** 无

### win-control

- **ID:** win-control
- **能力槽:** 控制 Windows 窗口/点击/输入/截图/剪贴板/应用启动
- **类型:** MCP（16工具）
- **平台:** Claude Code
- **部署与健康:** 已配置 / healthy
- **调用策略:** conditional（仅用户明确要求桌面操作时）
- **授权级别:** 普通记录
- **触发:** 用户明确说"打开/点击/截图/窗口/输入"时。**禁用:** 勿用于后台自动化、批量无确认操作、未明确授权的窗口操控
- **风险:** medium（可操作桌面UI、剪贴板）
- **manager-type:** 是（16工具全量暴露，描述需截断安全）
- **详情卡:** `manifests/win-control.md`

### gh-cli

- **ID:** gh-cli
- **能力槽:** GitHub PR/Issue/API/仓库查询与操作
- **类型:** CLI
- **平台:** 共享
- **部署与健康:** 已安装 / healthy
- **调用策略:** conditional
- **授权级别:** 普通记录（仓库查询）；配置修改（PR/Issue创建）
- **触发:** GitHub 仓库查询、PR/Issue 操作、API 调用。**禁用:** 勿用于非 GitHub 的 git 操作
- **风险:** low
- **详情卡:** `manifests/gh-cli.md`

### ssh-server

- **ID:** ssh-server
- **能力槽:** SSH 连接 <server-ip>，执行远程命令/部署/服务管理
- **类型:** CLI
- **平台:** 共享
- **部署与健康:** 已配置 / healthy
- **调用策略:** explicit-only（执行前必须用户确认）
- **授权级别:** 配置修改（涉及服务器操作）
- **触发:** 服务器部署、服务重启、远程日志查看。**禁用:** 勿在未确认时执行远程命令、勿自动 SSH
- **风险:** high（服务器 root 访问）
- **详情卡:** `manifests/ssh-server.md`

### web-search

- **ID:** web-search
- **能力槽:** 搜索公开网页并获取内容，生成带来源的摘要
- **类型:** 内置（WebSearch + WebFetch）
- **平台:** Claude Code
- **部署与健康:** built-in / healthy
- **调用策略:** conditional
- **授权级别:** 普通记录
- **触发:** 查公开文档、最新信息、GitHub 页面。**禁用:** 勿访问登录态页面、内部系统、含认证的URL
- **风险:** low
- **详情卡:** `manifests/web-search.md`

### file-ops

- **ID:** file-ops
- **能力槽:** 创建/编辑/删除本地文件
- **类型:** 内置（Write/Edit/Read/Glob/Grep）
- **平台:** Claude Code
- **部署与健康:** built-in / healthy
- **调用策略:** conditional
- **授权级别:** 普通记录（E盘）；需确认（C盘写入/删除）
- **触发:** 文件读写、代码编辑、搜索。**禁用:** C盘写入未经确认不得执行
- **风险:** low（E盘）/ medium（C盘）
- **详情卡:** 无（内置工具集）

### grep-glob-git

- **ID:** grep-glob-git
- **能力槽:** 代码全文搜索/文件名匹配/Git历史与差异
- **类型:** 内置（Grep/Glob/Bash git）
- **平台:** Claude Code
- **部署与健康:** built-in / healthy
- **调用策略:** auto
- **授权级别:** 普通记录
- **触发:** 代码搜索、文件查找、版本历史。**禁用:** 无特殊限制
- **风险:** 无
- **详情卡:** 无（内置工具集）
