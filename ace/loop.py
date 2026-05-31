"""The ACE loop: Generator -> execute -> grade -> Reflect -> Curate."""
from typing import Dict, List

from .db import results_match, run_sql
from .playbook import Playbook
from .roles import curate, generate_sql, reflect


def attempt(conn, schema: str, playbook: Playbook, task: Dict) -> Dict:
    """One generate-and-grade pass for a single task. Does not learn."""
    sql = generate_sql(task["question"], schema, playbook)
    ok, got = run_sql(conn, sql)
    _, gold = run_sql(conn, task["gold_sql"])
    correct = ok and results_match(got, gold)

    if not ok:
        error = f"Query failed to execute: {got}"
    elif not correct:
        error = f"Wrong result set.\nGot:  {got}\nGold: {gold}"
    else:
        error = ""
    return {"sql": sql, "ok": ok, "correct": correct, "error": error, "got": got}


def train(conn, schema: str, playbook: Playbook, tasks: List[Dict], epochs: int = 2):
    """Run the ACE loop, growing the playbook from failures. Returns accuracy history."""
    history = []
    for epoch in range(1, epochs + 1):
        correct = 0
        for task in tasks:
            res = attempt(conn, schema, playbook, task)
            if res["correct"]:
                correct += 1
            else:
                lesson = reflect(task["question"], schema, res["sql"], res["error"])
                tag = "+playbook" if curate(playbook, lesson) else "dup"
                print(f"  x {task['question'][:55]!r} -> learned ({tag}): {lesson}")
        acc = correct / len(tasks)
        history.append(acc)
        print(
            f"Epoch {epoch}: accuracy {correct}/{len(tasks)} = {acc:.0%}"
            f"  | playbook size {len(playbook.bullets)}"
        )
    return history
