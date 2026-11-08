from humanizer.checks.loops import cut_loop, is_loop, last_sentence, repeat_share, trailing_loop

PROSE = ("The cache layer stores results for later. We evict the oldest entries first, which works well enough. "
         "Monitoring tells us when latency grows past the budget we agreed on. Nobody reads that dashboard on weekends. "
         "A pager fixes that problem, though it creates another one for whoever carries it around all month. ")
LOOP = "and the war in the Mandela " * 40


def test_prose_is_not_a_loop():
    assert repeat_share(PROSE) < 0.05 and not is_loop(PROSE) and not trailing_loop(PROSE * 1)
    assert cut_loop(PROSE) == PROSE


def test_loop_is_found_and_cut_at_the_last_sentence():
    t = PROSE + "It was hard to explain " + LOOP
    assert is_loop(t) and trailing_loop(t)
    cut = cut_loop(t)
    assert cut.endswith("carries it around all month.") and "Mandela" not in cut


def test_long_period_loop():
    sent = ("Each of the lessons we learned that summer came back to the same stubborn question about what we owed the "
            "people who trusted us with their time and their money and their very patient attention. ")
    t = sent * 8
    assert is_loop(t) and trailing_loop(t)


def test_last_sentence():
    assert last_sentence('He said "stop." Then we went and') == 'He said "stop."'
    assert last_sentence("no end here") == ""
