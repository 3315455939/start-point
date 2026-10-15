---
name: release
description: 把 dev-main 攒好的改动推送出去；发布公开库时给出敏感信息扫描与网页操作步骤。
whenToUse: 用户要求提交、推送、发布，或要求把内容发布到公开库 start-point 时。
---

# 发布

| 仓库 | 位置 | 性质 |
|---|---|---|
| `dev-main` | `<repo>` | 私有。真值源是本机工作区，GitHub 这份是异地备份与历史存档 |
| `start-point` | `github.com/3315455939/start-point` | 公开，技术名片。**本地不留副本**，见第三节 |

前两节只服务 `dev-main`；要发布公开库时另看第三节。

## 一、推送门禁

`scripts/githooks/pre-push` 扫**索引**，命中即中止推送。它可被绕过，所以服务端由
`.github/workflows/checks.yml` 兜底，并额外扫**全部历史**（索引门禁看不见历史）。

同一个钩子还会打印本次推送的**提交数与主题前缀数**，非阻断。AGENTS.md「提交节奏」的
判据 C 是日均 ≤ 5 条提交、单条平均文件数 ≥ 8，超标时它会把话指回那一节。
**它只提示，不阻断**：启发式门禁一旦误报就会被绕过，等于没有门禁。

**每个克隆激活一次**（`.git/hooks` 不被 git 版本化，所以钩子本体入库在 `scripts/githooks/`）：

```powershell
git -C <repo> config core.hooksPath scripts/githooks
```

需要在不推送时手动跑同一次扫描：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <repo>\scripts\setup\scan-secrets.ps1 -Index
```

它扫索引而不是工作树。工作树里有 `.dsh/.credentials.yaml` 与 `infra/secrets/.env` 这类合理存在的本地真值，
扫工作树会几乎每次推送都误报；误报一多门禁就会被无视，等于没有。命中时报告只给**规则、文件、行号**，不给密钥值。

Linux 主机没有 powershell 时钩子**不放行**：拿不到「扫描已完成」的证据就一律拦。
服务器已不再 `git pull`（见下），所以这一条目前没有实际触发点，留档说明行为。

## 二、推送

**推送本身不构成「一件事」。** 提交节奏的判据在 `AGENTS.md` 的「提交节奏」节，本节不重复。
要点：工作区只有半成品时，不要为了发布临时造一个提交；先问用户这批改动算不算一件事。

```powershell
git -C <repo> status --short   # 先看攒了什么
git -C <repo> push
```

用 `git push`，不用 `--force`。破坏性操作（历史重写 / 大范围删除 / 批量重命名 / `--force`）
之前先提交当前状态留一个回退点，需要回退点也可以 `git stash` 或快照脚本，别拿 `git commit` 当存档。

**在受限沙箱内推不了，只剩「提权」这一层。** 受限令牌下 MSYS 的 `sh.exe` 起不来
（`couldn't create signal pipe, Win32 error 5`，退出码 3221225794），**pre-push 钩子因此没有执行路径**；
对那一条命令用 `danger-full-access`，钩子才会真的执行。

**2026-10-12 已修掉第二道坎**：以前还要手工把 `TEMP` 指到工作区，否则 gitleaks 写不出报告
（受限子进程只对工作区可写）。现在 `scan-secrets.ps1` 自己把报告与日志写到工作区的 `.cache\tmp`，
所以**不必再改 `TEMP`**：

```powershell
# 只对这条命令提权；TEMP 保持原样
git push
```

实测（提权、`TEMP` 未改动、推本地裸库）：`[PASS] no secrets found`，覆盖 ~1617156 bytes，exit 0。
代价是提权同时关掉文件隔离，只对需要它的单条命令用；**最省事的仍是普通终端推**（门禁在那里自己跑完）。
判据与修复过程见 `docs/lessons.md` §72，排障入口见 `docs/troubleshooting.md`。

## 三、发布到公开库

**公开库 `start-point` 只在 GitHub 网页维护，本地不留副本**（2026-10-11 起）。
本机不再克隆它：改内容走网页编辑器，改完直接 commit。

网页编辑没有 dev-main 的 pre-push 门禁兜底，所以**入库前必须扫敏感信息**。
从 dev-main 的文本文件里找 **API Key / Token / 密码 / 服务器 IP**，命中先处理再发布：

```powershell
grep -rnE "sk-|ghp_|AKIA|[0-9]{1,3}(\.[0-9]{1,3}){3}" <repo> --include=*.md
```

两条约束：

- **不整体复制目录。** 公开库是选定的子集，不是镜像。
- **平台不代管公开库的版本。** 它与 dev-main 的历史互不相干，各自提交。

想重新拿到本地副本时再 clone，用完即删：克隆它等于手工造出第二份会漂移的副本，
这正是 2026-10-11 退役本地副本的原因（见 `docs/status.md`）。

## 红线

- 不用 `git push --force`（破坏性操作前先留回退点）。
- 密钥值不进命令行参数，也不进公开库任何文件（含历史）。
- 服务器不持有 GitHub 凭据，`git pull` 拉不动是**有意为之**：公网机器不该能读私有库。
  同步到服务器走 `deploy` skill，不要试图在服务器上拉取。
