from humanizer.checks import claims, quality

DRAFT = "In 2019, Acme Corp shipped 1,200 units. The CEO said \"growth is hard\" at a meeting."


def test_unsupported_specifics_flags_new_number():
    out = "Acme Corp shipped 1,200 units in 2019, up 35% from before."
    assert claims.unsupported_specifics(DRAFT, out) == {"35%"}


def test_unsupported_specifics_flags_new_name_and_quote():
    out = "Jane Doe of Acme Corp said \"we will win\"."
    bad = claims.unsupported_specifics(DRAFT, out)
    assert "Jane Doe" in bad and "we will win" in bad


def test_specifics_ignores_code_blocks():
    text = "Use the `MaxRetries` option.\n\n```python\nClient(TimeoutSeconds=30)\n```\nDone."
    assert claims.specifics(text) == set()


def test_same_text_has_no_unsupported():
    assert claims.unsupported_specifics(DRAFT, DRAFT) == set()


def test_number_formats_match():
    assert claims.unsupported_specifics("about 1000 people", "about 1,000 people") == set()


def test_claim_check_combines(monkeypatch):
    monkeypatch.setattr(claims, "claude",
                        lambda p, **k: '[{"claim":"a","supported":true},{"claim":"b","supported":true}]')
    r = claims.claim_check(DRAFT, "Acme Corp shipped units.")
    assert r["pass"] and r["claims_total"] == 2 and r["claims_entailed"] == 2


def test_quality_pair_scores_both_orders(monkeypatch):
    answers = iter(["B", "A"])  # output is B first, then A after the swap: wins both
    monkeypatch.setattr(quality, "claude", lambda p, **k: next(answers))
    assert quality.quality_pair("draft", "output") == 1.0


def test_title_case_headings_are_not_names():
    from humanizer.checks.claims import unsupported_specifics
    out = "# One Workflow, Two Very Different Countries\n\nThe maps used Landsat data.\n\n## Why It Scales\n\nIt scales."
    assert unsupported_specifics("Landsat data mapped fields.", out) == set()
    assert unsupported_specifics("Landsat data.", "We met Jane Doe there.") == {"Jane Doe"}


def test_names_do_not_span_lines():
    from humanizer.checks.claims import specifics
    found = specifics("We went to Dunkeld\n## Old Stones\nThe fountain stood there.")
    assert not any(" " in s and "Dunkeld" in s for s in found)
