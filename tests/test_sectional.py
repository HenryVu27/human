import mlx.core as mx

from humanizer.pipeline.editor import Plan, Section
from humanizer.pipeline.sectional import Guard, allowed_specifics, sectional_prompt, split_by_starts

TEXT = "Foxes hunt at night. They listen for mice.\n\nIn winter they pounce through snow. It works well."


def test_split_by_starts_cuts_at_each_start_in_order():
    parts = split_by_starts(TEXT, ["Foxes hunt at night", "In winter they pounce"])
    assert parts == ["Foxes hunt at night. They listen for mice.", "In winter they pounce through snow. It works well."]
    assert split_by_starts(TEXT, ["In winter they pounce", "Foxes hunt at night"]) is None
    assert split_by_starts(TEXT, ["Foxes hunt", "Wolves howl"]) is None


def test_allowed_specifics_keeps_names_and_numbers():
    a = allowed_specifics("In 2018 the Landsat team in China mapped 94% of fields.")
    assert {"2018", "Landsat", "China", "94", "In", "I"} <= a
    assert "mapped" not in a


def test_sectional_prompt_ends_on_next_section_notes():
    plan = Plan("T", [Section(None, [{"note": "a"}], 50), Section("Two", [{"note": "b"}], 60)])
    p = sectional_prompt(plan, ["First section text."], [])
    assert p.rstrip().endswith("<<notes: b | about 60 words>>\nTwo")
    assert "First section text." in p and "<<notes: a | about 50 words>>" in p


class Tok:
    words = ["x", " the", " Wang", " China", " 30", ".", " Ma", "pping", "rine", "\n", " Researchers", ' "']

    def decode(self, ids):
        return "".join(self.words[i] for i in ids)


def _blocked(g, history):
    out = g(mx.array(history), mx.zeros((1, len(Tok.words))))
    return {Tok.words[i] for i in range(len(Tok.words)) if out[0, i].item() == float("-inf")}


def test_guard_blocks_new_names_and_numbers_mid_sentence():
    g = Guard(Tok(), allowed_specifics("Mapping cropland in China"), {"Researchers"}, allow_quotes=False)
    b = _blocked(g, [0, 1])  # "... the"
    assert {" Wang", " 30", " Researchers", ' "'} <= b
    assert " China" not in b and " Ma" not in b  # " Ma" is a prefix of Mapping


def test_guard_forces_a_started_name_to_finish_as_a_draft_word():
    g = Guard(Tok(), allowed_specifics("Mapping cropland in China"), set())
    b = _blocked(g, [0, 1, 6])  # "... the Ma"
    assert "pping" not in b and "rine" in b  # Mapping yes, Marine no
    assert " the" in b and "." in b  # cannot stop at "Ma"
    assert "rine" in _blocked(g, [0, 1, 6, 7]) and " the" not in _blocked(g, [0, 1, 6, 7])  # after "Mapping"


def test_guard_allows_common_words_at_sentence_start():
    g = Guard(Tok(), set(), {"Researchers"})
    assert " Researchers" not in _blocked(g, [0, 5])  # after "."
    assert " Researchers" in _blocked(g, [0, 1])      # mid-sentence
