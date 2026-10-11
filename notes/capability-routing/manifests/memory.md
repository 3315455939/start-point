# memory 系统

仅用于：读写持久化记忆文件（用户偏好、项目状态、工具参考）。
不要用于：存储临时会话状态、替代 git 记录代码变更。

## 基本信息

- **能力 ID:** memory
- **名称:** Claude Code Memory 系统
- **类型:** 内置（Claude Code 原生）
- **平台:** ~~Claude Code~~
- **能力槽:** 读写持久化记忆，跨会话复用

## 状态：已退役（2026-09-22）

**这张卡保留是为了说明「为什么现在没有记忆能力」。** 它指向的那套东西已经不存在：

| 项 | 结论 |
|---|---|
| 宿主 | Claude Code 与 `claude` 命令：2026-09-21 起即已断裂，09-22 彻底移除（3 个失效 shim、`claude-cli-nodejs`、`~\.claude` junction、`E:\dev-main\.claude-data`、`~\.claude.json`） |
| 数据 | `C:\Users\33154\.claude\projects\` 下的记忆与 5 份旧 Claude Code 对话记录（约 1 MB）已随宿主一并删除，**已确认放弃** |
| 唯一落点 | 现存「记忆」是 `docs/status.md`（现役状态唯一入口）与 `docs/lessons.md`（踩坑），都是文件，不是某套记忆系统 |

**不要照本卡去找记忆目录**：`C:\Users\33154\.claude\` 全盘已无残留。

现行替代（`AGENTS.md` 的记忆铁律）：心智笔记不存活，文件才存活。想记住的东西写进文件。

## 历史（退役前的形态）

- **来源:** `C:\Users\33154\.claude\projects\C--Users-33154\memory\`（已不存在）
- **Registry 条目:** 无（内置于 `CLAUDE.md` 初始化流程，`CLAUDE.md` 也已删除）
- **文件清单:** `MEMORY.md`（索引）——**这一行之外的五个名字是历史记录，指的文件都已随宿主删除**，
  不再用反引号标注，免得被幽灵引用检查当成现役引用：

  | 历史文件 | 现在的去处 |
  |---|---|
  | `soul.md`（人格准则） | DSH preset 的 persona 层（L0） |
  | `user.md`（用户信息） | `AGENTS.md` 的环境事实 |
  | `tools.md`（工具参考） | `capability-library/` |
  | `projects/`（项目进度） | `docs/status.md` |
  | `rules/`（C 盘 / Token 规则） | `AGENTS.md` 的写入规则 |
