from humanizer.pipeline import prune as pr

TEXT = "First point here. It repeats itself. Second point.\n\n## Part two\n\nOnly sentence of part two."


def test_split_and_number_sentences():
    paras = pr.split_sentences(TEXT)
    assert paras[0] == ["First point here.", "It repeats itself.", "Second point."]
    listing, flat = pr.numbered(paras)
    assert "[2] It repeats itself." in listing and flat[3] == "## Part two"


def test_apply_deletions_keeps_words_and_drops_empty_sections():
    paras = pr.split_sentences(TEXT)
    assert pr.apply_deletions(paras, {2}) == "First point here. Second point.\n\n## Part two\n\nOnly sentence of part two."
    assert pr.apply_deletions(paras, {5}) == "First point here. It repeats itself. Second point."


def test_prune_caps_the_cut(monkeypatch):
    monkeypatch.setattr(pr, "claude", lambda prompt, model: '{"delete": [1, 2, 3, 5]}')
    out = pr.prune("draft", TEXT)
    kept = len(out.split())
    assert kept >= 0.6 * len(TEXT.replace("## Part two", "").split()) - 1
    assert all(s in TEXT for s in out.replace("\n\n", " ").split(". ")[0:1])
