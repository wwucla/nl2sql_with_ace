"""The evolving playbook: an append-only list of strategy bullets.

ACE deliberately grows context with small *delta* updates instead of rewriting
it wholesale -- that's what avoids "context collapse", where a full rewrite
quietly drops hard-won lessons. So the curator only ever *appends* new bullets
(after a dedup check); it never regenerates the whole list.
"""
import json
import os
from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class Bullet:
    id: int
    lesson: str


@dataclass
class Playbook:
    bullets: List[Bullet] = field(default_factory=list)

    def render(self) -> str:
        if not self.bullets:
            return "(empty -- no strategies learned yet)"
        return "\n".join(f"- [{b.id}] {b.lesson}" for b in self.bullets)

    def add(self, lesson: str) -> bool:
        """Append a lesson as a delta. Returns False if it's an exact dup."""
        lesson = lesson.strip()
        if not lesson:
            return False
        norm = lesson.lower()
        if any(b.lesson.lower() == norm for b in self.bullets):
            return False  # cheap collapse guard; upgrade to semantic dedup if needed
        self.bullets.append(Bullet(id=len(self.bullets) + 1, lesson=lesson))
        return True

    # --- persistence ---------------------------------------------------------
    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump({"bullets": [asdict(b) for b in self.bullets]}, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "Playbook":
        if not os.path.exists(path):
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls(bullets=[Bullet(**b) for b in data.get("bullets", [])])
