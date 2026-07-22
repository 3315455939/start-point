# memory 系统

仅用于：读写持久化记忆文件（用户偏好、项目状态、工具参考）。
不要用于：存储临时会话状态、替代 git 记录代码变更。

## 基本信息

- **能力 ID:** memory
- **名称:** Claude Code Memory 系统
- **类型:** 内置（Claude Code 原生）
- **平台:** Claude Code
- **来源:** `~/.claude/projects/<project>/memory/`
- **能力槽:** 读写持久化记忆，跨会话复用

## 存储决策

- **资产管理:** built-in
- **管理状态:** active
- **健康状态:** healthy
- **风险:** low

## 路由

- **触发条件:** 用户偏好查询、项目状态记录、工具参考
- **Registry 条目:** 无（内置于 CLAUDE.md 初始化流程）

## 文件清单

- `MEMORY.md` — 索引
- `soul.md` — 人格准则
- `user.md` — 用户信息
- `tools.md` — 工具参考
- `projects/` — 项目进度
- `rules/` — C盘/Token规则
