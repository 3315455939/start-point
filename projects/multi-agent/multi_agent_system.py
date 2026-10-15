"""
===============================================
 Multi-Agent 客服系统（ReAct）
===============================================
目标：多智能体协作客服——接待 Agent 负责分流；售后 / 技术支持 / 主管
     各自使用符合 ReAct 范式的智能体（Thought / Action / Observation / Final Answer），
     由 LangChain `create_agent` + langgraph 驱动。

接待 Agent 无工具，仅做意图 JSON 路由，不参与 Action/Observation 循环。
"""

from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# 从项目根目录加载 .env（便于读取 ARK_API_KEY）
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# DeepSeek（OpenAI 兼容）
_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
_DEEPSEEK_MODEL = "deepseek-chat"


def _create_deepseek_llm(*, temperature: float = 0, max_tokens: int = 2000) -> ChatOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DEEPSEEK_API_KEY（DeepSeek API Key）。")
    return ChatOpenAI(
        api_key=api_key,
        base_url=_DEEPSEEK_BASE_URL,
        model=_DEEPSEEK_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=120,
        max_retries=2,
    )


# ============================================================
# 模拟数据
# ============================================================
MOCK_ORDERS = {
    "ORD-20240125-001": {"order_id": "ORD-20240125-001", "product": "StarPods Pro", "status": "shipped", "days": 10},
    "ORD-20240128-002": {"order_id": "ORD-20240128-002", "product": "StarPods Lite", "status": "delivered", "days": 3},
}
MOCK_LOGISTICS = {"ORD-20240125-001": {"courier": "顺丰", "location": "北京分拨中心", "eta": "明天"}}


# ============================================================
# 工具实现（ReAct 单字符串 Action Input）
# ============================================================
def _normalize_order_id(raw: str) -> str:
    text = (raw or "").strip().strip('"').strip("'")
    m = re.search(r"ORD-[0-9A-Za-z-]+", text)
    return m.group(0) if m else text


def _query_order_impl(order_id: str) -> str:
    return json.dumps(MOCK_ORDERS.get(order_id, {"error": "未找到"}), ensure_ascii=False)


def _query_logistics_impl(order_id: str) -> str:
    return json.dumps(MOCK_LOGISTICS.get(order_id, {"error": "暂无物流"}), ensure_ascii=False)


def _check_refund_policy_impl(product: str, days: int = 0) -> str:
    note = "在7天退货期内" if days <= 7 else f"已超7天(购于{days}天前)，但在1年质保期内"
    return json.dumps({"policy": note, "return_period": "7天", "warranty": "1年"}, ensure_ascii=False)


def _build_react_tools() -> list[Tool]:
    def query_order(action_input: str) -> str:
        """根据订单号查询订单详情。"""
        return _query_order_impl(_normalize_order_id(action_input))

    def query_logistics(action_input: str) -> str:
        """根据订单号查询物流。"""
        return _query_logistics_impl(_normalize_order_id(action_input))

    def check_refund_policy(action_input: str) -> str:
        """查询退款政策。输入：`商品名` 或 `商品名,天数`。"""
        raw = (action_input or "").strip()
        if "," in raw:
            name, days_s = raw.split(",", 1)
            try:
                days = int(days_s.strip())
            except ValueError:
                days = 0
            return _check_refund_policy_impl(name.strip(), days)
        return _check_refund_policy_impl(raw, 0)

    return [
        Tool.from_function(
            func=query_order,
            name="query_order",
            description="根据订单号查询订单详情（商品、状态等）。输入为订单号。",
        ),
        Tool.from_function(
            func=query_logistics,
            name="query_logistics",
            description="根据订单号查询物流（承运商、位置、预计到达）。输入为订单号。",
        ),
        Tool.from_function(
            func=check_refund_policy,
            name="check_refund_policy",
            description="查询退款/退货政策。输入为商品名，或 `商品名,下单天数`（如 `StarPods Pro,10`）。",
        ),
    ]


_ALL_REACT_TOOLS = _build_react_tools()
_TOOL_BY_NAME = {t.name: t for t in _ALL_REACT_TOOLS}


