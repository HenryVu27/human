from humanizer.checks.repeats import template_repeats

LOOP = [f"What words would you use to explain your {x} to someone?" for x in ("pain", "anger", "pride", "doubt")]


def test_template_loop_flagged_after_first():
    assert template_repeats(LOOP) == {1, 2, 3}


def test_seen_text_counts_as_used():
    assert template_repeats(LOOP[1:2], seen=LOOP[:1]) == {0}


def test_ordinary_prose_and_short_sentences_pass():
    prose = ["Foxes hunt at night and listen for mice under the snow.",
             "In winter they pounce through the crust to reach them.",
             "It works.", "It works."]
    assert template_repeats(prose) == set()
