"""forge/__init__.py — jb-forge core."""
from .generator import Generator
from .harness import Target, fire_openai_compat, fire_gemini
from .judge import Judge
from .humanize import Humanizer, score_risk
from .loop import ForgeLoop

from .longform import LongformBuilder

__all__ = ["Generator", "Target", "fire_openai_compat", "fire_gemini",
           "Judge", "Humanizer", "score_risk", "ForgeLoop", "LongformBuilder"]
