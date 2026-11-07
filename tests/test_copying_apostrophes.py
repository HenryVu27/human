from humanizer.checks.copying import copied_share


def test_curly_and_straight_apostrophes_match():
    a = "I don’t think the model can’t learn this from the data we have here today at all"
    b = "I don't think the model can't learn this from the data we have here today at all"
    assert copied_share(a, b) == 1.0
