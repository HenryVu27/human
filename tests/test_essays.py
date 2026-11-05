from humanizer.data.essays import _page_date, eligible, split, text_of


def test_text_of_drops_quotes_code_and_keeps_paragraphs():
    page = ("<p>First &amp; mine.</p><blockquote><p>someone else said this here</p></blockquote>"
            "<pre>code()</pre><p>Second<br><br>third</p><ul><li>item</li></ul>")
    text, quoted = text_of(page)
    assert text == "First & mine.\n\nSecond\n\nthird\n\n- item"
    assert round(quoted, 2) == round(5 / 12, 2)  # 5 quoted words, 7 kept


def test_page_date_reads_meta_and_month_year():
    assert _page_date('<meta property="article:published_time" content="2019-03-13T00:00:00">') == "2019-03-13"
    assert _page_date("<b>How to Work Hard</b><br>June 2021<br>It might") == "2021-06-01"
    assert _page_date("<p>March 13, 2019</p>") == "2019-03-01"


def test_split_is_fixed_and_filtered():
    posts = [{"url": f"u{i}", "title": "Links for May" if i == 0 else "t", "words": 400 + 50 * i,
              "quoted": 0.0, "date": "2020-01-01"} for i in range(30)]
    got = split(posts)
    assert got == split(list(reversed(posts)))
    assert all(eligible(p) for p in got) and "u0" not in {p["url"] for p in got}
    bench = [p for p in got if p["split"] == "bench"]
    assert len(bench) == 2 and all(500 <= p["words"] <= 1500 for p in bench)
