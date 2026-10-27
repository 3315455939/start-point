---
name: audit
description: 对 dev-main 环境做一次体检，找出幽灵引用、明文密钥、编码违规、C 盘新增写入、E 盘运行时可回收量与配置漂移。
whenToUse: 用户要求体检、审查环境、排查配置不一致，或提交前需要确认没有引入问题。
---

# 环境体检

每项检查都给出**可判定结论**，不是模糊提示。发现即列出路径与证据。

## 检查项

### 1. 幽灵引用

扫描仓库内 markdown 与脚本中出现的绝对路径，验证其是否存在。

```powershell
python <repo>\scripts\setup\dsh-audit.py
python <repo>\scripts\diagnostics\check-doc-refs.py    # 反引号路径引用
```

`check-doc-refs.py` 是**诊断工具不是门禁**：它有约 12 条已知的永久豁免（记在脚本自己的 docstring 里），
只扫现役文档、不扫 `docs/archive/`。看到命中要逐条判断，别当成必须清零的红灯。

已知历史幽灵引用（修复后应消失）：

| 引用 | 出现位置 | 状态 |
|---|---|---|
| `<repo>\tools\` | 旧 soul.md / user.md / troubleshooting.md | 该目录从未存在 |
| `env-secret/.env.template` | 旧 handoff.md | 该文件不存在（`env-secret/` 本身也已在 2026-09-22 并入 `infra/secrets/`） |
| `memory/soul.md` | 旧 `<home>\CLAUDE.md` | 该文件与该目录均已删除（2026-09-22） |

### 2. 明文密钥

交给 gitleaks 扫，**不要用自写的正则**。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <repo>\scripts\setup\scan-secrets.ps1
```

退出码 0 = 无命中，1 = 有命中。`-Quiet` 只输出一行，适合接进门禁。

脚本已强制两件事，不要绕过它直接敲 gitleaks：

| 强制项 | 原因 |
|---|---|
| `--redact` | gitleaks 默认把匹配到的密钥**原文**打进报告与 stdout，不加这个 flag，扫描本身就是一次泄露 |
| 只用 `dir` 子命令 | 见下 |

**为什么弃用原来的正则**：`git grep -nIE "sk-...\|ghp_...\|AKIA..."` 没有规则库、
不查历史、无熵检测、无白名单。密钥格式的长尾远不止三种，自己维护这张表必然漏。

#### ⚠️ 不要用 `gitleaks git`

在 DSH 沙箱下它会失败**而不报错退出**：

```
ERR [git] sh.exe: *** fatal error - couldn't create signal pipe, Win32 error 5
ERR [git] fatal: unable to read files to diff
INF 13 commits scanned.
INF no leaks found          ← 实际有 64 个提交
```

git 模式调用 MSYS 的 `sh.exe`，而 DSH 沙箱禁止创建具名管道
（同一限制见 `scripts/diagnostics/mcp-handshake-probe.py` 的文件头注释）。

**只扫了五分之一却报「无泄漏」，比不扫更危险。** 需要扫历史时，以
`danger-full-access` 提权单独执行，不要塞进日常门禁。

#### 扫描范围与排除

`gitleaks dir` **不看 `.gitignore`**，运行时会连 `.dsh/`、`infra/secrets/.env`、`.venv/` 一起扫，
那些地方本来就有真实凭据与第三方误报。排除项写在 `.gitleaks.toml` 里，每条都注明了理由。

排查结果只报**规则、文件、行号**，密钥值一律不打印。

### 3. 编码约定

`.ps1` 必须纯 ASCII。违反会在中文 Windows 上损坏解析：

```powershell
python <repo>\scripts\setup\dsh-audit.py
```

该脚本检查项 6 覆盖 preset、skill frontmatter、`AGENTS.md` 字节预算与共存规则。
`.ps1` 的 ASCII 判定用字节级扫描，不靠肉眼：

```powershell
python -c "import glob
for f in glob.glob(r'<repo>\scripts\**\*.ps1', recursive=True):
    b = open(f, 'rb').read()
    n = len([x for x in b if x > 127])
    print(('FAIL' if n else 'PASS'), f, n)"
```

