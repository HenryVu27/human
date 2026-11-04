"""Every model call goes through here: headless Claude Code and local MLX models.

Both are cached on disk by a hash of their inputs, so a crashed batch resumes
without paying for finished calls twice.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from humanizer import ROOT

CACHE = ROOT / ".cache" / "llm"
DEFAULT_SYSTEM = "You are a careful writing assistant. Follow the user's instructions exactly and output only what they ask for."


def _key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def _cache_get(key: str) -> str | None:
    p = CACHE / key[:2] / f"{key}.json"
    return json.loads(p.read_text())["text"] if p.exists() else None


def _cache_put(key: str, text: str) -> None:
    p = CACHE / key[:2] / f"{key}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"text": text}))


def claude(prompt: str, *, model: str = "haiku", system: str | None = None, retries: int = 3) -> str:
    """One headless Claude Code call with no tools, no MCP and no CLAUDE.md context."""
    key = _key("claude", model, system, prompt)
    if (hit := _cache_get(key)) is not None:
        return hit
    cmd = [
        "claude", "-p", "--model", model, "--output-format", "json",
        "--system-prompt", system or DEFAULT_SYSTEM,
        "--tools", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--no-session-persistence", "--setting-sources", "",
    ]
    err = ""
    for attempt in range(retries):
        # neutral cwd so no project CLAUDE.md is discovered
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                              cwd=tempfile.gettempdir(), timeout=900)
        if proc.returncode == 0:
            out = json.loads(proc.stdout)
            if not out.get("is_error"):
                _cache_put(key, out["result"])
                return out["result"]
            err = out.get("result", "")
        else:
            err = proc.stderr or proc.stdout
        time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"claude -p failed after {retries} attempts: {err[:500]}")


def claude_many(prompts: list[str], *, model: str = "haiku", system: str | None = None,
                workers: int = 4) -> list[str | None]:
    """Parallel claude() calls. A failed call yields None instead of sinking the batch."""
    def one(p):
        try:
            return claude(p, model=model, system=system)
        except Exception as e:  # noqa: BLE001
            print(f"[claude_many] failed: {e}")
            return None

    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(one, prompts))


_loaded: dict[str, tuple] = {}


def load_mlx(model_id: str):
    """Keep at most one MLX model in memory (16 GB machine)."""
    if model_id not in _loaded:
        _loaded.clear()
        import gc

        import mlx.core as mx
        gc.collect()
        mx.clear_cache()
        from mlx_lm import load
        _loaded[model_id] = load(model_id)
    return _loaded[model_id]


def local_generate(model_id: str, prompt: str, *, max_tokens: int, temp: float = 0.8,
                   top_p: float = 0.95, chat: bool = False, seed: int = 0, kv_bits: int | None = None) -> str:
    """Sample from a local MLX model. chat=True applies the instruct chat template.

    kv_bits quantizes the KV cache: OLMo-2-13B has no grouped-query attention, so a
    4k-token prompt needs about 3.3 GB of cache on top of 8.5 GB of weights, past the
    Metal limit on a 16 GB Mac. kv_bits=4 brings the cache under 1 GB.
    """
    parts = ("mlx", model_id, prompt, max_tokens, temp, top_p, chat, seed)
    key = _key(*parts) if kv_bits is None else _key(*parts, kv_bits)
    if (hit := _cache_get(key)) is not None:
        return hit
    import mlx.core as mx
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_logits_processors, make_sampler

    model, tok = load_mlx(model_id)
    if chat:
        prompt = tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                         add_generation_prompt=True, enable_thinking=False)
    mx.random.seed(seed)
    text = generate(model, tok, prompt, max_tokens=max_tokens,
                    sampler=make_sampler(temp=temp, top_p=top_p),
                    logits_processors=make_logits_processors(repetition_penalty=1.05),
                    prefill_step_size=512, kv_bits=kv_bits, quantized_kv_start=0)
    _cache_put(key, text)
    return text
