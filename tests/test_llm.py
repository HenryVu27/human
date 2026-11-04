import json
import subprocess

import pytest

from humanizer import llm


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_claude_cache_hit_skips_subprocess(monkeypatch):
    llm._cache_put(llm._key("claude", "haiku", None, "hi"), "cached")

    def boom(*a, **k):
        raise AssertionError("subprocess should not run on a cache hit")

    monkeypatch.setattr(subprocess, "run", boom)
    assert llm.claude("hi", model="haiku") == "cached"


def test_claude_parses_result_field(monkeypatch):
    class Done:
        returncode = 0
        stdout = json.dumps({"result": "hi", "is_error": False})
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Done())
    assert llm.claude("prompt", model="haiku") == "hi"
    # second call is served from cache
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: 1 / 0)
    assert llm.claude("prompt", model="haiku") == "hi"


def test_claude_error_raises(monkeypatch):
    class Failed:
        returncode = 1
        stdout = ""
        stderr = "rate limited"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Failed())
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError):
        llm.claude("prompt", model="haiku")
