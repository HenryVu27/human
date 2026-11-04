from humanizer.data.mirror import mirror_prompt, ngram_overlap, parse_topic, split_of

SOURCE = "The quick brown fox jumps over the lazy dog near the old river bank today."


def test_mirror_prompt_requests_length_and_topic_only():
    p = mirror_prompt({"title": "Foxes", "topic": "how foxes hunt", "genre": "explainer"}, 640)
    assert "how foxes hunt" in p and "640" in p
    assert "quick brown fox" not in p


def test_parse_topic_tolerates_fenced_json():
    t = parse_topic('```json\n{"title": "A", "topic": "b", "genre": "c"}\n```')
    assert t == {"title": "A", "topic": "b", "genre": "c"}


def test_ngram_overlap_detects_copied_span():
    assert ngram_overlap(SOURCE, "intro " + SOURCE, n=12)
    assert not ngram_overlap(SOURCE, "Foxes are clever animals that hunt at night.", n=12)


def test_split_of_assigns_frozen_ranges():
    assert split_of(0) == "pairs" and split_of(599) == "pairs"
    assert split_of(600) == "dev" and split_of(700) == "h1" and split_of(800) == "h2"
    assert split_of(850) == "spare"
