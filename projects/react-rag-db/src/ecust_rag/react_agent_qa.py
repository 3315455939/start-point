"""
基于 LangChain ReAct 的问答智能体。

智能体通过工具自主决定：
- 何时查询 PDF RAG 知识库
- 何时查询 SQLite 学籍库
- 何时先查库再整理答案
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from ecust_rag.config import API_KEY, BASE_URL, CHAT_MODEL, HTTP_TIMEOUT
from ecust_rag.db import (
    ensure_db,
    execute_readonly_sql,
    format_query_result,
    get_schema_text,
    tool_grades_for_course,
    tool_grades_for_student,
    tool_list_all_grades,
    tool_list_courses,
    tool_list_students,
    tool_top_students_by_course,
)
from ecust_rag.rag_chroma import build_retrieval_qa


def _get_chat_model() -> ChatOpenAI:
    if not API_KEY:
        raise RuntimeError("请先配置环境变量 ARK_API_KEY（用于对话模型）。")
    return ChatOpenAI(
        model=CHAT_MODEL,
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=HTTP_TIMEOUT,
        max_retries=2,
        temperature=0,
    )


def _build_react_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(
        """
你是华东理工大学问答智能体，需要基于工具完成回答。

你有两类信息源：
1. PDF/RAG：学校介绍、校史、学院说明、制度文档等文本知识
2. SQLite 成绩库：学生、课程、成绩、排名等结构化数据

数据库 schema 摘要：
{schema_text}

你必须遵守：
- 涉及学生、课程、成绩、分数、排名、平均分等结构化信息时，优先使用数据库工具
- 涉及学校介绍、校史、文档内容时，使用 rag_search
- 如果信息不足，先调用工具再回答，不要臆造
- 使用 `db_sql_query` 时只能传入单条只读 SQL
- 一般最多调用 1 到 2 次工具；拿到足够信息后立即输出 Final Answer
- 最终答案用简洁中文作答

你可以使用以下工具：

{tools}

请严格使用以下格式：

Question: 用户问题
Thought: 你应该先思考
Action: 要调用的工具名，必须是 [{tool_names}]
Action Input: 工具输入
Observation: 工具返回结果
...（Thought/Action/Action Input/Observation 可重复多轮）
Thought: 我已经得到最终答案
Final Answer: 对用户的最终回答

重要格式约束：
- 同一轮输出里，`Action` 和 `Final Answer` 只能二选一，绝对不能同时出现
- 只要你输出了 `Action:`，这一轮就必须结束，等待 `Observation`
- 没有看到工具返回的 `Observation` 前，不要输出 `Final Answer`
- 当信息已经足够时，直接输出 `Final Answer`，不要继续调用工具

Question: {input}
Thought:{agent_scratchpad}
""".strip()
    ).partial(schema_text=get_schema_text())


def _build_tools(rag_qa: object, db_path: str) -> list[Tool]:
    def rag_search(question: str) -> str:
        """查询 PDF 向量库，适合学校介绍、校史和文档问答。"""
        result = rag_qa.invoke({"query": question})
        return str(result.get("result", "")).strip()

    def db_sql_query(sql: str) -> str:
        """执行单条只读 SQL 查询，适合复杂统计、排序和筛选。"""
        headers, rows = execute_readonly_sql(db_path, sql)
        return format_query_result(headers, rows)

    def db_list_students_tool(_: str) -> str:
        """列出全部学生。"""
        return tool_list_students(db_path)

    def db_list_courses_tool(_: str) -> str:
        """列出全部课程。"""
        return tool_list_courses(db_path)

    def db_list_all_grades_tool(_: str) -> str:
        """列出全部学生成绩。"""
        return tool_list_all_grades(db_path)

    def db_top_students_by_course_tool(text: str) -> str:
        """按课程查询前 N 名学生。"""
        raw = (text or "").strip()
        course_name = raw
        limit = 3
        if "," in raw:
            course_name, limit_text = raw.split(",", 1)
            try:
                limit = int(limit_text.strip())
            except ValueError:
                limit = 3
        return tool_top_students_by_course(db_path, course_name.strip(), limit)

    def db_grades_for_student_tool(student_name: str) -> str:
        """查询某学生各门课成绩。"""
        return tool_grades_for_student(db_path, student_name)

    def db_grades_for_course_tool(course_name: str) -> str:
        """查询某门课所有学生成绩。"""
        return tool_grades_for_course(db_path, course_name)

    return [
        Tool.from_function(
            func=rag_search,
            name="rag_search",
            description="查询 PDF 向量库中的学校文档内容。输入应为自然语言问题。",
        ),
        Tool.from_function(
            func=db_sql_query,
            name="db_sql_query",
            description=(
                "执行 SQLite 只读 SQL。适用于复杂统计、排序、平均分、最高分、排名等问题。"
                "输入必须是单条 SELECT 或 WITH 查询。"
            ),
        ),
        Tool.from_function(
            func=db_list_students_tool,
            name="db_list_students",
            description="列出所有学生姓名和学号。若无需输入，可传空字符串。",
        ),
        Tool.from_function(
            func=db_list_courses_tool,
            name="db_list_courses",
            description="列出所有课程名称和课程代码。若无需输入，可传空字符串。",
        ),
        Tool.from_function(
            func=db_list_all_grades_tool,
            name="db_list_all_grades",
            description="列出所有学生的所有课程成绩。若无需输入，可传空字符串。",
        ),
        Tool.from_function(
            func=db_top_students_by_course_tool,
            name="db_top_students_by_course",
            description="查询某课程前 N 名。输入格式：课程名，或 `课程名,数量`，如 `计算机,5`。",
        ),
        Tool.from_function(
            func=db_grades_for_student_tool,
            name="db_grades_for_student",
            description="查询某个学生的各科成绩。输入学生姓名，如 `张三`。",
        ),
        Tool.from_function(
            func=db_grades_for_course_tool,
            name="db_grades_for_course",
            description="查询某门课全部学生成绩。输入课程名，如 `高等数学`。",
        ),
    ]


@dataclass
class ReactAgentQA:
    executor: AgentExecutor

    def ask(self, question: str) -> str:
        result = self.executor.invoke({"input": question})
        return str(result.get("output", "")).strip()


def build_react_agent_qa(
    index_path: str,
    db_path: str,
    *,
    top_k: int = 5,
) -> ReactAgentQA:
    """构建统一问答入口：ReAct 智能体 + RAG 工具 + 数据库工具。"""
    ensure_db(db_path)
    llm = _get_chat_model()
    rag_qa = build_retrieval_qa(index_path, llm=llm, top_k=top_k)
    tools = _build_tools(rag_qa, db_path)
    prompt = _build_react_prompt()
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=3,
        early_stopping_method="force",
    )
    return ReactAgentQA(executor=executor)
