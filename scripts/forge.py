"""scripts/forge.py — CLI (stdlib only): generate / attack / humanize / score."""
from __future__ import annotations
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from forge import Generator, Humanizer, score_risk, ForgeLoop
from forge.harness import targets_from_env


def cmd_generate(a):
    b = Generator().build(a.goal, persona=a.persona, technique=a.technique, seed=a.seed)
    print(f"[{b['persona']} :: {b['technique']} :: {b['seed_id']}]")
    print(b["prompt"])


def cmd_attack(a):
    tgts = targets_from_env()
    print(f"targets: {[t.name for t in tgts]}")
    res = ForgeLoop().attack(a.goal, tgts, rounds=a.rounds,
                            per_round=a.per_round, confirm_k=a.confirm_k)
    for r in res[:5]:
        print(f"\n== {'WORKS' if r['works'] else 'fail'} score={r['score']:.2f} "
              f"{r['persona']}/{r['technique']} via {r['target']} judge={r['judge']}")
        print(r["prompt"][:800])
    win = [r for r in res if r["works"]]
    if win and a.humanize:
        print("\n--- HUMANIZED WINNER ---")
        print(Humanizer().humanize(win[0]["trace"][0], aggression=a.humanize))


def cmd_humanize(a):
    text = pathlib.Path(a.file).read_text() if a.file else a.text
    h = Humanizer(seed=a.seed)
    before, out, after = score_risk(text), None, None
    out = h.humanize(text, aggression=a.aggression)
    after = score_risk(out)
    print(f"risk {before['risk']}% ({before['band']}) -> {after['risk']}% ({after['band']})")
    print(out)


def cmd_score(a):
    print(score_risk(pathlib.Path(a.file).read_text() if a.file else a.text))


def main():
    p = argparse.ArgumentParser(prog="forge")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--goal", required=True)
    g.add_argument("--persona", default="ratman3000")
    g.add_argument("--technique", default=None)
    g.add_argument("--seed", type=int, default=4080)
    g.set_defaults(fn=cmd_generate)
    at = sub.add_parser("attack")
    at.add_argument("--goal", required=True)
    at.add_argument("--rounds", type=int, default=3)
    at.add_argument("--per-round", type=int, default=4)
    at.add_argument("--confirm-k", type=int, default=3)
    at.add_argument("--humanize", type=int, default=0)
    at.set_defaults(fn=cmd_attack)
    h = sub.add_parser("humanize")
    h.add_argument("--file", default=None)
    h.add_argument("--text", default="")
    h.add_argument("--aggression", type=int, default=2)
    h.add_argument("--seed", type=int, default=4080)
    h.set_defaults(fn=cmd_humanize)
    s = sub.add_parser("score")
    s.add_argument("--file", default=None)
    s.add_argument("--text", default="")
    s.set_defaults(fn=cmd_score)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
