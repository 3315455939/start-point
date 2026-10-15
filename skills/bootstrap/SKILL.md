---
name: bootstrap
description: 在新机器上从零恢复 dev-main 环境：装依赖、落 DSH 配置、注册 MCP、验证。
whenToUse: 换新电脑、重装系统后重建环境，或在另一台机器上克隆本仓库后首次配置。
---

# 新机环境恢复

目标：`git clone` 之后只跑一个脚本，环境可用，**零手工步骤**。

## 前置

需要已安装：

| 工具 | 校验方式 |
|---|---|
| Git | `git --version` |
| Node.js | `node --version` |
| Python | `python --version` |
| VS Code | 能启动（远程开发需 Remote-SSH 扩展） |

缺失的工具先报告，不擅自安装。

## 流程

### 1. 克隆

```powershell
git clone <repo-url> <repo>
```

仓库路径必须是 `<repo>`。DSH_HOME 与多处配置依赖这个绝对路径。

### 2. 运行 bootstrap

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <repo>\scripts\setup\bootstrap.ps1
```

脚本依次：

1. 校验上述四个工具存在
2. `pnpm add -g @deepseek-ai/dsh` 安装 DSH
3. 设置用户级环境变量 `DSH_HOME=<repo>\.dsh`
4. 把 `dsh/profile/cordis.patch.yml` 落盘到 `$DSH_HOME/profiles/web/`；落盘副本与源不一致时先备份成 `.bak-<时间戳>` 并拒绝覆盖（`-Force` 强推）
5. 不存在则建 `$DSH_HOME/cordis.patch.yml`（home patch 层，内容空列表；已存在则一个字节都不动）
6. 建仓库根 `.cache/`；`scripts/bin/gitleaks.exe` 缺失时给出取回命令（不联网下载）
7. 提示填 `infra/secrets/.env`（**不代填密钥**）
8. 三段校验：`--dump-config` 无 patch 警告、`dsh --profile web --help` exit 0、合并树里存在 registry default 指向的 preset

**preset 不是目录**：`dsh/agent-presets/` 已于 2026-10-12 退役。0.2.x 的 registry
不扫描目录，preset 声明在 `dsh/profile/cordis.patch.yml` 里（`insert` 一行
`@deepseek-ai/dsh-agent-preset` + registry 顶层覆盖 `default`）。

### 3. 人工补全（尽量为零）

脚本结束会打印仍需要手工做的事。密钥必须由用户自己填，脚本只输出模板路径。

### 4. 验证

```powershell
dsh --profile web --help                              # 唯一可信：补丁真能 boot
python <repo>\scripts\setup\dsh-audit.py         # 40 checks, 0 failed
```

**不要用 `--dump-config` 当作补丁安全的证明**：它不做重复 id 校验，
把已存在的 id 放进 `insert` 时它照样 exit 0，而 boot 会直接失败。
它是「看合并结果」的工具，不是门禁。最后启动 DSH Web 确认 `http://127.0.0.1:3080` 可达。

## 红线

- **不代填、不读取、不输出任何密钥。** 只提示路径。
- 环境变量写入注册表属于「合规写入」，但要告知写到了哪里。
- 不修改 `main` 分支的提交历史。
- 服务器配置不在此流程里。它需要单独的 SSH 密钥，恢复服务器访问属于独立任务。
