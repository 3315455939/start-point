"""
SQLite 学籍库（演示用）：学生、课程、成绩。

定位：
- 所有查询都走**参数化 SQL**（避免注入），返回给模型的是“可读文本表格”。

典型调用链：
- `ensure_db()`：初始化表结构；若空库则写入 demo 数据
- `tool_*()`：面向 Agent 的工具函数（列学生、列课程、查某课排名、查某人各科成绩等）
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  student_no TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  code TEXT
);

CREATE TABLE IF NOT EXISTS grades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
  score REAL NOT NULL,
  UNIQUE(student_id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_grades_course ON grades(course_id);
CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
"""


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    """返回指定表的行数。"""
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def seed_demo_data(conn: sqlite3.Connection) -> None:
    """示例数据：10 名学生 × 3 门课（计算机、高等数学、大学英语），每人 3 条成绩。"""
    students = [
        ("张三", "S2024001"),
        ("李四", "S2024002"),
        ("王五", "S2024003"),
        ("赵六", "S2024004"),
        ("钱七", "S2024005"),
        ("孙八", "S2024006"),
        ("周九", "S2024007"),
        ("吴十", "S2024008"),
        ("郑十一", "S2024009"),
        ("冯十二", "S2024010"),
    ]
    courses = [
        ("计算机", "CS101"),
        ("高等数学", "MATH101"),
        ("大学英语", "ENG101"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO students (name, student_no) VALUES (?, ?)",
        students,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO courses (name, code) VALUES (?, ?)",
        courses,
    )

    def sid(name: str) -> int:
        r = conn.execute(
            "SELECT id FROM students WHERE name = ?", (name,)
        ).fetchone()
        assert r is not None
        return int(r[0])

    def cid(cname: str) -> int:
        r = conn.execute(
            "SELECT id FROM courses WHERE name = ?", (cname,)
        ).fetchone()
        assert r is not None
        return int(r[0])

    course_names = ["计算机", "高等数学", "大学英语"]
    # 每名同学一行：[计算机, 高等数学, 大学英语]
    score_rows: list[list[float]] = [
        [100.0, 88.0, 92.0],
        [95.0, 90.0, 85.0],
        [90.0, 95.0, 80.0],
        [85.0, 82.0, 78.0],
        [78.0, 88.0, 90.0],
        [92.0, 76.0, 84.0],
        [88.0, 91.0, 79.0],
        [83.0, 85.0, 92.0],
        [91.0, 87.0, 86.0],
        [79.0, 80.0, 88.0],
    ]
    for (sname, _), scores in zip(students, score_rows, strict=True):
        for cname, score in zip(course_names, scores, strict=True):
            conn.execute(
                """
                INSERT OR REPLACE INTO grades (student_id, course_id, score)
                VALUES (?, ?, ?)
                """,
                (sid(sname), cid(cname), float(score)),
            )


def ensure_db(db_path: str) -> None:
    """创建表结构；若为空则写入示例数据。"""
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        if _count_rows(conn, "students") == 0:
            # 仅当库是空的才 seed，避免重复运行覆盖用户数据。
            seed_demo_data(conn)
            conn.commit()
    finally:
        conn.close()


def reseed_db(db_path: str) -> None:
    """清空学生/课程/成绩并重新写入 10 人 × 3 课示例数据。"""
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM grades")
        conn.execute("DELETE FROM students")
        conn.execute("DELETE FROM courses")
        conn.commit()
        seed_demo_data(conn)
        conn.commit()
    finally:
        conn.close()


def _fmt_rows(headers: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "（无记录）"
    lines = ["\t".join(headers)]
    for r in rows:
        lines.append("\t".join(str(x) for x in r))
    return "\n".join(lines)


def get_schema_text() -> str:
    """返回供大模型生成 SQL 使用的精简 schema 描述。"""
    return """
可用 SQLite 表：

1. students
- id INTEGER PRIMARY KEY
- name TEXT
- student_no TEXT

2. courses
- id INTEGER PRIMARY KEY
- name TEXT
- code TEXT

3. grades
- id INTEGER PRIMARY KEY
- student_id INTEGER -> students.id
- course_id INTEGER -> courses.id
- score REAL

常见关联：
- grades.student_id = students.id
- grades.course_id = courses.id
""".strip()


def execute_readonly_sql(db_path: str, sql: str) -> tuple[list[str], list[tuple]]:
    """
    执行只读 SQL，并返回 (列名, 行数据)。

    仅允许单条 SELECT / WITH 查询，禁止写操作与多语句。
    """
    text = (sql or "").strip().rstrip(";")
    upper = text.upper()
    if not text:
        raise ValueError("SQL 不能为空。")
    if ";" in text:
        raise ValueError("仅允许单条 SQL。")
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise ValueError("仅允许 SELECT / WITH 只读查询。")

    banned = [
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "DROP ",
        "ALTER ",
        "CREATE ",
        "REPLACE ",
        "ATTACH ",
        "DETACH ",
        "PRAGMA ",
    ]
    if any(token in upper for token in banned):
        raise ValueError("检测到非只读 SQL，已拒绝执行。")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(text)
        rows = cur.fetchall()
        headers = [d[0] for d in (cur.description or [])]
        return headers, rows
    finally:
        conn.close()


def format_query_result(headers: list[str], rows: list[tuple]) -> str:
    """把 SQL 查询结果格式化成模型易读文本。"""
    return _fmt_rows(headers, rows)


def tool_list_students(db_path: str) -> str:
    """工具：列出全部学生。"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT id, name, student_no FROM students ORDER BY id"
        )
        rows = cur.fetchall()
        return _fmt_rows(["id", "姓名", "学号"], rows)
    finally:
        conn.close()


def tool_list_courses(db_path: str) -> str:
    """工具：列出全部课程。"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT id, name, code FROM courses ORDER BY id"
        )
        rows = cur.fetchall()
        return _fmt_rows(["id", "课程名", "课程代码"], rows)
    finally:
        conn.close()


def tool_list_all_grades(db_path: str) -> str:
    """工具：列出全部成绩行。"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            """
            SELECT s.name, c.name, g.score
            FROM grades g
            JOIN students s ON s.id = g.student_id
            JOIN courses c ON c.id = g.course_id
            ORDER BY s.name, c.name
            """
        )
        rows = cur.fetchall()
        return _fmt_rows(["姓名", "课程", "成绩"], rows)
    finally:
        conn.close()


def tool_top_students_by_course(
    db_path: str, course_name: str, limit: int
) -> str:
    """工具：某课程分数最高的前 limit 名学生。"""
    limit = max(1, min(int(limit), 50))
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            """
            SELECT s.name, g.score, s.student_no
            FROM grades g
            JOIN students s ON s.id = g.student_id
            JOIN courses c ON c.id = g.course_id
            WHERE c.name = ?
            ORDER BY g.score DESC
            LIMIT ?
            """,
            (course_name.strip(), limit),
        )
        rows = cur.fetchall()
        return _fmt_rows(["姓名", "成绩", "学号"], rows)
    finally:
        conn.close()


def tool_grades_for_student(db_path: str, student_name: str) -> str:
    """工具：某学生各科成绩。"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            """
            SELECT c.name, g.score
            FROM grades g
            JOIN students s ON s.id = g.student_id
            JOIN courses c ON c.id = g.course_id
            WHERE s.name = ?
            ORDER BY c.name
            """,
            (student_name.strip(),),
        )
        rows = cur.fetchall()
        return _fmt_rows(["课程", "成绩"], rows)
    finally:
        conn.close()


def tool_grades_for_course(db_path: str, course_name: str) -> str:
    """工具：某课程全部学生成绩（降序）。"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            """
            SELECT s.name, g.score
            FROM grades g
            JOIN students s ON s.id = g.student_id
            JOIN courses c ON c.id = g.course_id
            WHERE c.name = ?
            ORDER BY g.score DESC
            """,
            (course_name.strip(),),
        )
        rows = cur.fetchall()
        return _fmt_rows(["姓名", "成绩"], rows)
    finally:
        conn.close()


def dispatch_db_tool(db_path: str, name: str, args: dict) -> str:
    """执行数据库工具，返回给模型的文本。"""
    try:
        if name == "db_list_students":
            return tool_list_students(db_path)
        if name == "db_list_courses":
            return tool_list_courses(db_path)
        if name == "db_list_all_grades":
            return tool_list_all_grades(db_path)
        if name == "db_top_students_by_course":
            course = str(args.get("course_name", "")).strip()
            lim = int(args.get("limit", 3))
            if not course:
                return "请提供参数：课程名称（course_name）。"
            return tool_top_students_by_course(db_path, course, lim)
        if name == "db_grades_for_student":
            sn = str(args.get("student_name", "")).strip()
            if not sn:
                return "请提供参数：学生姓名（student_name）。"
            return tool_grades_for_student(db_path, sn)
        if name == "db_grades_for_course":
            cn = str(args.get("course_name", "")).strip()
            if not cn:
                return "请提供参数：课程名称（course_name）。"
            return tool_grades_for_course(db_path, cn)
    except Exception as e:
        return f"数据库查询错误: {e}"
    return f"未知数据库工具: {name}"