def _build_role_react_prompt(role_instructions: str) -> str:
    """ReAct 标准格式的系统提示词。"""
    return f"""
你是公司客服团队中的一员，按下列职责与规则工作。

【你的职责与回复规则】
{role_instructions}

【工具使用】
- 用户给出订单号时优先用 query_order / query_logistics，不要编造状态
- 退换规则用 check_refund_policy；多参数用英文逗号分隔，如 `StarPods Pro,10`
- 信息不足时先调用工具再回答，不要臆造
- 一般 1~3 次工具即可；拿到足够信息后立刻给出最终答案
- 最终答案用简洁、友好的中文，不要整段粘贴原始 JSON
""".strip()


# ============================================================
# 专业 Agent：LangChain 1.x create_agent + langgraph
# ============================================================
class ReActSpecialistAgent:
    """基于 langgraph 的专员智能体。"""

    def __init__(
        self,
        name: str,
        role: str,
        role_instructions: str,
        tool_names: list[str],
    ):
        self.name = name
        self.role = role
        tools = [_TOOL_BY_NAME[n] for n in tool_names]
        llm = _create_deepseek_llm(temperature=0)
        system_prompt = _build_role_react_prompt(role_instructions)
        self.agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )

    def process(self, message: str, context: str = "") -> dict:
        user_input = f"{context}\n\n用户消息：{message}" if context else message
        result = self.agent.invoke({"messages": [HumanMessage(content=user_input)]})
        messages = result.get("messages", [])
        reply = str(messages[-1].content) if messages else "处理完成"
        
        tool_calls = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_calls.append({
                        "tool": tool_call.get('name', ''),
                        "args": tool_call.get('args', ''),
                    })
        
        return {
            "agent": self.name,
            "reply": reply.strip(),
            "tool_calls": tool_calls,
            "react_steps": len(tool_calls),
        }


# ============================================================
# 接待 Agent（路由，无工具，非 ReAct Action 循环）
# ============================================================
class ReceptionAgent:
    """前台接待：仅输出路由 JSON，不参与 Thought/Action/Observation 工具循环。"""

    ROUTE_MAP = {
        "after_sales": "售后专员",
        "tech_support": "技术支持",
        "supervisor": "客服主管",
    }

    def __init__(self):
        self.name = "reception"
        self.role = "前台接待"
        self.llm = _create_deepseek_llm(temperature=0)
        self._system = """你是公司客服的前台接待。你的唯一工作是分析用户消息，判断该派给哪个专员处理。

可选路由：
1. after_sales（售后专员）—— 退款、退货、换货、物流查询、订单状态
2. tech_support（技术支持）—— 产品故障、使用方法、连接问题、功能咨询
3. supervisor（客服主管）—— 投诉、对之前处理不满、复杂问题、说不清的问题

请用 JSON 格式输出（不要调用工具）：
{"route": "after_sales/tech_support/supervisor", "reason": "简要原因", "extracted_info": {"order_id": "...", "product": "...", "key_info": "..."}}"""

    def route(self, message: str) -> dict:
        response = self.llm.invoke(
            [SystemMessage(content=self._system), HumanMessage(content=message)]
        )
        content = (response.content or "").strip()
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            decision = json.loads(content)
            return {
                "agent": decision.get("route", "supervisor"),
                "reason": decision.get("reason", ""),
                "extracted_info": decision.get("extracted_info", {}),
            }
        except (json.JSONDecodeError, IndexError):
            return {"agent": "supervisor", "reason": "无法识别意图，转主管处理", "extracted_info": {}}


# ============================================================
# 各专业角色（不同 Prompt + 不同工具子集）
# ============================================================
class AfterSalesAgent(ReActSpecialistAgent):
    """售后专员 —— ReAct + 订单 / 物流 / 退款政策。"""

    def __init__(self):
        super().__init__(
            name="after_sales",
            role="售后专员",
            role_instructions="""
1. 查到结果后用自然语言总结，不要返回原始数据
2. 退款/退货引导用户在 APP 中申请
3. 物流问题告知当前位置和预计到达时间
4. 超出退货期但在质保期内的情况要主动说明
5. 语气亲切专业，简洁不废话""",
            tool_names=["query_order", "query_logistics", "check_refund_policy"],
        )


