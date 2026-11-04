from humanizer.detect.score import Detector, normalize, windows


def test_normalize_strips_markdown():
    md = "# Title\n\nSome **bold** text with `code`.\n\n- item one\n- item two\n\n```py\nx = 1\n```"
    out = normalize(md)
    assert "#" not in out and "**" not in out and "- item" not in out and "x = 1" not in out
    assert "Title" in out and "bold" in out and "item one" in out


def test_windows_cover_every_token():
    ids = list(range(1300))
    ws = windows(ids, 512, 256)
    assert ws[0][0] == 0 and ws[-1][-1] == 1299
    assert all(len(w) == 512 for w in ws)


def test_score_long_text_uses_windows(monkeypatch):
    calls = []

    class Tok:
        cls_token_id, sep_token_id = 0, 1

        def __call__(self, text, add_special_tokens=False):
            return {"input_ids": list(range(2000))}

    det = Detector(model=None, tok=Tok(), device="cpu")
    monkeypatch.setattr(det, "window_probs", lambda t: calls.append(t) or [0.2, 0.4])
    assert abs(det.score("x") - 0.3) < 1e-9
    # the real window count for 2000 tokens at 510/256 is at least 7
    assert len(windows(list(range(2000)), 510, 256)) >= 7
