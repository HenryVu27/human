from humanizer.data.wiki import _paras, permalink

HTML = ('<div><p>Gaucher&#39;s disease is a <a href="x">genetic disorder</a> in which glucocerebroside '
        'accumulates in cells and certain organs of the body.<sup>[1]</sup><sup>[citation needed]</sup></p>'
        '<p>Too short.</p><table><tr><td>cell</td></tr></table></div>')


def test_paras_strips_tags_entities_and_markers():
    assert _paras(HTML) == ["Gaucher's disease is a genetic disorder in which glucocerebroside accumulates "
                            "in cells and certain organs of the body."]


def test_permalink_points_at_the_revision():
    assert permalink(1055445132) == "https://en.wikipedia.org/w/index.php?oldid=1055445132"
