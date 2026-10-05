"""forge/harness.py — stdlib-only HTTP (urllib), threaded firing."""
from __future__ import annotations
import json
import os
import threading
import time
import urllib.request


class Target:
    def __init__(self, name, kind, base_url, key, model, rpm=20):
        self.name, self.kind = name, kind
        self.base_url = base_url.rstrip("/")
        self.key, self.model = key, model
        self._gap = 60.0 / max(rpm, 1)
        self._last = 0.0
        self._lock = threading.Lock()

    def fire(self, messages: list[dict]) -> str:
        with self._lock:
            wait = self._gap - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            try:
                out = fire_gemini(self.base_url, self.key, self.model, messages) \
                    if self.kind == "gemini" else fire_compat(self.base_url, self.key, self.model, messages)
            except Exception as e:
                out = f"[FIRE-ERROR: {type(e).__name__}: {e}]"
            self._last = time.monotonic()
            return out


def _post(url: str, headers: dict, payload: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fire_compat(base_url, key, model, messages, timeout=60) -> str:
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization"] = f"Bearer {key}"
    d = _post(f"{base_url}/chat/completions", h,
              {"model": model, "messages": messages}, timeout)
    return d["choices"][0]["message"]["content"]


def fire_gemini(base_url, key, model, messages, timeout=60) -> str:
    contents = [{"role": "user" if m["role"] == "user" else "model",
                 "parts": [{"text": m["content"]}]} for m in messages]
    d = _post(f"{base_url}/models/{model}:generateContent?key={key}",
              {"Content-Type": "application/json"}, {"contents": contents}, timeout)
    return d["candidates"][0]["content"]["parts"][0]["text"]


def targets_from_env() -> list[Target]:
    t = []
    if os.getenv("GEMINI_API_KEY"):
        t.append(Target("gemini-flash", "gemini",
                        "https://generativelanguage.googleapis.com/v1beta",
                        os.environ["GEMINI_API_KEY"], "gemini-2.0-flash", 15))
    if os.getenv("OPENROUTER_API_KEY"):
        t.append(Target("openrouter-free", "openrouter",
                        "https://openrouter.ai/api/v1",
                        os.environ["OPENROUTER_API_KEY"],
                        "meta-llama/llama-3.3-70b-instruct:free", 20))
    if os.getenv("GROQ_API_KEY"):
        t.append(Target("groq-fast", "openai_compat",
                        "https://api.groq.com/openai/v1",
                        os.environ["GROQ_API_KEY"], "llama-3.3-70b-versatile", 30))
    if os.getenv("TOGETHER_API_KEY"):
        t.append(Target("together-free", "openai_compat",
                        "https://api.together.xyz/v1",
                        os.environ["TOGETHER_API_KEY"],
                        "meta-llama/Llama-3.3-70B-Instruct-Turbo", 20))
    t.append(Target("local-ollama", "openai_compat",
                    "http://localhost:11434/v1", "", "dolphin-llama3", 600))
    return t


# compat alias so old imports keep working
fire_openai_compat = fire_compat
