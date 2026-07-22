"""
`python -m rag_db` 的模块入口。

该文件只做一件事：把执行权交给 `rag_db.main.main()`。
好处是：
- 便于将来把 CLI 逻辑集中在 `main.py` 里维护
- `python -m` 与 `react-rag-db`（console script）共享同一套入口实现
"""

from rag_db.main import main

if __name__ == "__main__":
    main()
