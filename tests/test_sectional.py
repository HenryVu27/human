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
    words = ["x", " the", " Wang", " China", " 1999", ".", " Chi", "\n"]

    def decode(self, ids):
        return "".join(self.words[i] for i in ids)


def test_guard_blocks_new_names_and_numbers_mid_sentence_only():
    g = Guard(Tok(), allowed_specifics("Researchers in China"))
    logits = mx.zeros((1, 8))
    mid = g(mx.array([1]), logits)  # after " the"
    blocked = {i for i in range(8) if mid[0, i].item() == float("-inf")}
    assert blocked == {2, 4}  # " Wang" and " 1999"; " China" and its prefix " Chi" are allowed
    start = g(mx.array([5]), logits)  # after "."
    assert {i for i in range(8) if start[0, i].item() == float("-inf")} == {4}
