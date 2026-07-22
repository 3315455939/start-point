# Capability Ledger / 能力账本

> 全量盘点，每行一个能力。管理状态/健康状态/风险分开记录。
> 最后更新: 2026-07-22

## Active

| ID | 能力槽 | 类型 | 健康 | 风险 | 总管型 | 备注 |
|---|---|---|---|---|---|---|
| baseline-direct | 直接作答 | 内置 | healthy | 无 | 否 | 默认首选 |
| grep-glob-git | 本地代码搜索与文件查找 | 内置 | healthy | 无 | 否 | Grep+Glob+Bash |
| web-search | 联网搜索与页面抓取 | 内置 | healthy | low | 否 | WebSearch+WebFetch |
| file-ops | 文件读写与编辑 | 内置 | healthy | low-med | 否 | C盘写入有门禁 |
| win-control | Windows桌面操控 | MCP | healthy | medium | **是** | 16工具，截断安全改写 |
| gh-cli | GitHub CLI操作 | CLI | healthy | low | 否 | |
| ssh-server | SSH服务器运维 | CLI | healthy | high | 否 | 执行前必须确认 |
| memory | 记忆系统读写 | 内置 | healthy | low | 否 | ~/\.claude\projects\ |

## Cold

| ID | 能力槽 | 类型 | 健康 | 风险 | 备注 |
|---|---|---|---|---|---|
| check-disk | C盘空间使用分析 | Script | unverified | low | PowerShell，低频 |
| clean-safe | 安全磁盘清理 | Script | unverified | medium | PowerShell，涉及删除 |
| deploy.sh | 服务器部署脚本 | Script | unverified | medium | Bash，需SSH配合 |
| <gateway-service> | OpenClaw网关systemd服务 | Service | unverified | medium | 服务器端 |

## Reference

| ID | 内容 | 路径 |
|---|---|---|
| systematic-debugging | 系统调试方法论（根因追踪/防御深度/条件等待） | `reference/systematic-debugging.md` |
| test-driven-development | TDD RED-GREEN-REFACTOR方法论 | `reference/test-driven-development.md` |
| verification-before-completion | 完成前验证铁律 | `reference/verification-before-completion.md` |

## Retired

| ID | 原能力 | 退役原因 | 退役日期 |
|---|---|---|---|
| rtk | Rust Token Killer CLI | 80%子命令被Claude Code内置覆盖，用户不使用 | 2026-07-22 |
| superpowers | Superpowers 6.1.1 插件（12技能） | 10/12与内置重合，总管型触发与薄路由冲突 | 2026-07-22 |
| disk-stat | C盘四行统计脚本 | 被check-disk.ps1全量覆盖 | 2026-07-22 |
