# WebSearch + WebFetch

仅用于：搜索公开网页、获取官方文档、读取公开 GitHub 页面。
不要用于：登录态页面、内部系统、含认证 Cookie/Token 的 URL。

## 基本信息

- **能力 ID:** web-search
- **名称:** 联网搜索与页面抓取
- **类型:** 内置（DSH 原生工具：`web_search` + `web_fetch`）
- **平台:** DSH（内置）
- **能力槽:** 搜索网页并获取内容，生成带来源摘要

## 存储决策

- **资产管理:** built-in
- **管理状态:** active
- **健康状态:** healthy
- **风险:** low

## 路由

- **触发条件:** 查公开文档、最新信息、GitHub 页面、技术资料
- **禁用条件:** 不碰登录态、内部系统、认证页面
- **替代方案:** gh CLI（GitHub 专用场景）
- **Registry 条目:** `registry/level2-registry.md#web-search`

## 安全

- **权限范围:** 公开网页只读
- **是否涉及凭据:** 否
- **副作用:** 无（只读）
