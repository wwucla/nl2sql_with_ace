"""The three ACE roles: Generator, Reflector, Curator."""
from .llm import complete
from .playbook import Playbook

GENERATOR_SYSTEM = """You are an expert SQLite query writer.
Given a database schema, a learned playbook of strategies, and a question,
output ONE SQLite query that answers it.
Return ONLY the SQL -- no markdown fences, no explanation."""


def generate_sql(question: str, schema: str, playbook: Playbook) -> str:
    user = f"""Schema:
{schema}

Playbook (lessons from past attempts -- follow them):
{playbook.render()}

Question: {question}

SQL:"""
    return _strip_fences(complete(GENERATOR_SYSTEM, user))


REFLECTOR_SYSTEM = """You diagnose failed SQL attempts.
Given the question, the schema, the SQL that was tried, and what went wrong,
state the SINGLE most useful general lesson to avoid this mistake next time.
Make it a concrete, reusable rule -- not specific to this one question.
Answer in one sentence, with no preamble."""


def reflect(question: str, schema: str, sql: str, error: str) -> str:
    user = f"""Schema:
{schema}

Question: {question}
SQL tried:
{sql}

What went wrong:
{error}

Lesson:"""
    return complete(REFLECTOR_SYSTEM, user).strip()


def curate(playbook: Playbook, lesson: str) -> bool:
    """Append the lesson to the playbook as a delta if it's genuinely new."""
    return playbook.add(lesson)


def _strip_fences(sql: str) -> str:
    """Tolerate models that wrap SQL in ```sql ... ``` fences."""
    s = sql.strip()
    if s.startswith("```"):
        s = s[3:]
        if s[:3].lower() == "sql":
            s = s[3:]
        if "```" in s:
            s = s[: s.index("```")]
    return s.strip()
