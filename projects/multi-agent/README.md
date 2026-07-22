# Multi-Agent Customer Service System

基于 LangChain ReAct 的多智能体客服系统演示。

## 架构

- **接待 Agent**：意图路由（售后/技术支持/投诉），无工具，纯 JSON 意图识别
- **售后 Agent**：订单查询、物流追踪、退款处理（模拟数据）
- **技术支持 Agent**：产品问题诊断与解决方案推荐
- **主管 Agent**：投诉升级处理，综合决策

## 运行

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY="your-deepseek-api-key"
python multi_agent_system.py
```

## 技术栈

Python · LangChain (create_agent + langgraph) · DeepSeek Chat
