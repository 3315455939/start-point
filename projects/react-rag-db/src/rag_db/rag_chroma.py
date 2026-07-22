"""
Chroma 版 RAG 实现：

- PyPDFLoader 读取 PDF 为 Document 列表
- RecursiveCharacterTextSplitter 切分为重叠 chunk
- DashScopeEmbeddings 生成向量
- Chroma 作为向量数据库（本地持久化）
- RetrievalQA 作为“检索 + 生成”的问答链

该模块提供两个对外函数：
- `ingest_pdf_to_chroma(...)`：离线入库（构建/覆盖向量库）
- `build_retrieval_qa(...)`：加载向量库并构建问答链
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain.chains import RetrievalQA  # type: ignore[import-not-found]
from langchain.text_splitter import (  # type: ignore[import-not-found]
    RecursiveCharacterTextSplitter,
)
from langchain_community.document_loaders import (  # type: ignore[import-not-found]
    PyPDFLoader,
)
from langchain_community.embeddings import (  # type: ignore[import-not-found]
    DashScopeEmbeddings,
)
from langchain_chroma import Chroma  # type: ignore[import-not-found]
from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]

from rag_db.config import EMBEDDING_MODEL


def _embeddings() -> DashScopeEmbeddings:
    """
    构造通义向量模型。

    使用配置：
    - 模型：`text-embedding-v1`
    - 密钥：`os.environ.get("DASHSCOPE_API_KEY")`
    """

    return DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY"),
    )


def ingest_pdf_to_chroma(
    pdf_path: str,
    persist_dir: str,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 180,
    collection_name: str = "rag_documents",
) -> int:
    """
    从 PDF 构建并持久化 Chroma 向量库。

    返回写入的 chunk 数量。
    """
    p = Path(pdf_path)
    if not p.is_file():
        raise FileNotFoundError(f"未找到 PDF 文件：{p}")

    out = Path(persist_dir)
    out.mkdir(parents=True, exist_ok=True)

    docs = PyPDFLoader(str(p)).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    # 为了可重复入库：清理旧集合（同目录多次 ingest 时避免叠加重复数据）
    vectordb = Chroma(
        collection_name=collection_name,
        persist_directory=str(out),
        embedding_function=_embeddings(),
    )
    try:
        vectordb.delete_collection()
    except Exception:
        
        pass

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=_embeddings(),
        collection_name=collection_name,
        persist_directory=str(out),
    )
    return len(chunks)


def build_retrieval_qa(
    persist_dir: str,
    *,
    llm: ChatOpenAI,
    top_k: int = 5,
    collection_name: str = "rag_documents",
) -> Any:
    """
    加载 Chroma 向量库并构建 RetrievalQA 链。

    注意：RetrievalQA 是“单轮问答链”，默认不维护多轮 chat_history。
    """
    d = Path(persist_dir)
    if not d.exists():
        raise FileNotFoundError(f"未找到向量库目录：{d}")

    vectordb = Chroma(
        collection_name=collection_name,
        persist_directory=str(d),
        embedding_function=_embeddings(),
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": int(top_k)})

    # chain_type="stuff"：把检索到的文档片段直接拼接进 prompt
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=False,
    )

