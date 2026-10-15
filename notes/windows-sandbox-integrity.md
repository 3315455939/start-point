# Windows 沙箱的强制完整性标签

在 Windows 上给 agent 的 shell 加沙箱时，会遇到一种很像"随机失败"的现象：同一个进程里，
有的目录能写，有的目录**一律拒绝**，看起来毫无规律。

本文记录这套机制的实测判据与修法。

## 现象

在受限（沙箱内）的 shell 里：

```
Set-Content <工作区>\w1.txt          -> OK
Set-Content <工作区>\docs\w3.txt     -> UnauthorizedAccessException
python -m venv / npm install         -> [WinError 5] / EPERM: operation not permitted
```

同一个工作区根能写，根下面的某个子目录不能写。

## 两条命令定生死

```powershell
icacls <工作区根>
icacls <写不进去的目录>
```

看输出末尾有没有 `Mandatory Label` 这一行：

| 对象 | 强制标签 | 受限命令可写 |
|---|---|---|
| 工作区根 | `Low Mandatory Level:(OI)(CI)(NW)` | ✅ |
| 沙箱授权**之后**新建的目录 | 有（靠继承） | ✅ |
| 沙箱授权**之前**就存在的目录 | **没有这一行** | ❌ |

## 机制

1. 沙箱把命令子进程降级为 **Low 完整性**，写边界由内核的 no-write-up 规则定：
   **只有带 Low 标签的对象可写**。
2. 每次授权，沙箱一次性写三样东西：一个能力 SID 的允许 ACE、一条 `Everyone` 的拒绝 ACE、
   以及那条 Low 标签。文档里的说法是"授权物化是急切的全树传播"。
3. 但**传播只覆盖授权那一刻已经存在的后代**。授权时已经躺在根目录里的旧目录不会被追溯标注，
   之后新建的才会继承。
4. 授权入口开头有一条幂等快捷路径：三样都命中就直接返回，**跳过全树再传播**。
   于是根目录从此"已授权"，那些漏标的旧目录**永久保持无标签**，重启服务也没用。

**修法**：把根上那条标签补到**直接子目录**即可，不必遍历整棵树（标签带容器继承）。

```powershell
# 需要管理员窗口：改安全描述符需要 SeSecurityPrivilege
icacls <工作区根>\docs /setintegritylevel "(OI)(CI)Low"
```

验收两条都过：

```powershell
icacls <工作区根>\docs\sub   # 期望带 (I) 的 Low 标签，说明是继承来的
Set-Content <工作区根>\docs\zz.tmp -Value x   # 期望 OK
```

## 配套的判断规则：环境不让做 ≠ 你的代码有 bug

同一类坑还有一个更贵的版本。给工作区补标签需要 `SeSecurityPrivilege`，一个自写的脚本在管理员窗口里报：

```
ABORT: this token has no SeSecurityPrivilege. Re-run in an ELEVATED (Administrator) terminal.
```

容易得出的错误结论是"提升令牌里没有这条权限，标签打不了"。实际上三步交叉就能定性：

| 证据 | 取值 |
|---|---|
| `whoami /groups` 的完整性 | `High Mandatory Level (S-1-16-12288)` |
| `whoami /priv` | `SeSecurityPrivilege  Manage auditing and security log  Disabled` |
| 结论 | **特权在令牌里，只是未启用**，脚本自己启用即可 |

判据：**先确认令牌里有没有那条特权（`Disabled` 也算在），再谈命令写得对不对。**
非提升窗口的 `whoami /priv` 里，这条**根本不出现**，那是另一种失败，修法完全不同。

## 一句话总结

- 写不进去先查 `icacls` 的 Mandatory Label 行，不要先怀疑权限继承或杀软。
- 标签只对"授权那一刻已存在"的后代失效，补标签只补直接子目录。
- 需要改安全描述符的动作，一律在管理员窗口里做，并且先看 `whoami /priv`。
