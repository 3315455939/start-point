# start-point

个人开源作品与技术笔记。

本仓库是私有仓库 `dev-main` 的**展示门面**：内容按最新的私有仓库重写，发布由脚本单向生成，
这里不接受手工编辑（下一次发布会覆盖）。所以本仓库只有一层含义：把还在用的东西拿出来给人看。

## 这里有什么

| 目录 | 内容 |
|---|---|
| [`notes/`](./notes/) | 技术笔记。Windows 沙箱的强制完整性标签、文本编码陷阱、文档的分层维护 |
| [`skills/`](./skills/) | 日常使用的动作说明（审计、环境重建、发布）。写法本身就是方法论的展示 |
| [`projects/`](./projects/) | 三个可运行的小项目 |

## 项目

| 项目 | 说明 | 技术栈 |
|---|---|---|
| [`multi-agent`](./projects/multi-agent/) | 多智能体协作的最小实现 | Python |
| [`react-rag-db`](./projects/react-rag-db/) | ReAct 式 RAG 问答 | Python · LLM · Chroma |
| [`team-project`](./projects/team-project/) | 个人自动化助手（桌面端 + 后端） | Python · React |

## 笔记

- [Windows 沙箱的强制完整性标签](./notes/windows-sandbox-integrity.md)：为什么有的目录能写、有的目录一律拒绝，以及两条命令的判据
- [Windows 上的文本编码陷阱](./notes/text-encoding-traps.md)：读、写、跨进程传文本各有一个坑，附带字节级验证方法
- [文档的分层维护](./notes/documentation-lifecycle.md)：参考、日志、归档三层各有保鲜期，混用是文档腐败的主因

## 关于我

GitHub：[@3315455939](https://github.com/3315455939)

技术栈：Python / Node.js / C / React · AI Agent / LLM 应用 / 桌面自动化

## 许可

MIT，见 [LICENSE](./LICENSE)。
