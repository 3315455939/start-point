# react-rag-db新手运行指南

本文档说明如何在 Windows / macOS / Linux 上，从零运行本仓库的 **PDF 向量检索（Chroma + RAG）** 与 **学籍 SQLite + ReAct 智能体问答**。

---

## 一、项目是做什么的？

本仓库实现了一个「混合问答」演示系统：

| 能力 | 技术 | 用途 |
|------|------|------|
| PDF 知识库 | `PyPDFLoader` → 文本切分 → `DashScopeEmbeddings` → `Chroma` | 回答校史、学校介绍等文档类问题 |
| 学籍数据库 | SQLite（`data/school.db`） | 回答学生、课程、成绩、排名等结构化问题 |
| 智能体 | LangChain **ReAct** | 自动选择调用 RAG 或数据库工具 |
| 交互方式 | 命令行 `query`、Web 页面 `serve`、Jupyter Notebook | 三种入口任选 |

核心代码目录：`src/rag_db/`  
你当前打开的 `rag_chroma.py` 负责 **PDF 入库** 与 **构建 RetrievalQA 检索链**。

---

## 二、运行前准备

### 2.1 环境要求

- **Python 3.10 及以上**（见 `pyproject.toml`）
- 可访问互联网的终端（安装依赖、调用云端 API）
- 两个 API 密钥（对话与向量来自不同厂商，不要混用）：

| 环境变量 | 用途 | 获取方式（示例） |
|----------|------|------------------|
| `ARK_API_KEY` | 对话模型（火山方舟 / OpenAI 兼容接口） | 火山引擎控制台 → 方舟 |
| `DASHSCOPE_API_KEY` | 向量模型（通义 `text-embedding-v1`） | 阿里云 DashScope 控制台 |

### 2.2 克隆或打开项目

确保项目根目录为 `react-rag-db`（内含 `pyproject.toml`、`src/rag_db/`）。

```powershell
cd D:\gtcode\react-rag-db
```

后续所有命令均在**项目根目录**执行，除非特别说明。

---

## 三、安装依赖（推荐：虚拟环境）

### 3.1 创建并激活虚拟环境

**Windows（PowerShell）：**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux：**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3.2 安装项目与依赖

任选其一：

```powershell
# 方式 A：可编辑安装（推荐，支持 react-rag-db 命令）
pip install -e .

# 方式 B：仅安装 requirements.txt
pip install -r requirements.txt
pip install -e .
```

LangChain 读 PDF、通义向量可能还需要额外包（若报错再装）：

```powershell
pip install pypdf dashscope
```

验证 Python 能导入包：

```powershell
python -c "import rag_db; print('OK')"
```

---

## 四、配置 API 密钥

在项目根目录新建 `.env` 文件（已被 `.gitignore` 忽略，勿提交到 Git）：

```env
# 火山方舟：对话模型（ReAct 智能体、Web 问答）
ARK_API_KEY=你的方舟_API_Key

# 阿里云 DashScope：向量嵌入（PDF 入库、检索）
DASHSCOPE_API_KEY=你的通义_API_Key

# 可选：HTTP 超时秒数，默认 600
# RAG_HTTP_TIMEOUT=600
```

程序启动时会通过 `python-dotenv` 自动加载根目录 `.env`（见 `src/rag_db/config.py`）。

也可在系统环境变量中设置同名变量，效果相同。

---

## 五、准备数据文件

### 5.1 PDF 文档

将待入库的 PDF 放到项目根目录，命名为 **`document.pdf`**（默认路径）。

- 若没有 PDF，使用 **Jupyter 引导脚本** 可自动生成示例 PDF（见第七节）。
- 也可在入库时指定路径：`--pdf 你的文件.pdf`

### 5.2 学籍演示库

初始化 SQLite（10 名学生、3 门课、成绩示例）：

```powershell
python init_school_db.py
```

强制清空并重新灌入：

```powershell
python init_school_db.py --force
```

成功后应有：`data/school.db`

---

## 六、核心流程：PDF 入库 → 问答

整体流程：

```
document.pdf  →  ingest  →  data/index（Chroma）  →  query / serve  →  回答
                ↑
         需要 DASHSCOPE_API_KEY
```

### 6.1 构建向量库（ingest）

任选一种方式：

**方式 1：一键脚本（最适合新手）**

```powershell
python ingest_ecust.py
```

**方式 2：模块命令**

```powershell
python -m rag_db ingest --pdf document.pdf --out data/index
```

**方式 3：安装后的 CLI**

```powershell
react-rag-db ingest --pdf document.pdf --out data/index
```

成功时会打印类似：`已写入 N 个 chunk 到 Chroma 目录：data/index`

入库逻辑在 `rag_chroma.py` 的 `ingest_pdf_to_chroma()`：

1. `PyPDFLoader` 读取 PDF  
2. `RecursiveCharacterTextSplitter` 切分（默认 chunk 1000、重叠 180）  
3. `DashScopeEmbeddings` 生成向量  
4. 写入本地 Chroma（`persist_directory=data/index`）

