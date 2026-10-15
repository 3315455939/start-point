"""
FastAPI Web 服务：网页对话与会话管理。

核心思路（LangChain ReAct 版）：
- 应用启动时构建一个统一问答智能体
- 智能体自主选择调用 RAG 工具或数据库工具
- 统一从 `/api/chat` 对外提供问答能力

注意：
- 本实现把索引与执行器保存在进程内存里，适合课堂演示/单机运行
- 若要多进程/多实例部署，应把会话历史外置（Redis/DB），并避免使用全局变量
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ecust_rag.react_agent_qa import build_react_agent_qa

_STATIC_DIR = Path(__file__).resolve().parent / "static"

_qa: Any = None


class ChatBody(BaseModel):
    """聊天接口请求体。"""

    message: str = Field(..., min_length=1, description="用户输入")
    session_id: str | None = Field(None, description="已有会话 id，首次可为空")


def _get_app_state(
    index_path: str,
    db_path: str,
    top_k: int,
) -> None:
    """构建 ReAct 智能体对象。"""
    global _qa
    _qa = build_react_agent_qa(index_path, db_path, top_k=top_k)


def create_app(
    index_path: str,
    *,
    db_path: str = "data/school.db",
    top_k: int = 5,
) -> FastAPI:
    """创建 FastAPI 应用：首页 HTML + /api/chat + /api/session/reset。"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _get_app_state(
            index_path,
            db_path,
            app.state.top_k,
        )
        yield
       

    app = FastAPI(title="智能体演示", lifespan=lifespan)
    app.state.top_k = top_k

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        html_path = _STATIC_DIR / "index.html"
        if not html_path.is_file():
            raise HTTPException(500, "缺少静态文件 static/index.html")
        return html_path.read_text(encoding="utf-8")

    @app.post("/api/chat")
    async def chat(body: ChatBody) -> dict[str, Any]:
        if _qa is None:
            raise HTTPException(503, "向量库或 QA 链未加载")

        text = body.message.strip()
        if not text:
            raise HTTPException(400, "消息不能为空")

        
        sid = body.session_id or str(uuid.uuid4())
        try:
            reply = _qa.ask(text)
        except Exception as e:
            raise HTTPException(500, f"{type(e).__name__}: {e}")

        return {"reply": reply, "session_id": sid}

    @app.post("/api/session/reset")
    async def reset_session(body: dict[str, Any]) -> dict[str, str]:
        """新会话：丢弃旧 session 的历史。"""
        return {"session_id": str(uuid.uuid4())}

    if _STATIC_DIR.is_dir():
        app.mount(
            "/static",
            StaticFiles(directory=str(_STATIC_DIR)),
            name="static",
        )

    return app
