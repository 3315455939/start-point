"""
一键入库脚本（面向初学者的“最短路径”）。

等价命令：
  `python -m ecust_rag ingest --pdf ecust.pdf --out data/index`

为什么需要这个脚本：
- 课堂/新手经常不熟悉 `-m`、包路径与工作目录
- 这里显式把 `src/` 加入 `sys.path`，确保在项目根目录直接运行也能导入包

前置条件：
- 项目根目录存在 `ecust.pdf`
- 已配置向量化所需密钥（见 `src/ecust_rag/config.py` 的 ARK_API_KEY）
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    # 允许在“未安装成包”的情况下直接运行脚本（教学/演示场景）。
    sys.path.insert(0, str(SRC))

from ecust_rag.ingest_cli import run_ingest


def main() -> None:
    """使用项目根目录下的 ecust.pdf，输出到 data/index。"""
    pdf = ROOT / "ecust.pdf"
    out = ROOT / "data" / "index"
    run_ingest(str(pdf), str(out))


if __name__ == "__main__":
    main()
