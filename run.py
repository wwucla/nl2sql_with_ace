#!/usr/bin/env python3
"""nl2sql_with_ace -- a tiny Agentic Context Engineering demo.

Usage:
  python run.py train            # resume (or start) training; saves checkpoint
  python run.py train --reset    # wipe checkpoint + playbook and train from scratch
  python run.py eval             # score the current playbook, no learning
  python run.py ask "question"   # answer one NL question with current playbook
"""
import json
import os
import sys

from ace.checkpoint import Checkpoint
from ace.db import build_db, run_sql, schema_text
from ace.llm import CallBudgetExceeded
from ace.loop import attempt, train
from ace.playbook import Playbook
from ace.roles import generate_sql

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PLAYBOOK_PATH = os.path.join(ROOT, "playbook.json")
CHECKPOINT_PATH = os.path.join(ROOT, "checkpoint.json")


def load_env() -> None:
    """Minimal .env loader so the demo has no extra dependency for it."""
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def setup():
    schema_sql = open(os.path.join(DATA, "schema.sql")).read()
    seed_sql = open(os.path.join(DATA, "seed.sql")).read()
    conn = build_db(schema_sql, seed_sql)
    tasks = [
        json.loads(line)
        for line in open(os.path.join(DATA, "tasks.jsonl"))
        if line.strip()
    ]
    return conn, schema_text(conn), tasks


def main() -> None:
    load_env()
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    flags = set(sys.argv[2:])
    conn, schema, tasks = setup()

    try:
        if cmd == "train":
            reset = "--reset" in flags

            if reset:
                Checkpoint.delete(CHECKPOINT_PATH)
                Playbook().save(PLAYBOOK_PATH)
                print("Reset: checkpoint and playbook cleared.")

            playbook = Playbook.load(PLAYBOOK_PATH)
            checkpoint = Checkpoint.load(CHECKPOINT_PATH)

            if not reset and checkpoint.entries:
                print(f"Resuming: {checkpoint.summary()}")

            try:
                train(
                    conn, schema, playbook, tasks,
                    epochs=int(os.environ.get("EPOCHS", 2)),
                    checkpoint=checkpoint,
                    checkpoint_path=CHECKPOINT_PATH,
                )
            finally:
                playbook.save(PLAYBOOK_PATH)
                print(f"\nSaved playbook -> {PLAYBOOK_PATH}")

        elif cmd == "eval":
            playbook = Playbook.load(PLAYBOOK_PATH)
            correct = sum(attempt(conn, schema, playbook, t)["correct"] for t in tasks)
            print(f"accuracy {correct}/{len(tasks)} = {correct / len(tasks):.0%}")

        elif cmd == "ask":
            if len(sys.argv) < 3:
                print('usage: python run.py ask "your question"')
                return
            playbook = Playbook.load(PLAYBOOK_PATH)
            sql = generate_sql(sys.argv[2], schema, playbook)
            ok, rows = run_sql(conn, sql)
            print(f"\nSQL:\n{sql}\n")
            print("Result:" if ok else "Error:")
            if ok:
                for r in rows:
                    print(" ", r)
            else:
                print(" ", rows)

        else:
            print(__doc__)

    except CallBudgetExceeded as e:
        print(f"\n[stopped] {e}")
        print("Run `python run.py train` again to continue from where it stopped.")


if __name__ == "__main__":
    main()
