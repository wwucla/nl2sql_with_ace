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


DEDUP_SYSTEM = """You are a deduplication judge for a SQL strategy playbook.
Your only job is to decide if a proposed lesson is already covered by an existing one."""


def curate(playbook: Playbook, lesson: str) -> bool:
    """Append the lesson to the playbook as a delta if it's genuinely new.

    Uses a two-pass guard:
      1. Exact string match (free) -- catches identical lessons instantly.
      2. LLM semantic judge (budget-exempt) -- catches paraphrases and near-dups
         that exact match would miss.
    """
    lesson = lesson.strip()
    if not lesson:
        return False
    if playbook.is_exact_dup(lesson):
        return False
    if playbook.bullets and _is_semantic_dup(lesson, playbook.bullets):
        return False
    return playbook.add(lesson)


def _is_semantic_dup(lesson: str, bullets) -> bool:
    """Ask the LLM if lesson is semantically equivalent to any existing bullet.

    Runs budget-exempt (count=False) so it never consumes task quota.
    Returns False on any error so a failing dedup check never silently drops lessons.
    """
    existing = "\n".join(f"- [{b.id}] {b.lesson}" for b in bullets)
    user = f"""Existing playbook lessons:
{existing}

Proposed new lesson: "{lesson}"

Does the proposed lesson express the same core idea as any existing lesson?
Answer YES if it is substantially equivalent to an existing lesson.
Answer NO if it adds genuinely new information not covered above.
Reply with exactly one word: YES or NO."""
    try:
        answer = complete(DEDUP_SYSTEM, user, count=False)
        return answer.strip().upper().startswith("YES")
    except Exception:
        return False


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