**判断是否入库成功：** 目录 `data/index` 下应出现 Chroma 相关文件（如 `chroma.sqlite3`）。若只有旧的 `meta.json` 而没有 Chroma 文件，请重新执行 ingest。

可选参数示例：

```powershell
python -m rag_db ingest --pdf document.pdf --out data/index --chunk-size 800 --chunk-overlap 120
```

### 6.2 终端交互问答（query）

需要：**ARK_API_KEY**、已入库的 `data/index`、`data/school.db`

```powershell
python -m rag_db query
```

指定路径：

```powershell
python -m rag_db query --index data/index --db data/school.db --top-k 5
```

在提示符 `你:` 后输入问题，空行退出。智能体会根据问题类型自动选择 RAG 或数据库工具。

**示例问题：**

- 文档类：`RAG 知识库中有什么内容？`
- 数据库类：`张三各科成绩是多少？` / `数据结构这门课谁排第一？`

### 6.3 启动 Web 对话界面（serve）

```powershell
python serve_web.py
```

或：

```powershell
python -m rag_db serve --host 127.0.0.1 --port 8000
```

浏览器访问：**http://127.0.0.1:8000/**  
`serve_web.py` 会自动尝试打开浏览器。

---

## 七、Jupyter Notebook 方式（可选）

适合课堂演示：自动检查依赖、生成示例 PDF、自动入库。

1. 在项目根目录启动 Jupyter：

   ```powershell
   jupyter notebook
   ```

2. 在 Notebook **第一个单元格** 执行：

   ```python
   exec(open("notebook_bootstrap.py", encoding="utf-8").read())
   ```

   或在任意目录通过 `run_bootstrap.py` 定位项目根后执行引导。

3. 引导完成后可使用：

   ```python
   from rag_db.react_agent_qa import build_react_agent_qa
   
   qa = build_react_agent_qa("data/index", "data/school.db")
   print(qa.ask("学校有哪些校区？"))
   ```

`notebook_bootstrap.py` 会调用 `ensure_index()`、`ensure_db()`，在缺少向量库时自动 ingest（需已配置两个 API Key）。

---

## 八、命令速查表

| 目标 | 命令 |
|------|------|
| 安装依赖 | `pip install -e .` |
| 初始化学籍库 | `python init_school_db.py` |
| PDF 入库 | `python ingest_ecust.py` 或 `python -m rag_db ingest` |
| 终端问答 | `python -m rag_db query` |
| Web 服务 | `python serve_web.py` 或 `python -m rag_db serve` |
| 查看子命令帮助 | `python -m rag_db -h` |

---

## 九、目录结构说明

```
react-rag-db/
├── .env                    # 本地密钥（需自行创建）
├── document.pdf               # 待入库 PDF（需自行准备或 Notebook 生成）
├── ingest_ecust.py         # 一键入库
├── init_school_db.py       # 一键初始化学籍库
├── serve_web.py            # 一键启动 Web
├── notebook_bootstrap.py   # Notebook 环境引导
├── requirements.txt
├── pyproject.toml
├── data/
│   ├── index/              # Chroma 向量库（ingest 后生成）
│   └── school.db           # SQLite 学籍库
└── src/rag_db/
    ├── rag_chroma.py       # Chroma RAG 入库与检索链
    ├── react_agent_qa.py   # ReAct 智能体
    ├── main.py             # CLI 入口
    └── web.py              # FastAPI Web
```

---

## 十、常见问题排查

### 10.1 `请配置环境变量 ARK_API_KEY`

- 检查项目根目录是否有 `.env`，且变量名正确。  
- 重新打开终端，确认已 `Activate` 虚拟环境。  
- **query / serve** 需要此密钥；**仅 ingest** 主要需要 `DASHSCOPE_API_KEY`。

### 10.2 `DASHSCOPE_API_KEY` 相关 / 向量化失败

- ingest 阶段必须配置通义密钥。  
- 确认已安装：`pip install dashscope langchain-community`

### 10.3 `未找到 PDF 文件`

- 将 PDF 放到根目录并命名为 `document.pdf`，或使用 `--pdf` 指定完整路径。

### 10.4 `未找到向量库目录` / 检索无结果

- 先执行第六节 ingest。  
- 确认 `data/index` 中存在 Chroma 持久化文件，而非仅有旧版 `meta.json`。

### 10.5 `ModuleNotFoundError: rag_db`

- 在项目根目录执行命令。  
- 或：`pip install -e .`  
- 或临时：`set PYTHONPATH=src`（Windows）/ `export PYTHONPATH=src`（Linux）

### 10.6 `PyPDFLoader` / `pypdf` 报错

```powershell
pip install pypdf
```

### 10.7 Web 启动后页面打不开

- 检查 8000 端口是否被占用，可换端口：`python -m rag_db serve --port 8080`  
- 防火墙是否拦截本地访问。

### 10.8 调用超时

- 在 `.env` 中增大：`RAG_HTTP_TIMEOUT=900`

---

