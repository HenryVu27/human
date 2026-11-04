from humanizer.data import lora
from humanizer.pipeline.editor import Plan, Section


def test_prompt_format():
    plan = Plan("Wells", [Section("Digging", [{"note": "dug by hand, 1890", "quote": ""}], 80),
                          Section(None, [{"note": "dry by 1920", "quote": ""}], 40)])
    p = lora.lora_prompt(plan)
    assert p.startswith("Notes:\nTitle: Wells\n")
    assert "Part: Digging (about 80 words)\n- dug by hand, 1890\n" in p
    assert "Part:  (about 40 words)" in p
    assert p.endswith("\nArticle:\n")


def test_fits_cuts_at_paragraph():
    text = "\n".join(["word " * 500] * 4)
    out = lora._fits(text)
    assert len(out.split()) == 1000
    assert out.count("\n") == 1


def test_train_ids_avoid_eval_topics():
    assert not any(600 <= i < 850 for i in lora.TRAIN_IDS)


def test_selection_groups_and_scales():
    from humanizer.pipeline.lora_writer import apply_selection, numbered_notes
    plan = Plan("T", [Section("A", [{"note": "a1"}, {"note": "a2"}], 100),
                      Section("B", [{"note": "b1"}, {"note": "b2"}, {"note": "b3"}, {"note": "b4"}], 200)])
    listing, flat = numbered_notes(plan)
    assert "[3] b1" in listing
    out = apply_selection(plan, flat, [3, 4, 1, 1, 99])
    assert [s.heading for s in out.sections] == ["B", "A"]
    assert [p["note"] for p in out.sections[0].points] == ["b1", "b2"]
    assert [s.target_words for s in out.sections] == [100, 50]
    assert all(isinstance(s.target_words, int) for s in out.sections)
