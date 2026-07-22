"""
启动网页对话（等价于 python -m rag_db serve --index data/index）

用法：在项目根目录执行
  python serve_web.py

依赖：ARK_API_KEY；ingest 后的 data/index；data/school.db。
"""

from __future__ import annotations

import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

HOST = "127.0.0.1"
PORT = 8000
INDEX_DIR = ROOT / "data" / "index"
DB_PATH = ROOT / "data" / "school.db"


def main() -> None:
    """启动 Uvicorn 并尝试打开浏览器。"""
    import uvicorn

    from rag_db.web import create_app

    index_path = str(INDEX_DIR)
    app = create_app(
        index_path,
        db_path=str(DB_PATH),
        top_k=5,
    )

    url = f"http://{HOST}:{PORT}/"

    def _open_browser() -> None:
        import time

        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()
    print(f"索引：{index_path}  数据库：{DB_PATH}")
    print(f"浏览器访问：{url}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
