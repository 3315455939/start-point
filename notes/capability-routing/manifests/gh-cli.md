# gh CLI

仅用于：GitHub 仓库查询、PR/Issue 操作、API 调用。
不要用于：非 GitHub 的 git 操作（用内置 Bash + git）。

## 基本信息

- **能力 ID:** gh-cli
- **名称:** GitHub CLI
- **类型:** CLI
- **平台:** 共享
- **来源:** `gh` CLI（通过包管理器安装）
- **能力槽:** GitHub PR/Issue/API/仓库查询与操作

## 存储决策

- **资产管理:** cli
- **管理状态:** active
- **健康状态:** healthy
- **风险:** low

## 路由

- **触发条件:** GitHub 仓库查询、PR/Issue 操作、API 调用
- **禁用条件:** 勿用于本地 git 操作（git add/commit/push 直接用 Bash）
- **替代方案:** WebFetch（只读查询时可替代）
- **Registry 条目:** `registry/level2-registry.md#gh-cli`

## 激活

- **激活方式:** 已安装，`gh` 命令直接可用
- **健康检查:** `gh auth status`
- **回滚方式:** 无

## 安全

- **License:** MIT
- **权限范围:** GitHub 账户读写
- **是否涉及凭据:** 是（OAuth token）
- **副作用:** PR/Issue 创建会公开发布内容
