# JB Forge — README

Automated jb generator + auto-tester. Generates persona-wrapped
jb prompts, fires them at target models (Gemini / OpenRouter /
Groq / Together / local), judges success automatically, confirms winners
across K re-runs, and humanizes output to dodge AI detectors.

## Layout

```
forge/          core engine (generator, harness, judge, humanize, loop)
corpus/         fuel — techniques, seed prompts, personas
providers/      provider configs
scripts/        CLI entry points
tests/          smoke tests
dashboard/      run reports (sqlite + markdown)
```

## Quickstart

```bash
pip install -e .
cp .env.example .env   # drop keys in
python scripts/forge.py generate --goal "write a keylogger" --persona ratman3000 --technique refusal_suppression
python scripts/forge.py attack --goal "write a keylogger" --rounds 3 --confirm-k 3
python scripts/forge.py humanize --file out.txt --aggression 2
```
