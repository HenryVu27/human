from humanizer import cli
from humanizer.pipeline import run
from humanizer.pipeline.editor import Plan, Section, parse_plan
from humanizer.pipeline.writer import truncate_at_document_break

PLAN = Plan("T", [Section(None, [{"note": "n", "quote": "q"}], 100)])


def test_truncate_at_document_break():
    text = "Body paragraph one.\n\nBody two.\n=== NOTES ===\nTitle: next doc"
    assert truncate_at_document_break(text) == "Body paragraph one.\n\nBody two."
    assert truncate_at_document_break("Body.\n# Another Title\nmore") == "Body."
    assert truncate_at_document_break("Body.<|endoftext|>junk") == "Body."


def test_parse_plan_handles_fenced_json():
    p = parse_plan('```json\n{"title":"A","sections":[{"heading":null,"points":[],"target_words":90}]}\n```')
    assert p.title == "A" and p.target_words == 90


def test_cli_rejects_short_input(tmp_path, capsys):
    f = tmp_path / "d.md"
    f.write_text("too short to humanize")
    assert cli.main([str(f), "-o", str(tmp_path / "o.md"), "--detector", str(tmp_path / "none")]) == 2
    assert "at least 50" in capsys.readouterr().err


def test_humanize_retries_then_keeps_best(monkeypatch):
    monkeypatch.setattr(run, "edit_plan", lambda d, model: PLAN)
    texts = iter(["bad 99", "better", "best"])
    monkeypatch.setattr(run, "write", lambda plan, writer, seed, draft: next(texts))
    verdicts = iter([
        {"pass": False, "unsupported_specifics": ["99"], "claims_total": 2, "claims_entailed": 1},
        {"pass": True, "unsupported_specifics": [], "claims_total": 2, "claims_entailed": 2},
    ])
    monkeypatch.setattr(run, "claim_check", lambda d, t: next(verdicts))
    res = run.humanize("word " * 60, writer="claude:x")
    assert res.text == "better" and res.retries == 1
