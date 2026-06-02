"""Training checkpoint: tracks completed (epoch, task) pairs across runs.

Each entry maps (epoch, question) -> was_correct so that:
  - Completed tasks are skipped on resume without re-spending LLM calls.
  - Accuracy counts in the epoch summary remain correct for skipped tasks.
  - If CallBudgetExceeded fires mid-task, that task is NOT recorded, so it
    retries cleanly next run (no partial state).

Swap the save/load methods for SQLite if you want queryable history later.
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Checkpoint:
    # (epoch, question) -> was_correct
    entries: Dict[Tuple[int, str], bool] = field(default_factory=dict)

    def is_done(self, epoch: int, question: str) -> bool:
        return (epoch, question) in self.entries

    def was_correct(self, epoch: int, question: str) -> bool:
        return self.entries.get((epoch, question), False)

    def mark_done(self, epoch: int, question: str, correct: bool) -> None:
        self.entries[(epoch, question)] = correct

    def summary(self) -> str:
        total = len(self.entries)
        correct = sum(self.entries.values())
        return f"{total} tasks completed ({correct} correct) across all runs"

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(
                {"entries": [[e, q, c] for (e, q), c in sorted(self.entries.items())]},
                f,
                indent=2,
            )

    @classmethod
    def load(cls, path: str) -> "Checkpoint":
        if not os.path.exists(path):
            return cls()
        with open(path) as f:
            data = json.load(f)
        cp = cls()
        cp.entries = {(e, q): c for e, q, c in data.get("entries", [])}
        return cp

    @staticmethod
    def delete(path: str) -> None:
        if os.path.exists(path):
            os.remove(path)
