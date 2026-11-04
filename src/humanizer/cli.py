"""humanize INPUT -o OUT [--writer mlx:<model>|claude:<model>] [--detector models/detector-v1]"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from humanizer import ROOT
from humanizer.pipeline.run import TooShort, humanize

DEFAULT_WRITER = f"sec:{ROOT / 'models' / 'olmo2-13b-base-4bit'}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="humanize")
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--writer", default=DEFAULT_WRITER)
    ap.add_argument("--detector", type=Path, default=ROOT / "models" / "detector-v1")
    a = ap.parse_args(argv)

    draft = a.input.read_text()
    det = None
    if a.detector.exists():
        from humanizer.detect.score import Detector
        det = Detector.load(a.detector)
    try:
        res = humanize(draft, writer=a.writer, detector=det)
    except TooShort as e:
        print(f"humanize: {e}", file=sys.stderr)
        return 2
    a.out.write_text(res.text + "\n")
    report = {"writer": a.writer, "detector": res.detector, "retries": res.retries, "checks": res.checks,
              "plan": asdict(res.plan), "words_in": len(draft.split()), "words_out": len(res.text.split())}
    if det is not None:
        report["detector_input"] = det.score(draft)
    a.out.with_suffix(a.out.suffix + ".report.json").write_text(json.dumps(report, indent=1))
    print(f"wrote {a.out} ({report['words_out']} words); claim check pass={res.checks['pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
