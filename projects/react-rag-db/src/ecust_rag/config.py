"""
模型与向量化配置。

当前工程同时演示两种“OpenAI 兼容”对接：
- **对话模型**：使用火山方舟（ARK）OpenAI 兼容接口（`ChatOpenAI`）
- **向量模型**：使用通义 DashScope（`DashScopeEmbeddings`，通常读取 `DASHSCOPE_API_KEY`）

课堂提示：
- 对话（Chat）与向量化（Embedding）往往来自不同厂商，配置环境变量时别混淆。
"""

import os
from pathlib import Path

from openai import OpenAI

# 从项目根目录加载 .env（需安装 python-dotenv）；密钥勿写入代码
try:
    from dotenv import load_dotenv

    _ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

API_KEY = os.environ.get("ARK_API_KEY")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
EMBEDDING_MODEL = "text-embedding-v1"
CHAT_MODEL = "doubao-seed-2-0-lite-260215"
HTTP_TIMEOUT = float(os.environ.get("P0413_HTTP_TIMEOUT", "600"))

# DashScope：用于 `DashScopeEmbeddings`（LangChain Community）
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")


def get_client() -> OpenAI:
    """构造用于对话的 OpenAI 兼容客户端。"""
    if not API_KEY:
        raise RuntimeError("请配置环境变量 ARK_API_KEY，或在项目根目录 .env 中设置。")
    return OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=HTTP_TIMEOUT,
        max_retries=2,
    )


def get_embedding_http_url() -> str:
    """多模态向量化接口完整 URL。"""
    return f"{BASE_URL.rstrip('/')}/embeddings/multimodal"
