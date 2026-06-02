"""The ACE loop: Generator -> execute -> grade -> Reflect -> Curate."""
from typing import Dict, List, Optional

from .checkpoint import Checkpoint
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


def train(
    conn,
    schema: str,
    playbook: Playbook,
    tasks: List[Dict],
    epochs: int = 2,
    checkpoint: Optional[Checkpoint] = None,
    checkpoint_path: Optional[str] = None,
):
    """Run the ACE loop, growing the playbook from failures. Returns accuracy history.

    If a checkpoint is provided, already-completed (epoch, task) pairs are skipped
    so the run resumes exactly where the previous call budget ran out. The checkpoint
    is written to disk after every successfully completed task, so a mid-task budget
    exhaustion never leaves partial state.
    """
    history = []
    for epoch in range(1, epochs + 1):
        correct = 0
        for task in tasks:
            q = task["question"]

            if checkpoint and checkpoint.is_done(epoch, q):
                if checkpoint.was_correct(epoch, q):
                    correct += 1
                print(f"  . (skip ep{epoch}) {q[:55]!r}")
                continue

            res = attempt(conn, schema, playbook, task)
            if res["correct"]:
                correct += 1
            else:
                lesson = reflect(q, schema, res["sql"], res["error"])
                tag = "+playbook" if curate(playbook, lesson) else "dup"
                print(f"  x {q[:55]!r} -> learned ({tag}): {lesson}")

            # Only reach here if both generate (and reflect, if needed) succeeded.
            if checkpoint is not None:
                checkpoint.mark_done(epoch, q, res["correct"])
                if checkpoint_path:
                    checkpoint.save(checkpoint_path)

        acc = correct / len(tasks)
        history.append(acc)
        print(
            f"Epoch {epoch}: accuracy {correct}/{len(tasks)} = {acc:.0%}"
            f"  | playbook size {len(playbook.bullets)}"
        )
    return history
