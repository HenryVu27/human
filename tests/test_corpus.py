from humanizer.data.corpus import keep_doc

LONG = " ".join(["word"] * 600)


def row(**kw):
    base = {"text": LONG, "dump": "CC-MAIN-2019-30", "int_score": 3, "language": "en"}
    return base | kw


def test_keep_doc_rejects_2023_dump():
    assert not keep_doc(row(dump="CC-MAIN-2023-06"))


def test_keep_doc_rejects_short():
    assert not keep_doc(row(text="too short " * 50))


def test_keep_doc_rejects_low_edu_score():
    assert not keep_doc(row(int_score=2))


def test_keep_doc_rejects_boilerplate_opening():
    assert not keep_doc(row(text="We use cookies to improve your experience. " + LONG))


def test_keep_doc_accepts_2019_long_edu():
    assert keep_doc(row())
