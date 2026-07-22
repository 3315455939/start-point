# Level 1 Thin Router / 一级薄路由

> Agent 不扫描全量能力库。先读此表，只读命中类别，再打开对应的能力卡。
> 原理见 `methodology/` 下方法论文件。

## Writing rules

- 每行一句话，~30-50 字，单独成立
- 限制条件前置，不放行尾（截断安全）
- 一条入口只服务一个任务类型
- 未命中时优先 baseline-direct；不要扫描全库

## L1 Routing Table

| 任务类型 | 一句话边界 | 候选行 |
|---|---|---|
| 直接作答 | 已给信息足够直接完成，不加任何工具 | baseline-direct |
| 桌面操控 | 仅用户明确要求窗口/点击/输入/截图时启用，勿后台自动化 | win-control |
| 本地检索 | 代码搜索/文件查找/Git历史/版本对比 | grep-glob-git |
| 联网查资料 | 公开网页与官方文档，不碰登录态与认证页面 | web-search |
| GitHub操作 | PR/Issue/API/仓库查询，执行前确认 | gh-cli |
| 服务器运维 | SSH远程命令/部署/服务管理，执行前必须确认 | ssh-server |
| 文件读写 | 创建/编辑/删除本地文件，C盘写入执行前先问 | file-ops |
