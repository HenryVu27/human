import httpx
import pytest

from humanizer.eval import pangram
from humanizer.eval.pangram import Pangram, is_human


@pytest.fixture(autouse=True)
def tmp_log(tmp_path, monkeypatch):
    monkeypatch.setattr(pangram, "LOG", tmp_path / "log.jsonl")


def client(handler):
    return httpx.Client(base_url=pangram.BASE, transport=httpx.MockTransport(handler))


def test_is_human_mixed_is_false():
    assert not is_human({"prediction_short": "Mixed"})
    assert not is_human({"prediction_short": "AI"})
    assert is_human({"prediction_short": "Human"})


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("PANGRAM_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        Pangram()


def test_score_polls_until_success():
    polls = iter([{"stage": "STAGE_PREPROCESSING"},
                  {"stage": "STAGE_SUCCESS", "prediction_short": "Human", "version": "4.1", "windows": []}])

    def handler(req):
        assert req.headers["x-api-key"] == "k"
        if req.method == "POST":
            return httpx.Response(200, json={"task_id": "t1"})
        return httpx.Response(200, json=next(polls))

    res = Pangram("k", client=client(handler), poll=0).score("text", "pangram-4")
    assert is_human(res) and pangram.LOG.read_text().count("4.1") == 1


def test_bulk_returns_results_in_input_order():
    def handler(req):
        if req.method == "POST":
            return httpx.Response(202, json={"bulk_id": "b1"})
        if req.url.path.endswith("/results"):
            return httpx.Response(200, json={"total_items": 2, "items": [
                {"index": 1, "id": "y", "result": {"prediction_short": "AI", "windows": []}},
                {"index": 0, "id": "x", "result": {"prediction_short": "Human", "windows": []}}]})
        return httpx.Response(200, json={"status": "succeeded"})

    out = Pangram("k", client=client(handler), poll=0).bulk(["a", "b"], "pangram-4", ids=["x", "y"])
    assert [r["prediction_short"] for r in out] == ["Human", "AI"]
