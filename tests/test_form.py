from humanizer.checks.form import check_form, new_code_lines, new_framing, new_headers, non_english_runs, restart_opening

SRC = "I ran the race in May. My time was slow because of the heat. I learned to drink more water."


def test_clean_rewrite_passes():
    out = "In May I ran the race. The heat made my time slow, and I learned to drink more water."
    r = check_form(out, SRC)
    assert r["ok"], r


def test_french_run_is_flagged():
    out = ("I ran the race in May. Les coureurs sont arrivés dans la ville pour la course et nous avons couru avec eux. "
           "Mais il est très difficile de courir dans la chaleur et pour moi la fin était dure.")
    assert len(non_english_runs(out)) == 2
    assert not check_form(out, SRC)["ok"]


def test_english_with_one_borrowed_word_passes():
    assert non_english_runs("I had a croissant and a coffee at the cafe before the race started that day.") == []


def test_new_code_is_flagged_but_source_code_is_not():
    src = "Set the pin with pinMode(13, OUTPUT); and then wait."
    out = "Set the pin:\npinMode(13, OUTPUT);\nvoid loop() {\n  digitalWrite(13, HIGH);\n  delay(500);\n}\n"
    found = new_code_lines(out, src)
    assert "pinMode(13, OUTPUT);" not in found
    assert any("digitalWrite" in x for x in found) and any("void loop" in x for x in found)
    assert not check_form(out, src)["ok"]


def test_series_opener_and_signoff_are_flagged_unless_in_source():
    out = "This is the second of three articles on running. Thanks for reading!"
    assert len(new_framing(out, SRC)) == 2
    assert new_framing(out, "This is the second of three articles on running. " + SRC) == ["Thanks for reading"]
    assert not check_form("In my last post I wrote about May. " + SRC, SRC)["ok"]


def test_invented_header_is_flagged():
    out = "### Gaussian and Bounded Draft\nA variable is subgaussian if its tail is light."
    assert new_headers(out, "A variable is subgaussian if its tail is light.") == ["### Gaussian and Bounded Draft"]
    assert new_headers(out, "Gaussian and Bounded Draft\nA variable is subgaussian if its tail is light.") == []


def test_restart_opening_only_counts_in_later_sections():
    sec = "In today's post, I'm going to talk about the seventh book. It is long."
    assert restart_opening(sec, "The seventh book is long.") == ["In today's post"]
    assert check_form(sec, "The seventh book is long.")["ok"]
    assert not check_form(sec, "The seventh book is long.", later_section=True)["ok"]
    assert "Last time, I" in restart_opening("Last time, I wrote about ePub files. Now the tips.", "Tips for ePub files.")
