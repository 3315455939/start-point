# 受限沙箱下跑 MCP stdio 握手：为什么官方客户端会挂，以及怎么绕

写于 2026-09-21 · 平台 Windows · Python 3.14 · `mcp` SDK 1.28.1

---

## 现象

想验证一个 stdio 型 MCP server 能不能正常握手，最直觉的写法是用官方 SDK：

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async with stdio_client(StdioServerParameters(command=..., args=[...])) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
```

在普通终端里没问题。但在**受限沙箱**（进程创建被允许、但句柄/管道被限制）里必然失败：

```
PermissionError: [WinError 5] 拒绝访问。
  File ".../anyio/_backends/_asyncio.py", line 2745, in open_process
    transport, protocol = await loop.subprocess_exec(...)
  File ".../asyncio/windows_utils.py", line 136, in __init__
    stdin_rh, stdin_wh = pipe(overlapped=(False, True), duplex=True)
  File ".../asyncio/windows_utils.py", line 63, in pipe
    h2 = _winapi.CreateFile(address, access, 0, _winapi.NULL,
                            _winapi.OPEN_EXISTING, flags_and_attribs, _winapi.NULL)
```

注意失败点：**不是启动进程失败，是 `CreateFile` 建管道失败**。
`mcp.client.stdio` → `anyio.open_process` → Windows 的 asyncio 子进程传输，
而 asyncio 在 Windows 上是用**具名管道**（named pipe）实现子进程 stdio 的。
沙箱放行了 `CreateProcess`，却没放行具名管道 —— 于是 SDK 这条路直接封死。

`asyncio` 的调用栈很有迷惑性：报错落在 `windows_utils.py:63`，看起来像 asyncio 的 bug，
实际是环境权限问题。**看到 `CreateFile` + `WinError 5`，先怀疑沙箱，别去读 SDK 源码。**

---

## 关键区分：具名管道 vs 匿名管道

| 实现 | 用的管道 | 受限沙箱 |
|---|---|---|
| Windows `asyncio` 子进程传输 | **具名**管道（overlapped） | ❌ 被拒 |
| `subprocess.Popen(..., PIPE)` | **匿名**管道（`CreatePipe`） | ✅ 可用 |
| Node.js `child_process` 默认 stdio | **具名**管道 | ❌ 被拒 |

所以「沙箱禁了子进程」是误判 —— 禁的是**具名管道这一种 IPC 机制**。
换成匿名管道就能通，而匿名管道恰好是 MCP stdio 传输真正需要的东西：
一行一个 JSON-RPC，标准的换行分帧。

---

## 绕法：`Popen` + 手写 JSON-RPC

不依赖 SDK、不碰 asyncio，直接按 MCP 的线上协议说话：

```python
"""MCP stdio 握手探针（匿名管道版）。

用法: python mcp_handshake_probe.py <command> [args...]
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading

PROTOCOL_VERSION = "2025-11-25"
READ_TIMEOUT_S = 30.0


class Reader:
    """后台线程读 stdout，好让主线程能超时而不是挂死。"""

    def __init__(self, stream) -> None:
        self._lines: list[str] = []
        self._cv = threading.Condition()
        self._eof = False
        threading.Thread(target=self._pump, args=(stream,), daemon=True).start()

    def _pump(self, stream) -> None:
        for line in stream:
            with self._cv:
                self._lines.append(line)
                self._cv.notify_all()
        with self._cv:
            self._eof = True
            self._cv.notify_all()

    def next_line(self, timeout: float = READ_TIMEOUT_S) -> str | None:
        with self._cv:
            if not self._lines and not self._eof:
                self._cv.wait(timeout)
            return self._lines.pop(0) if self._lines else None


def send(proc: subprocess.Popen, payload: dict) -> None:
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: mcp_handshake_probe.py <command> [args...]")
        return 2
    command, *args = sys.argv[1:]

    proc = subprocess.Popen(
        [command, *args],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )
    out, err = Reader(proc.stdout), Reader(proc.stderr)

    try:
        send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "handshake-probe", "version": "1.0"},
        }})
        line = out.next_line()
        if line is None:
            print(f"FAIL: no initialize response within {READ_TIMEOUT_S:.0f}s")
            return 1
        reply = json.loads(line)
        if "error" in reply:
            print(f"FAIL: initialize error: {reply['error']}")
            return 1
        result = reply.get("result", {})
        info, caps = result.get("serverInfo", {}), result.get("capabilities", {})
        print(f"protocolVersion : {result.get('protocolVersion')}")
        print(f"serverInfo      : {info.get('name')} {info.get('version')}")
        print(f"capabilities    : tools={'tools' in caps} "
              f"resources={'resources' in caps} prompts={'prompts' in caps}")

        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        line = out.next_line()
        if line is None:
            print(f"FAIL: no tools/list response within {READ_TIMEOUT_S:.0f}s")
            return 1
        tools = json.loads(line).get("result", {}).get("tools", [])
        print(f"tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.get('name')}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if (text := "\n".join(err._lines).strip()):
        print("--- server stderr ---")
        print(text)
    print("handshake OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

跑起来：

```
$ python mcp_handshake_probe.py .venv/Scripts/python.exe server.py
spawning: .venv/Scripts/python.exe server.py
protocolVersion : 2025-11-25
serverInfo      : my-server 1.28.1
capabilities    : tools=True resources=True prompts=True
tools (16):
  - list_windows
  - click
  ...
handshake OK
```

三个容易踩的实现细节：

1. **`notifications/initialized` 必须发**，且它**没有 `id`**。少了这一步，很多 server 会把后续
   `tools/list` 当成初始化前的非法请求。反过来，通知也**永远不会有响应**，别去等它的 `id`。
2. **读必须放后台线程**。`for line in proc.stdout` 在主线程里读，遇到 server 不回话就是永久挂死；
   放进线程 + `Condition.wait(timeout)` 才有可控超时。
3. **`bufsize=1` + 每帧 `flush()`**。缓冲的 stdin 会让 server 一直等不到完整的一行。

---

## 更重要的教训：进程起来了 ≠ 接上了

这个探针只能证明「server 单独能跑」，**证明不了 harness 真的接上了**。
那次接线是靠**真调一次工具、拿到真实返回**才敢下结论的 ——
期间踩到「配置 dry-run 只报一句不起眼的 `entry not found` 警告就静默跳过」，
说明只看退出码和「进程起来了」会得出完全相反的结论。

完整的判据与分级见 [证据强度阶梯](../methodology/evidence-strength.md)（L0–L5）。

---

## 一句话总结

沙箱限制的是**具体的 IPC 机制**，不是笼统的「子进程」。
`WinError 5` 出现在 `CreateFile` 建管道处 → 换匿名管道（`Popen`）；
报错落在 asyncio 内部 → 先查环境，再查代码。
