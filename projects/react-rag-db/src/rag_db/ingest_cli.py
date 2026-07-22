"""
入库命令（Chroma 版）：从 PDF 构建向量库并持久化到磁盘。

技术栈（按课堂要求）：
- `PyPDFLoader`：读取 PDF 为 Document 列表
- `RecursiveCharacterTextSplitter`：切分为重叠 chunk
- `DashScopeEmbeddings`：通义向量模型（需配置 `DASHSCOPE_API_KEY`）
- `Chroma`：向量数据库（本地持久化）

落盘目录是 Chroma 的 `persist_directory`，不再是旧版的 `meta.json/embeddings.npy`。
"""

from __future__ import annotations

import argparse

from rag_db.rag_chroma import ingest_pdf_to_chroma


def run_ingest(
    pdf: str,
    out: str,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 180,
) -> None:
    """读取 PDF → 切分 → 向量化 → 写入 Chroma 持久化目录。"""
    n = ingest_pdf_to_chroma(
        pdf,
        out,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    print(f"已写入 {n} 个 chunk 到 Chroma 目录：{out}")


def main() -> None:
    """命令行入口。"""
    p = argparse.ArgumentParser(description="从 PDF 构建向量索引并保存")
    p.add_argument("--pdf", type=str, default="document.pdf", help="PDF 路径")
    p.add_argument(
        "--out",
        type=str,
        default="data/index",
        help="Chroma 持久化目录（persist_directory）",
    )
    p.add_argument("--chunk-size", type=int, default=1000)
    p.add_argument("--chunk-overlap", type=int, default=180)
    args = p.parse_args()
    run_ingest(
        args.pdf,
        args.out,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )


if __name__ == "__main__":
    main()
