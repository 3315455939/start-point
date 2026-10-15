# multi-agent —— ReAct 多智能体客服

单文件实现的多智能体客服系统（`multi_agent_system.py`，约 15 KB）。

## 结构

```
接待 Agent        无工具，只做意图识别的 JSON 路由，不参与 Action/Observation 循环
 ├─ 售前 Agent     ReAct
 ├─ 技术支持 Agent  ReAct
 └─ 主管 Agent     兜底
```

各子 Agent 使用符合 ReAct 范式的循环（Thought / Action / Observation / Final Answer），
由 LangChain 的 `create_agent` 驱动。

## 依赖

```
python-dotenv
langchain
langchain-core
langchain-openai
langgraph
```

`langgraph` 未在文件头直接 import，但 docstring 声明由它驱动；若运行时报缺包，装它。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

同目录建 `.env`（LLM 走 OpenAI 兼容接口，`langchain_openai.ChatOpenAI`）：

```
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=可选，指向兼容网关
```

```powershell
python multi_agent_system.py
```

## 构建入口

`requirements.txt`（依赖声明）。

## 状态

单文件原型。未拆分模块、无测试、无配置外置。
