"""Local stand-in for Pangram: P(AI) from a fine-tuned encoder, averaged over windows."""

from __future__ import annotations

import re
from pathlib import Path

WINDOW, STRIDE = 512, 256

_MD = [
    (re.compile(r"```.*?```", re.S), " "),          # code blocks
    (re.compile(r"^\s{0,3}#{1,6}\s*", re.M), ""),    # heading markers
    (re.compile(r"^\s*([-*+]|\d+[.)])\s+", re.M), ""),  # list markers
    (re.compile(r"(\*\*|__|\*|_|`)"), ""),          # emphasis and inline code
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), r"\1"),  # links
    (re.compile(r"[ \t]+"), " "),
    (re.compile(r"\n{3,}"), "\n\n"),
]


def normalize(text: str) -> str:
    """Strip markdown so the detector cannot learn formatting as a shortcut."""
    for pat, rep in _MD:
        text = pat.sub(rep, text)
    return text.strip()


def windows(ids: list[int], size: int = WINDOW, stride: int = STRIDE) -> list[list[int]]:
    if len(ids) <= size:
        return [ids]
    starts = list(range(0, len(ids) - size + 1, stride))
    if starts[-1] + size < len(ids):
        starts.append(len(ids) - size)
    return [ids[s:s + size] for s in starts]


class Detector:
    def __init__(self, model, tok, device: str):
        self.model, self.tok, self.device = model, tok, device

    @classmethod
    def load(cls, path: Path) -> "Detector":
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        model = AutoModelForSequenceClassification.from_pretrained(path).to(device).eval()
        return cls(model, AutoTokenizer.from_pretrained(path), device)

    def window_probs(self, text: str) -> list[float]:
        import torch

        ids = self.tok(normalize(text), add_special_tokens=False)["input_ids"]
        out = []
        for w in windows(ids, WINDOW - 2):
            x = torch.tensor([[self.tok.cls_token_id, *w, self.tok.sep_token_id]], device=self.device)
            with torch.no_grad():
                logits = self.model(input_ids=x).logits
            out.append(torch.softmax(logits, -1)[0, 1].item())
        return out

    def score(self, text: str) -> float:
        probs = self.window_probs(text)
        return sum(probs) / len(probs)
