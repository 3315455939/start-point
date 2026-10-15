# Windows 上的文本编码陷阱

Windows 上处理文本有四个独立的坑，读、写、跨进程、跨机器各一个。它们都会表现成"文件坏了"或
"中文变乱码"，但修法完全不同。本文给出每个坑的判据与字节级验证方法。

## 一、读：PowerShell 5.1 按 ANSI 代码页读无 BOM 的 UTF-8

Windows PowerShell 5.1（`powershell.exe`）读**无 BOM 的 UTF-8** 时，按系统 ANSI 代码页解析。
中文 Windows 上是 cp936，于是：

```powershell
Get-Content .gitignore     # 中文注释显示成乱码，但文件本身是好的
```

判据：**用字节读，不用肉眼**。

```powershell
python -c "b=open(r'path','rb').read(); print(b[:3], len([x for x in b if x>127]))"
```

乱码只在显示层时，字节里不会有 `U+FFFD`（替换字符）。反之，如果文件真被写坏，会出现 `EF BF BD`。

## 二、写：`>` 重定向写的是 UTF-16

PowerShell 的 `>` 重定向在 5.1 与 7 上默认编码不同，5.1 下会写出 UTF-16LE：

```powershell
git show <rev>:scripts/foo.py > .cache/old.py
# 原文件 18539 字节，写出 38012 字节（正好翻倍）
```

双倍大小是 UTF-16 的指纹。下游工具（`python`、`grep`、`git`）读它就会报奇怪的语法错误。

修法：需要保留原始字节时用 `git show ... | Out-File -Encoding utf8`（并确认无 BOM），
或者干脆绕开 PowerShell 的重定向。

## 三、跨进程：Python 在 Windows 上默认 gbk

Python 在 Windows 的 `stdout` 默认是 gbk，往管道里写中文会乱码或直接抛
`UnicodeEncodeError`：

```powershell
$env:PYTHONIOENCODING='utf-8'    # 跨管道传中文前设上
```

## 四、跨机器：把脚本文本喂给 `ssh` 的 stdin 会被改动

```powershell
Get-Content probe.sh -Raw | ssh host "bash -s"
# 远端：bash: line 1: set: command not found
#       bash: line 47: $'\r': command not found
```

本地文件是干净的 UTF-8 + LF（`first3=115,101,116` 就是 `set`，CRLF 计数 0），
但远端收到的是**带 BOM、行尾还被改成 CRLF** 的文本：BOM 让第一行非法，CR 让后续每行报错。

修法：**传脚本一律 base64**。

```powershell
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($p))
ssh host "echo $b64 | base64 -d | bash"
```

注意这两条错误都报在远端，很容易被误判成"服务器上的 bash 有问题"，根因其实在本地管道。

## 编码约定（可直接抄）

| 文件类型 | 编码 |
|---|---|
| `.ps1` | **纯 ASCII**，注释与消息都用英文 |
| `.sh` `.md` `.py` `.json` `.yml` | UTF-8，**无 BOM** |

`.ps1` 要纯 ASCII 的原因是第一条：5.1 会把无 BOM 的 UTF-8 按 cp936 解析，中文不仅显示乱，
还可能破坏解析。

## 一句话总结

- 读写文本都用字节级检查，不靠肉眼。
- 大小翻倍 = UTF-16；出现 `EF BF BD` = 真的坏了；只是显示乱 = 显示层假象。
- 跨进程传中文设 `PYTHONIOENCODING=utf-8`；跨机器传脚本用 base64。
