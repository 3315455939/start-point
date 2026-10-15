# react-rag-db —— ECUST RAG 问答系统

华东理工大学校园知识库的问答系统。**本项目文档最全，先读 [`新手运行指南.md`](新手运行指南.md)。**

## 它能做什么

| 能力 | 技术 | 用途 |
|---|---|---|
| PDF 知识库 | `PyPDFLoader` → 文本切分 → `DashScopeEmbeddings` → `Chroma` | 校史、学校介绍等文档类问答 |
| 学籍数据库 | SQLite（`data/school.db`） | 学生、课程、成绩、排名等结构化问答 |
| 智能体 | LangChain ReAct | 自动选择调用 RAG 或数据库工具 |
| 交互方式 | 命令行 `query`、Web 页面 `serve`、Jupyter Notebook | 三个入口任选 |

## 布局

```
src/ecust_rag/
├── config.py            配置
├── db.py                SQLite 学籍库
├── rag_chroma.py        PDF 入库 + RetrievalQA 检索链
├── react_agent_qa.py    ReAct 智能体问答
├── web.py + static/     Web 入口
├── ingest_cli.py        入库命令行
├── main.py / __main__.py  CLI 入口
ingest_ecust.py          PDF 入库脚本
init_school_db.py        学籍库初始化
serve_web.py             Web 服务启动
pyproject.toml           包定义
requirements.txt         依赖
```

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

完整步骤、环境变量与各入口用法见 [`新手运行指南.md`](新手运行指南.md)。

## 构建入口

`pyproject.toml`（可 `pip install -e .`）+ `requirements.txt`。

## 状态

功能完整、有独立文档。移除了 `src/ecust_rag.egg-info/`——那是 `pip install -e .` 的构建产物，
不应入库（已加入 `.gitignore` 的 `*.egg-info/`），需要时重新 `pip install -e .` 生成。
