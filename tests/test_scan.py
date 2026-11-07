from humanizer.eval.scan import PLACEHOLDER, canary_check, credits, parse_transcript, scoring_form


def test_scoring_form_removes_code_math_and_markdown():
    text = (
        "## Why bandits\n\nThe **regret** grows like $\\sqrt{T}$, and it costs $5 to run.\n\n"
        "```python\nprint('hi')\n```\n\n$$R_T = \\sum_t r_t$$\n\n- one point\n- [a link](http://x)\n"
    )
    out = scoring_form(text)
    assert "print" not in out and "```" not in out
    assert PLACEHOLDER in out and "\\sum" not in out and "sqrt" not in out
    assert "$5" in out                      # currency survives
    assert "##" not in out and "**" not in out and "- " not in out
    assert "regret" in out and "a link" in out and "http" not in out


def test_credits_per_started_hundred():
    assert credits("w " * 100) == 1
    assert credits("w " * 101) == 2


def test_parse_transcript(tmp_path):
    p = tmp_path / "t.txt"
    p.write_text("1918734b.docx|5 Credits,484 Words|Mixed\nnoise\n2e38c03d.docx|8 Credits,1,204 Words|Human\n")
    rows = parse_transcript(p)
    assert rows == [
        {"name": "1918734b", "credits": 5, "pangram_words": 484, "label": "Mixed"},
        {"name": "2e38c03d", "credits": 8, "pangram_words": 1204, "label": "Human"},
    ]


def test_canary_check_flags_any_change():
    rows = [{"key": "CAN_a", "cell": "CAN", "label": "Human", "ai_share": 0.0},
            {"key": "CAN_b", "cell": "CAN", "label": "Mixed", "ai_share": 0.12}]
    ref = {"CAN_a": {"label": "Human", "ai_share": 0.0}, "CAN_b": {"label": "Human", "ai_share": 0.09}}
    res = canary_check(rows, ref)
    assert not res["identical"] and [c["key"] for c in res["changed"]] == ["CAN_b"]