### 4. C 盘写入登记

对照 `docs/c-drive-ledger.md`，检查是否有未登记的写入点。

排查已知的 AI agent 残留目录：

```powershell
Get-ChildItem <home> -Force -Directory | Where-Object { $_.Name -match '^\.(codex|copilot|marscode|lark-cli|verifier-pylibs|workbuddy)' }
```

### 5. 配置漂移

`dsh/` 是 DSH 配置真值源，`$DSH_HOME` 是落盘副本。两者应一致：

```powershell
dsh --profile web --help     # 唯一可信校验：补丁能否 boot
```

期望 exit 0。**不要**用 `--dump-config` 当补丁安全的证明（不校验重复行），
**更不要**写 `dsh --profile web --patch <本 profile 自己的补丁> --dump-config`：
补丁已落盘时会重复叠加同一行并给出虚假 exit 0。

副本一致性用文件比较判定，不用 dump：

```powershell
git diff --no-index <repo>\dsh\profile\cordis.patch.yml <repo>\.dsh\profiles\web\cordis.patch.yml
```

`bootstrap.ps1 -DryRun` 会打印所有待复制项，落盘前先看它。

### 6. DSH 硬约束

| 约束 | 检查方式 |
|---|---|
| preset id 匹配 `[a-z0-9][a-z0-9-]*` | 读 `dsh/profile/cordis.patch.yml` 里 `agent-preset-registry` 行的 `config.default` |
| persona 除 `{{model}}`/`{{provider}}` 外无 `{{…}}` | 正则扫同一文件里 `preset-<id>` 行的 persona 段。**0.2.1-rc.2 起 `cwd` 不再注册**，模板里留着它会在任何模型请求之前抛 `unknown prompt variable` |
| preset 必须由 `insert` 行声明 | 顶层 `- id: preset-<id>` 只会得到 `patch: entry not found` 并被跳过，boot 仍 exit 0 |
| `AGENTS.md` ≤ 8 KB | 量字节数 |
| `AGENTS.md` 与 `CLAUDE.md` 不同时存在 | 同目录共存即失败（两者都会被注入） |

### 7. E 盘运行时占用与可回收量

`c-drive-usage.ps1` 只扫 C 盘，`.dsh/` 与 `.cache/` 都在 E 盘，不在它的视野里。只读盘点：

```powershell
python <repo>\scripts\ops\session-clean.py             # dry run，默认只算已归档会话
python <repo>\scripts\ops\session-clean.py --all-stale # 连带脱离注册表的会话
```

**报两个数字，不要只报一个**：可回收量，以及仍被引用而不可回收的量。后者由存活会话决定，删不掉；
靠删会话去凑数是另一类决策，不是清理。规则见 `docs/structure.md` 落点规则 ④。

| 项 | 判据 |
|---|---|
| 附件库物理占用 | `files/` 与 `file-objects/` 互为硬链接，两目录相加是重复计数；物理占用约等于 `objects/` + `file-objects/` |
| 可回收 | dry run 的 `Reclaimable:` 行 |
| 不可回收 | dry run 的 `N of M blob(s) still referenced` 行 |

**先看这条再动手**：blob 的文件名就是它的 hash，把附件文件名打印进会话，就会把那个 blob 钉住。
统计占用只用 `Get-ChildItem <附件目录> -Recurse -File | Measure-Object -Property Length -Sum`（只输出数字）；
不要 `Select-Object FullName`。2026-10-13 有一次就是这么让自己的会话变成引用者的。

结论按 `[WARN]` 报，不判 PASS/FAIL。`--apply` 属免问范围（规则见 `docs/structure.md` 落点规则 ④），
但**报数要说明是第几遍的量**：第一遍删日志与投影，第二遍才收因此变成孤儿的 blob。

## 输出格式

```
[PASS] 检查项
[FAIL] 检查项 — 路径与证据
[WARN] 检查项 — 需人工判断
```

全 PASS 时输出单行总结。有 FAIL 时逐条列出并给修复建议。
