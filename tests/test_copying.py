from humanizer.checks.copying import copied_share


def test_copied_share_counts_words_in_shared_runs():
    src = "one two three four five six seven eight nine ten"
    text = "zero one two three four five six seven eight end"
    assert copied_share(text, src) == 0.8
    assert copied_share(text, src, beyond="one two three four five six seven eight") == 0.0
    assert copied_share("nothing in common here at all today", src) == 0.0
