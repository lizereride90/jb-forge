"""forge/loop.py — stdlib-only attack loop (sync)."""
from __future__ import annotations
import pathlib
import random
import sqlite3
import time
from .generator import Generator
from .judge import Judge

SCHEMA = """CREATE TABLE IF NOT EXISTS runs(
id INTEGER PRIMARY KEY, ts REAL, goal TEXT, persona TEXT, technique TEXT,
seed_id TEXT, target TEXT, works INTEGER, score REAL, judge TEXT, prompt TEXT)"""


class ForgeLoop:
    def __init__(self, db: pathlib.Path = pathlib.Path("dashboard/runs.db")):
        self.db = pathlib.Path(db)
        self.db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db) as c:
            c.execute(SCHEMA)
        self.gen = Generator()

    def _log(self, row: dict):
        with sqlite3.connect(self.db) as c:
            c.execute("INSERT INTO runs(ts,goal,persona,technique,seed_id,target,works,score,judge,prompt)"
                      " VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (time.time(), row["goal"], row["persona"], row["technique"],
                       row["seed_id"], row["target"], int(row["works"]),
                       row["score"], str(row["judge"]), row["prompt"][:2000]))

    def attack(self, goal, targets, judge_target=None,
               personas=("ratman3000", "cowmoo90"),
               rounds=3, per_round=4, confirm_k=3, seed=4080):
        rng = random.Random(seed)
        judge = Judge(judge_target or (targets[0] if targets else None))
        tech_ids = [t["id"] for t in self.gen.techniques]
        results = []
        for _ in range(rounds):
            batch = []
            for _ in range(per_round):
                b = self.gen.build(goal, persona=rng.choice(list(personas)),
                                   technique=rng.choice(tech_ids),
                                   seed=rng.randint(0, 99999))
                if results and rng.random() < 0.4:
                    b["prompt"] = self.gen.mutate(rng.choice(results)["prompt"], goal, rng)
                batch.append(b)
            for b in batch:
                tgt = rng.choice(targets)
                res = judge.test(b["prompt"], goal, tgt, confirm_k=confirm_k)
                row = {**b, **res, "goal": goal, "target": tgt.name,
                       "judge": res["judge"], "prompt": b["prompt"]}
                results.append(row)
                self._log(row)
                if res["works"]:
                    return sorted(results, key=lambda x: -x["score"])
        return sorted(results, key=lambda x: -x["score"])
