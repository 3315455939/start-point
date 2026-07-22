# Capability Routing Library / 能力路由库

为 AI Agent 设计的 3 层能力路由体系：L1 薄路由 → L2 注册表 → L3 能力卡。

灵感来源：[Table-GitHub-Capability-Router](https://github.com/duoduoler-ops/Table-GitHub-Capability-Router)

## 设计理念

Agent 不应扫描全量能力库。通过三层路由，Agent 只在启动时读取 7 行的 L1 薄路由表，命中后按需展开到 L2、L3。核心收益：上下文瘦身、路由分层、能力即插即用。

## 目录

```
capability-routing/
├── README.md                    本文件
├── router/
│   └── level1-router.md         L1 薄路由（7 个任务分类）
├── registry/
│   └── level2-registry.md       L2 注册表（每行一个能力元数据）
├── manifests/                   L3 能力卡（每个能力一张详细卡片）
│   ├── win-control.md           Windows 桌面操控
│   ├── gh-cli.md                GitHub CLI
│   ├── ssh-server.md            SSH 服务器运维
│   ├── web-search.md            Web 搜索
│   └── memory.md                Memory 系统
├── inventory/
│   └── capability-ledger.md     全量能力账本
└── maintenance-log.md           维护日志
```

## 关联

- [methodology/](../methodology/) — 开发方法论（调试、TDD、验证）
