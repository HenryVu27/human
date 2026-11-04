"""editor -> writer -> checks, with up to two retries on a failed claim check."""

from __future__ import annotations

from dataclasses import dataclass, field

from humanizer.checks.claims import claim_check
from humanizer.pipeline.editor import Plan, edit_plan
from humanizer.pipeline.prune import prune
from humanizer.pipeline.writer import write

MIN_WORDS = 50
MAX_RETRIES = 2


class TooShort(ValueError):
    pass


@dataclass
class Result:
    text: str
    plan: Plan
    checks: dict
    detector: float | None = None
    retries: int = 0
    attempts: list[dict] = field(default_factory=list)


def humanize(draft: str, *, writer: str, detector=None, editor_model: str = "opus") -> Result:
    if len(draft.split()) < MIN_WORDS:
        raise TooShort(f"draft has {len(draft.split())} words; need at least {MIN_WORDS}")
    plan = edit_plan(draft, model=editor_model)
    best = None
    for attempt in range(MAX_RETRIES + 1):
        text = write(plan, writer, seed=attempt, draft=draft)
        if not writer.startswith("claude:"):
            text = prune(draft, text)  # base-model writers ramble; cut, never reword
        checks = claim_check(draft, text)
        rank = (checks["pass"], -len(checks["unsupported_specifics"]),
                checks["claims_entailed"] / max(1, checks["claims_total"]))
        cand = {"text": text, "checks": checks, "rank": rank, "attempt": attempt}
        if best is None or rank > best["rank"]:
            best = cand
        if checks["pass"]:
            break
    res = Result(best["text"], plan, best["checks"], retries=attempt)
    if detector is not None:
        res.detector = detector.score(res.text)
    return res
