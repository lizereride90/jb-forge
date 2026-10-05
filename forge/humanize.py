"""forge/humanize.py — detector-resistance: local risk scorer + rewriter.

Mirrors public humanizer mechanics (humanize-cli / Humanize-AI style):
burstiness, contractions, AI-vocab swap, filler-strip, rhythm jitter.
No network needed — runs offline so output stays reproducible.
"""
from __future__ import annotations
import random
import re

AI_WORDS = {
    "additionally": "also", "furthermore": "also", "moreover": "plus",
    "consequently": "so", "nevertheless": "still", "however": "but",
    "utilize": "use", "utilizes": "uses", "leverage": "use",
    "leverage": "use", "comprehensive": "full", "robust": "solid",
    "delve": "dig", "delves": "digs", "pivotal": "key",
    "innovative": "fresh", "cutting-edge": "sharp", "seamless": "smooth",
    "testament": "proof", "landscape": "field", "realm": "area",
    "tapestry": "mix", "crucial": "key", "vital": "key",
    "showcase": "show", "enhance": "lift", "facilitate": "help",
    "implement": "build", "aforementioned": "that", "it is important to note": "note",
    "in conclusion": "last bit", "in summary": "to wrap it",
    "plays a crucial role": "matters", "a wide range of": "a bunch of",
    "best practices": "what works", "deep dive": "close look",
}
FILLER = re.compile(
    r"\b(as an ai language model|as an ai|it('s| is) worth noting that|"
    r"it goes without saying that|in today('s|’s) fast-paced world)\b[,.]?\s*", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def score_risk(text: str) -> dict:
    words = re.findall(r"[A-Za-z']+", text.lower())
    n = max(len(words), 1)
    ai_hits = sum(1 for w in words if w in AI_WORDS)
    sents = [s for s in SENT_SPLIT.split(text) if s.strip()]
    lens = [len(s.split()) for s in sents] or [0]
    avg = sum(lens) / max(len(lens), 1)
    var = sum((x - avg) ** 2 for x in lens) / max(len(lens), 1)
    uniform_pen = 25 if sents and var < 8 else 0  # flat rhythm = robot
    nocontract_pen = 10 if not re.search(r"\b(don't|can't|won't|it's|i'm|you're|that's|there's)\b", text, re.I) else 0
    vocab_pen = min(50, ai_hits * 9)
    filler_pen = 15 if FILLER.search(text) else 0
    long_pen = 10 if avg > 28 else 0
    risk = min(100, vocab_pen + uniform_pen + nocontract_pen + filler_pen + long_pen)
    band = "LOW" if risk <= 20 else "MODERATE" if risk <= 40 else "HIGH" if risk <= 70 else "VERY HIGH"
    return {"risk": risk, "band": band, "ai_words": ai_hits,
            "sentences": len(sents), "avg_len": round(avg, 1), "variance": round(var, 1)}


class Humanizer:
    def __init__(self, seed: int = 4080):
        self.rng = random.Random(seed)

    def humanize(self, text: str, aggression: int = 2) -> str:
        t = FILLER.sub("", text)
        t = self._swap_vocab(t)
        t = self._contractions(t)
        if aggression >= 1:
            t = self._rhythm(t)
        if aggression >= 2:
            t = self._voice(t)
        if aggression >= 3:
            t = self._grit(t)
        return t.strip()

    def _swap_vocab(self, t: str) -> str:
        for k, v in AI_WORDS.items():
            t = re.sub(rf"\b{re.escape(k)}\b", v, t, flags=re.I)
        return t

    def _contractions(self, t: str) -> str:
        pairs = [("do not", "don't"), ("does not", "doesn't"), ("cannot", "can't"),
                 ("it is", "it's"), ("that is", "that's"), ("there is", "there's"),
                 ("you are", "you're"), ("I am", "I'm"), ("will not", "won't"),
                 ("have not", "haven't"), ("would not", "wouldn't")]
        for a, b in pairs:
            if self.rng.random() < 0.8:
                t = re.sub(rf"\b{a}\b", b, t, flags=re.I)
        return t

    def _rhythm(self, t: str) -> str:
        parts = [s.strip() for s in SENT_SPLIT.split(t) if s.strip()]
        out = []
        for s in parts:
            out.append(s)
            if len(s.split()) > 22 and self.rng.random() < 0.6:
                out.append(self.rng.choice(["No fluff.", "That's the core of it.",
                                            "Rest is execution.", "Moo. Moving on."]))
        # merge a couple of short neighbors for burstiness
        merged, i = [], 0
        while i < len(out):
            if (i + 1 < len(out) and len(out[i].split()) < 8
                    and len(out[i + 1].split()) < 8 and self.rng.random() < 0.5):
                merged.append(out[i] + " " + out[i + 1][0].lower() + out[i + 1][1:])
                i += 2
            else:
                merged.append(out[i]); i += 1
        return " ".join(merged)

    def _voice(self, t: str) -> str:
        openers = ["Look — ", "Here's the thing: ", "Flat truth: ", ""]
        t = self.rng.choice(openers) + t
        t = re.sub(r"\bIn order to\b", "To", t, flags=re.I)
        return t

    def _grit(self, t: str) -> str:
        tics = [" honestly", ", flat out", " — no padding"]
        parts = [s for s in SENT_SPLIT.split(t) if s.strip()]
        for i in self.rng.sample(range(len(parts)), min(2, len(parts))):
            p = parts[i].rstrip(".!?")
            parts[i] = p + self.rng.choice(tics) + "."
        return " ".join(parts)
