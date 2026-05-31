"""SQLite execution + the automatic grader (the ACE reward signal)."""
import sqlite3
from typing import Any, List, Tuple


def build_db(schema_sql: str, seed_sql: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(schema_sql)
    conn.executescript(seed_sql)
    return conn


def schema_text(conn: sqlite3.Connection) -> str:
    """The CREATE TABLE statements, fed to the Generator as schema context."""
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    return "\n\n".join(r[0] for r in rows)


def run_sql(conn: sqlite3.Connection, sql: str) -> Tuple[bool, Any]:
    """Return (ok, rows) on success, or (False, error_message) on failure."""
    try:
        return True, conn.execute(sql).fetchall()
    except Exception as e:  # surface any SQL error text to the Reflector
        return False, f"{type(e).__name__}: {e}"


def results_match(a: List, b: List) -> bool:
    """Order-insensitive comparison of two result sets."""
    return sorted(map(str, a)) == sorted(map(str, b))