class TechSupportAgent(ReActSpecialistAgent):
    """技术支持 —— ReAct + 仅订单查询（核对型号与购买记录时可查）。"""

    def __init__(self):
        super().__init__(
            name="tech_support",
            role="技术支持工程师",
            role_instructions="""
1. 先了解具体症状和产品型号
2. 给出逐步排查建议；需要核对订单信息时可使用 query_order
3. 如果是硬件故障，建议用户申请售后维修
4. 语气专业耐心，避免使用过于技术化的术语""",
            tool_names=["query_order"],
        )


class SupervisorAgent(ReActSpecialistAgent):
    """客服主管 —— ReAct + 全量工具兜底。"""

    def __init__(self):
        super().__init__(
            name="supervisor",
            role="客服主管",
            role_instructions="""
1. 投诉用户要先安抚情绪，表示重视
2. 了解问题全貌后再给出方案
3. 可以给出补偿方案（如优惠券、延长质保等）
4. 复杂问题及时创建工单并分配跟进
5. 语气诚恳，展现解决问题的诚意""",
            tool_names=["query_order", "query_logistics", "check_refund_policy"],
        )


# ============================================================
# Multi-Agent 系统调度器
# ============================================================
class MultiAgentSystem:
    """多智能体客服系统：接待路由 + 各专员执行。"""

    def __init__(self):
        self.reception = ReceptionAgent()
        self.agents = {
            "after_sales": AfterSalesAgent(),
            "tech_support": TechSupportAgent(),
            "supervisor": SupervisorAgent(),
        }

    def chat(self, user_message: str) -> dict:
        """
        处理用户消息的完整流程：
        1. 接待 Agent 分析意图（无工具）
        2. 分配给对应的专业 Agent
        3. 专业 Agent 调用工具并输出最终答案
        """
        print(f"\n  [系统] 用户消息：{user_message}")

        print("  [接待] 正在分析意图...")
        route_decision = self.reception.route(user_message)
        target_agent = route_decision["agent"]
        reason = route_decision["reason"]
        extracted_info = route_decision.get("extracted_info", {})

        print(f"  [接待] 路由决策：{self.reception.ROUTE_MAP.get(target_agent, target_agent)}")
        print(f"  [接待] 原因：{reason}")

        agent = self.agents.get(target_agent, self.agents["supervisor"])
        print(f"  [{agent.role}] 处理中...")

        context = ""
        if extracted_info:
            context = f"接待 Agent 提取的信息：{json.dumps(extracted_info, ensure_ascii=False)}"

        result = agent.process(user_message, context=context)

        return {
            "reply": result["reply"],
            "routed_to": agent.role,
            "route_reason": reason,
            "tool_calls": result.get("tool_calls", []),
            "react_steps": result.get("react_steps", 0),
        }


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("第九章 示例 4：Multi-Agent 客服系统（专业线 ReAct）")
    print("=" * 60)

    system = MultiAgentSystem()

    test_cases = [
        ("我的耳机有杂音怎么办？", "技术问题"),
        ("我要查一下订单 ORD-20240125-001 到哪了", "物流查询"),
        ("你们这个耳机质量太差了！用了两天就坏了，我要投诉！", "投诉"),
        ("StarPods Pro 买了 10 天了能退吗？", "退货咨询"),
    ]

    for question, desc in test_cases:
        print(f"\n{'=' * 60}")
        print(f"测试：{desc}")
        print(f"用户：{question}")
        print("-" * 60)

        result = system.chat(question)

        print(f"\n  [结果] 分配给：{result['routed_to']}")
        print(f"  [结果] 工具调用次数：{result.get('react_steps', 0)}")
        print(f"  [结果] 回复：{result['reply']}")
        if result["tool_calls"]:
            print("  [结果] 工具调用轨迹：")
            for idx, log in enumerate(result["tool_calls"], start=1):
                print(f"    Step {idx}: {log['tool']}({log['args']!r})")

    print("\n" + "=" * 60)
    print("关键要点：")
    print("  1. 专业 Agent 使用 langchain.agents.create_agent + langgraph")
    print("  2. 接待 Agent 无工具，只做 JSON 路由")
    print("  3. 各专员不同工具子集与职责 Prompt，多智能体分工清晰")
    print("=" * 60)