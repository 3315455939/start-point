"""
项目的命令行入口（LangChain ReAct 版）。

提供三类能力：
- `ingest`: PyPDFLoader → RecursiveCharacterTextSplitter → DashScopeEmbeddings → Chroma 持久化
- `query`: 通过 LangChain ReAct 智能体调用 RAG/数据库工具
- `serve`: FastAPI Web 服务（对外暴露 `/api/chat`）
"""

from __future__ import annotations

import argparse

from ecust_rag.ingest_cli import run_ingest
from ecust_rag.react_agent_qa import build_react_agent_qa


def cmd_query(args: argparse.Namespace) -> None:
    """终端问答：ReAct 智能体自动选择 RAG 或数据库工具。"""
    qa = build_react_agent_qa(args.index, args.db, top_k=args.top_k)

    print(
        "ECUST Hybrid QA（空行退出）。Chroma 目录：",
        args.index,
        "数据库：",
        args.db,
    )
    while True:
        try:
            line = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            break
        try:
            print("助手:", qa.ask(line))
        except Exception as e:
            print(f"调用失败：{type(e).__name__}: {e}")


def main() -> None:
    """解析子命令并执行。"""
    parser = argparse.ArgumentParser(
        description="ECUST：PDF 向量检索 + 学籍库 + LangChain ReAct 智能体",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="从 PDF 构建向量索引")
    p_ingest.add_argument("--pdf", type=str, default="ecust.pdf")
    p_ingest.add_argument("--out", type=str, default="data/index")
    p_ingest.add_argument("--chunk-size", type=int, default=1000)
    p_ingest.add_argument("--chunk-overlap", type=int, default=180)

    p_query = sub.add_parser("query", help="终端交互问答")
    p_query.add_argument("--index", type=str, default="data/index")
    p_query.add_argument("--db", type=str, default="data/school.db")
    p_query.add_argument("--top-k", type=int, default=5, dest="top_k")

    p_web = sub.add_parser("serve", help="启动浏览器对话 Web 服务")
    p_web.add_argument("--index", type=str, default="data/index")
    p_web.add_argument("--db", type=str, default="data/school.db")
    p_web.add_argument("--host", type=str, default="127.0.0.1")
    p_web.add_argument("--port", type=int, default=8000)
    p_web.add_argument("--top-k", type=int, default=5, dest="top_k")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest(
            args.pdf,
            args.out,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    elif args.command == "serve":
        import uvicorn

        from ecust_rag.web import create_app

        app = create_app(
            args.index,
            db_path=args.db,
            top_k=args.top_k,
        )
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        cmd_query(args)


if __name__ == "__main__":
    main()
