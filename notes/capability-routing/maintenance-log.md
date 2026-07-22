# Maintenance Log / 维护日志

## 2026-07-22 — 初始化能力路由体系

### 新增

- 创建 `~/dev-main/capability-library/` 完整目录结构
- `router/level1-router.md` — L1 薄路由（7 个任务分类，截断安全）
- `registry/level2-registry.md` — L2 注册表（7 行）
- `manifests/*` — 5 张 L3 能力卡（win-control/gh-cli/ssh-server/web-search/memory）
- `inventory/capability-ledger.md` — 全量能力账本
- `reference/systematic-debugging.md` — 从 Superpowers 提取的系统调试方法论
- `reference/test-driven-development.md` — 从 Superpowers 提取的 TDD 方法论
- `reference/verification-before-completion.md` — 从 Superpowers 提取的验证铁律
- `~/CLAUDE.md` 追加一行路由指针

### 删除

- `~/dev-main\tools\rtk.exe`（8.9MB）— 80% 子命令被 Claude Code 内置覆盖
- `~/dev-main\scripts\disk-stat.ps1` — 被 `check-disk.ps1` 全量覆盖
- `~/dev-main\CLAUDE.md` 中 rtk 指令（~4 行，范式 1 和快捷命令）— 2026-07-22 第二次清理时移除
- Superpowers 6.1.1 插件（2.4MB，203 文件）— 10/12 技能与内置重合，总管型触发与薄路由冲突
- `~/\.claude\plugins\cache\superpowers-marketplace\` 完整删除
- `installed_plugins.json` 和 `known_marketplaces.json` 已清空

### 预期效果

- 启动上下文瘦身：去掉了 rtk.exe + Superpowers 12技能发现层 + plugin marketplace 元数据
- 总管型能力清零：不再有「1% 可能就必须调用全部 skill」
- 路由分层就绪：L1 薄路由 → L2 注册行 → L3 能力卡 → 本体
- 独有方法论保留：3 个 reference 文件按需读取

### 未执行事项

- 无
