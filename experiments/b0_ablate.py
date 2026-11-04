"""B0 scripted arm: remove an "AI register" direction from Qwen3.5-4B instruct by editing weights.

Directional ablation (Arditi et al. 2024), applied to style instead of refusal:
  1. Read topic-matched human texts and AI mirrors with the instruct model, and
     take the mean residual-stream activation per layer for each side.
  2. r_l = normalize(mean_ai_l - mean_human_l). Pick the layer whose direction
     best separates held-out pairs (AUROC), among the middle layers.
  3. For every layer, project r out of each matrix that writes to the residual
     stream (attention or linear-attention output, MLP down projection):
     W <- W - r r^T W. Embeddings are tied to the output head, so left alone.
  4. Generate from 20 dev mirror prompts with the original and the edited model,
     and compare local detector P(AI), length and a pairwise quality judge.

Variant "posttrain": r_l = normalize(mean_instruct_l - mean_base_l) on the same
human texts, i.e. the direction post-training added.
"""

import argparse
import json
import statistics

import mlx.core as mx
import numpy as np

from humanizer import ROOT
from humanizer.data.mirror import mirror_prompt

INSTRUCT, BASE = "Qwen/Qwen3.5-4B", "Qwen/Qwen3.5-4B-Base"
RES = ROOT / "results"
MAX_TOK, SKIP = 384, 8


def _layers(model):
    return model.language_model.model.layers


def mean_acts(model, tok, texts):
    """Per-layer mean residual activation over token positions: [L, n, H]."""
    from mlx_lm.models import qwen3_5

    store = {}
    orig = qwen3_5.DecoderLayer.__call__
    index = {id(layer): i for i, layer in enumerate(_layers(model))}

    def rec(self, x, *a, **k):
        out = orig(self, x, *a, **k)
        store[index[id(self)]] = out[0, SKIP:].astype(mx.float32).mean(axis=0)
        return out

    qwen3_5.DecoderLayer.__call__ = rec
    try:
        rows = []
        for t in texts:
            ids = tok.encode(t)[:MAX_TOK]
            model(mx.array([ids]))
            mx.eval(list(store.values()))
            rows.append(np.stack([np.array(store[i]) for i in range(len(store))]))
    finally:
        qwen3_5.DecoderLayer.__call__ = orig
    return np.stack(rows, axis=1)


def auroc(pos, neg):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score([1] * len(pos) + [0] * len(neg), list(pos) + list(neg)))


def pairs(n_fit=150, n_val=50):
    human = {r["id"]: r for r in map(json.loads, (ROOT / "data/human.jsonl").open())}
    ai = [json.loads(line) for line in (ROOT / "data/ai.jsonl").open()]
    ai = [a for a in ai if not a["generator"].startswith("mlx")][: n_fit + n_val]  # Claude mirrors only
    h = [human[a["source_id"]]["text"] for a in ai]
    t = [a["text"] for a in ai]
    return (t[:n_fit], h[:n_fit]), (t[n_fit:], h[n_fit:])


def directions(variant: str):
    from mlx_lm import load

    (ai_fit, hu_fit), (ai_val, hu_val) = pairs()
    model, tok = load(INSTRUCT)
    A, H = mean_acts(model, tok, ai_fit), mean_acts(model, tok, hu_fit)
    Av, Hv = mean_acts(model, tok, ai_val), mean_acts(model, tok, hu_val)
    if variant == "posttrain":
        del model
        mx.clear_cache()
        base, btok = load(BASE)
        B = mean_acts(base, btok, hu_fit)
        diff = H.mean(1) - B.mean(1)
    else:
        diff = A.mean(1) - H.mean(1)
    r = diff / np.linalg.norm(diff, axis=-1, keepdims=True)
    L = r.shape[0]
    sep = [auroc(Av[i] @ r[i], Hv[i] @ r[i]) for i in range(L)]
    lo, hi = int(0.2 * L), int(0.8 * L)
    best = max(range(lo, hi), key=lambda i: sep[i])
    np.save(RES / f"b0_dir_{variant}.npy", r[best])
    info = {"variant": variant, "layer": best, "val_auroc_by_layer": [round(s, 3) for s in sep]}
    (RES / f"b0_dir_{variant}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))
    return r[best]


def ablate(model, r: np.ndarray, alpha: float = 1.0):
    rr = mx.array(r.astype(np.float32))
    for layer in _layers(model):
        mods = [layer.linear_attn.out_proj if layer.is_linear else layer.self_attn.o_proj, layer.mlp.down_proj]
        for m in mods:
            W = m.weight.astype(mx.float32)
            m.weight = (W - alpha * mx.outer(rr, rr @ W)).astype(m.weight.dtype)
    mx.eval(model.parameters())


def generate_set(model, tok, prompts):
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler

    out = []
    for i, p in enumerate(prompts):
        chat = tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False,
                                       add_generation_prompt=True, enable_thinking=False)
        mx.random.seed(i)
        out.append(generate(model, tok, chat, max_tokens=900, sampler=make_sampler(temp=0.7, top_p=0.95)))
    return out


def evaluate(variant: str, alpha: float, n: int):
    from mlx_lm import load

    r = np.load(RES / f"b0_dir_{variant}.npy")
    topics = {t["id"]: t for t in map(json.loads, (ROOT / "data/topics.jsonl").open())}
    docs = [json.loads(line) for line in (ROOT / "data/human.jsonl").open()][600:600 + n]
    prompts = [mirror_prompt(topics[d["id"]], 600) for d in docs if d["id"] in topics]
    model, tok = load(INSTRUCT)
    before = generate_set(model, tok, prompts)
    ablate(model, r, alpha)
    after = generate_set(model, tok, prompts)
    rows = [{"prompt": p, "before": b, "after": a} for p, b, a in zip(prompts, before, after)]
    path = RES / f"b0_gen_{variant}_a{alpha}.jsonl"
    path.write_text("".join(json.dumps(x) + "\n" for x in rows))
    del model
    mx.clear_cache()
    score(path)


def score(path):
    from humanizer.checks.quality import quality_pair
    from humanizer.detect.score import Detector

    det = Detector.load(ROOT / "models" / "detector-v1")
    rows = [json.loads(line) for line in path.open()]
    pb = [det.score(x["before"]) for x in rows]
    pa = [det.score(x["after"]) for x in rows]
    q = [quality_pair(x["before"], x["after"]) for x in rows]  # edited output vs original output
    res = {"n": len(rows), "before_mean_p_ai": statistics.mean(pb), "after_mean_p_ai": statistics.mean(pa),
           "after_share_below_0.5": sum(p < 0.5 for p in pa) / len(pa),
           "quality_after_vs_before": statistics.mean(q),
           "words_before": statistics.mean(len(x["before"].split()) for x in rows),
           "words_after": statistics.mean(len(x["after"].split()) for x in rows)}
    out = path.with_name(path.stem.replace("b0_gen", "b0_result") + ".json")
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["directions", "evaluate", "score"])
    ap.add_argument("--variant", default="ai_vs_human", choices=["ai_vs_human", "posttrain"])
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--path")
    a = ap.parse_args()
    if a.step == "directions":
        directions(a.variant)
    elif a.step == "evaluate":
        evaluate(a.variant, a.alpha, a.n)
    else:
        score(ROOT / "results" / a.path)
