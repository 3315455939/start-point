"""初始化学籍 SQLite（data/school.db）：10 名学生、3 门课、每人 3 条成绩。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ecust_rag.db import ensure_db, reseed_db


def main() -> None:
    """命令行：初始化或强制重灌。"""
    ap = argparse.ArgumentParser(description="初始化 data/school.db 示例学籍数据")
    ap.add_argument(
        "--force",
        action="store_true",
        help="清空并重新灌入示例数据（已有库想升级为新数据时用）",
    )
    args = ap.parse_args()
    p = ROOT / "data" / "school.db"
    if args.force:
        reseed_db(str(p))
        print(f"已重灌示例数据：{p}")
    else:
        ensure_db(str(p))
        print(f"就绪：{p}")


if __name__ == "__main__":
    main()
