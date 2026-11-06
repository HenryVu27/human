"""Open-detector panel on Modal: Binoculars, Fast-DetectGPT (two model choices), MELD and desklib.

Part of the long-form program (docs/specs/2026-11-06-longform-program.md). The panel is the development judge:
Pangram stays held out. Nothing here is trained, and no threshold or weight is fitted to Pangram labels.

  modal run experiments/modal/lf_detect.py::fetch                       # weights to the Volume, CPU only
  modal run experiments/modal/lf_detect.py::score --inp X.jsonl --out Y.jsonl [--only binoculars,meld]

Input rows: {"id", "text"}. Output rows: {"id", "<detector>": {...}} with an `ai` field oriented so that a higher
value means more AI-like, plus the raw score, token count and per-window values for later aggregation.

Detectors and their document rules, fixed 2026-11-06 02:04 CST, before any text was scored:
- binoculars: observer tiiuae/falcon-7b, performer tiiuae/falcon-7b-instruct (Hans et al. 2024, the released
  pair). Text is cut into consecutive 512-token windows (the published setting). Per token: performer
  log-perplexity and the cross-perplexity (observer probabilities against performer log-probabilities).
  Document score = sum of log-perplexity / sum of cross-perplexity over all windows; ai = -score. Also the share
  of windows below the released low-FPR threshold 0.8536.
- fdg_falcon: analytic Fast-DetectGPT from the same forward passes, sampling model falcon-7b, scoring model
  falcon-7b-instruct (the authors' second-ranked pair). Criterion = sum(ll - mu) / sqrt(sum var) over all scored
  tokens; ai = criterion. Shares its inputs with binoculars, so it is not an independent mechanism.
- fdg_llama: analytic Fast-DetectGPT, white-box, sampling = scoring = meta-llama/Llama-3.1-8B (base), 2,048-token
  windows with a BOS token each. The authors rank the Llama 3 8B pair first; the instruct half is not used
  because access to it is not verified. ai = criterion.
- meld: anon-review-meld-2026/meld at revision ddfc9c78 (Ettin-1B encoder, trained on 78 generators including
  claude-sonnet-4.6 and gpt-5-chat), its own meld.py Scorer unchanged (sha256 checked), canonicalized input,
  2,046-token windows, top-quantile pooling. ai = score; flagged above its shipped 1% FPR offset (3.92).
- desklib: desklib/ai-text-detector-v1.01 (DeBERTa-v3-large trained on RAID, 2023 generators): the model card's
  mean-pooled head, 768-token windows (the last one anchored at the end), document ai = token-weighted mean of
  window logits. An old-data control.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import modal

app = modal.App("lf-detect")
VOL = modal.Volume.from_name("b31-weights")
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.11.0", "transformers==5.22.1", "accelerate==1.15.0", "safetensors", "sentencepiece",
                    "protobuf", "huggingface_hub[hf_xet]", extra_index_url="https://download.pytorch.org/whl/cu128")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1", "PYTHONUTF8": "1",
          "TOKENIZERS_PARALLELISM": "false"})
)
MODELS = {
    "falcon": ("tiiuae/falcon-7b", "ec89142b67d748a1865ea4451372db8313ada0d8"),
    "falcon_instruct": ("tiiuae/falcon-7b-instruct", "8782b5c5d8c9290412416618f36a133653e85285"),
    "llama": ("meta-llama/Llama-3.1-8B", "main"),  # already on the Volume from B31
    "meld": ("anon-review-meld-2026/meld", "ddfc9c789b8c8d0f92d3774265316d418c96dc67"),
    "desklib": ("desklib/ai-text-detector-v1.01", "5fdea974cd4287c61674951ec78803aa274e2fb7"),
}
MELD_SHA256 = "c82d503a4a8f96430dfed6cc83c9ec8bdffea6591c4b43c6883ee0cd7b51567f"  # meld.py as read on 2026-11-06
BINO_LOW_FPR = 0.8536432310785527
PATTERNS = ["*.json", "*.safetensors", "*.txt", "*.model", "tokenizer*", "spm.model", "meld.py"]


def mdir(key: str) -> str:
    repo, rev = MODELS[key]
    return f"/vol/models/{repo}/{rev}"


@app.function(image=IMAGE, volumes={"/vol": VOL}, cpu=4, memory=8192, timeout=3600,
              secrets=[modal.Secret.from_name("huggingface")])
def download(key: str) -> dict:
    from huggingface_hub import snapshot_download

    repo, rev = MODELS[key]
    if pathlib.Path(mdir(key), "config.json").exists():
        return {"key": key, "cached": True}
    path = snapshot_download(repo, revision=rev, local_dir=mdir(key), allow_patterns=PATTERNS)
    VOL.commit()
    gb = sum(p.stat().st_size for p in pathlib.Path(path).rglob("*") if p.is_file()) / 1e9
    return {"key": key, "gb": round(gb, 1)}


@app.local_entrypoint()
def fetch(keys: str = "falcon,falcon_instruct,meld,desklib"):
    for r in download.map(keys.split(","), order_outputs=False):
        print(json.dumps(r), flush=True)


def windows(ids: list[int], size: int, anchor_end: bool = False) -> list[list[int]]:
    out = [ids[i:i + size] for i in range(0, len(ids), size)] or [[]]
    if anchor_end and len(ids) > size and len(out[-1]) < size:
        out[-1] = ids[-size:]
    return out


def _pair_stats(obs_logits, perf_logits, labels, mask, chunk=256):
    """Per-token Binoculars and Fast-DetectGPT terms, summed per row (positions already shifted).

    Works through the batch one row and `chunk` positions at a time, so a 128K-token vocabulary fits in memory."""
    import torch

    v = min(obs_logits.shape[-1], perf_logits.shape[-1])
    sums = torch.zeros(5, obs_logits.shape[0], dtype=torch.float64)
    for b in range(obs_logits.shape[0]):
        for c0 in range(0, obs_logits.shape[1], chunk):
            m = mask[b, c0:c0 + chunk].float()
            if m.sum() == 0:
                continue
            lp_perf = torch.log_softmax(perf_logits[b, c0:c0 + chunk, :v].float(), -1)
            p_obs = torch.softmax(obs_logits[b, c0:c0 + chunk, :v].float(), -1)
            ll = lp_perf.gather(-1, labels[b, c0:c0 + chunk].unsqueeze(-1)).squeeze(-1)  # log p_perf(x_t)
            ent = (p_obs * lp_perf).sum(-1)               # E_{q=obs}[log p_perf]; minus it is the cross-perplexity
            var = (p_obs * lp_perf.square()).sum(-1) - ent.square()
            sums[0, b] += float((ll * m).sum())
            sums[1, b] += float((-ent * m).sum())
            sums[2, b] += float((ent * m).sum())
            sums[3, b] += float((var * m).sum())
            sums[4, b] += float(m.sum())
            del lp_perf, p_obs
    return [sums[i] for i in range(5)]


def _batches(items, bs):
    for i in range(0, len(items), bs):
        yield items[i:i + bs]


def run_pair(rows, bs=8):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(mdir("falcon"))
    kw = dict(torch_dtype=torch.bfloat16, device_map="cuda")
    obs = AutoModelForCausalLM.from_pretrained(mdir("falcon"), **kw).eval()
    perf = AutoModelForCausalLM.from_pretrained(mdir("falcon_instruct"), **kw).eval()
    pad = tok.eos_token_id
    jobs = []  # (row index, window index, ids)
    for i, r in enumerate(rows):
        ids = tok(r["text"], add_special_tokens=False)["input_ids"]
        for j, w in enumerate(windows(ids, 512)):
            if len(w) >= 2:
                jobs.append((i, j, w))
    jobs.sort(key=lambda x: len(x[2]))
    acc = {}
    with torch.no_grad():
        for b in _batches(jobs, bs):
            L = max(len(x[2]) for x in b)
            inp = torch.full((len(b), L), pad, dtype=torch.long)
            att = torch.zeros((len(b), L), dtype=torch.long)
            for k, (_, _, w) in enumerate(b):
                inp[k, :len(w)] = torch.tensor(w)
                att[k, :len(w)] = 1
            inp, att = inp.cuda(), att.cuda()
            lo = obs(input_ids=inp, attention_mask=att).logits[:, :-1]
            lpf = perf(input_ids=inp, attention_mask=att).logits[:, :-1]
            stats = _pair_stats(lo, lpf, inp[:, 1:], att[:, 1:])
            for k, (i, j, _) in enumerate(b):
                acc.setdefault(i, []).append((j, *[float(s[k]) for s in stats]))
    out = []
    for i, r in enumerate(rows):
        ws = sorted(acc.get(i, []))
        if not ws:
            out.append({"id": r["id"], "binoculars": None, "fdg_falcon": None})
            continue
        ll = sum(w[1] for w in ws); xent = sum(w[2] for w in ws); mu = sum(w[3] for w in ws)
        var = sum(w[4] for w in ws); n = sum(w[5] for w in ws)
        bino = (-ll) / xent
        win_bino = [(-w[1]) / w[2] for w in ws]
        crit = (ll - mu) / max(var, 1e-9) ** 0.5
        out.append({"id": r["id"],
                    "binoculars": {"ai": -bino, "score": bino, "n_tokens": int(n),
                                   "share_windows_flagged": sum(x < BINO_LOW_FPR for x in win_bino) / len(win_bino),
                                   "windows": [round(x, 4) for x in win_bino]},
                    "fdg_falcon": {"ai": crit, "crit": crit, "per_token": (ll - mu) / n, "n_tokens": int(n),
                                   "windows": [round((w[1] - w[3]) / max(w[4], 1e-9) ** 0.5, 3) for w in ws]}})
    del obs, perf
    import gc
    gc.collect()
    torch.cuda.empty_cache()
    return out


def run_llama(rows, bs=2, size=2048):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(mdir("llama"))
    model = AutoModelForCausalLM.from_pretrained(mdir("llama"), torch_dtype=torch.bfloat16, device_map="cuda").eval()
    bos, pad = tok.bos_token_id, tok.eos_token_id
    jobs = []
    for i, r in enumerate(rows):
        ids = tok(r["text"], add_special_tokens=False)["input_ids"]
        for j, w in enumerate(windows(ids, size - 1)):
            if w:
                jobs.append((i, j, [bos] + w))
    jobs.sort(key=lambda x: len(x[2]))
    acc = {}
    with torch.no_grad():
        for b in _batches(jobs, bs):
            L = max(len(x[2]) for x in b)
            inp = torch.full((len(b), L), pad, dtype=torch.long)
            att = torch.zeros((len(b), L), dtype=torch.long)
            for k, (_, _, w) in enumerate(b):
                inp[k, :len(w)] = torch.tensor(w)
                att[k, :len(w)] = 1
            inp, att = inp.cuda(), att.cuda()
            logits = model(input_ids=inp, attention_mask=att).logits[:, :-1]
            stats = _pair_stats(logits, logits, inp[:, 1:], att[:, 1:])
            for k, (i, j, _) in enumerate(b):
                acc.setdefault(i, []).append((j, *[float(s[k]) for s in stats]))
    out = []
    for i, r in enumerate(rows):
        ws = sorted(acc.get(i, []))
        ll = sum(w[1] for w in ws); mu = sum(w[3] for w in ws); var = sum(w[4] for w in ws); n = sum(w[5] for w in ws)
        crit = (ll - mu) / max(var, 1e-9) ** 0.5 if n else None
        out.append({"id": r["id"], "fdg_llama": None if crit is None else
                    {"ai": crit, "crit": crit, "per_token": (ll - mu) / n, "n_tokens": int(n), "ppl": float(2.718281828 ** (-ll / n)),
                     "windows": [round((w[1] - w[3]) / max(w[4], 1e-9) ** 0.5, 3) for w in ws]}})
    del model
    import gc
    gc.collect()
    torch.cuda.empty_cache()
    return out


def run_meld(rows):
    import importlib.util
    import sys

    src = pathlib.Path(mdir("meld"), "meld.py")
    got = hashlib.sha256(src.read_bytes()).hexdigest()
    if got != MELD_SHA256:
        raise RuntimeError(f"meld.py changed: {got}")
    spec = importlib.util.spec_from_file_location("meld", src)
    meld = importlib.util.module_from_spec(spec)
    sys.modules["meld"] = meld
    spec.loader.exec_module(meld)
    scorer = meld.Scorer(mdir("meld"), device="cuda")
    out = []
    for r in rows:
        try:
            s = scorer.score(r["text"], batch_size=4)
            out.append({"id": r["id"], "meld": {"ai": s["score"], **{k: s[k] for k in
                        ("score", "p_ai", "flagged", "family", "task", "n_tokens", "truncated")}}})
        except ValueError as e:
            out.append({"id": r["id"], "meld": None, "meld_error": str(e)})
    return out


def run_desklib(rows, size=768, bs=8):
    import torch
    import torch.nn as nn
    from safetensors.torch import load_file
    from transformers import AutoConfig, AutoModel, AutoTokenizer

    d = mdir("desklib")
    tok = AutoTokenizer.from_pretrained(d)
    cfg = AutoConfig.from_pretrained(d)

    class Desklib(nn.Module):  # the model card's DesklibAIDetectionModel: mean pooling, one linear head
        def __init__(self):
            super().__init__()
            self.model = AutoModel.from_config(cfg)
            self.classifier = nn.Linear(cfg.hidden_size, 1)

        def forward(self, ids, att):
            h = self.model(ids, attention_mask=att)[0]
            m = att.unsqueeze(-1).float()
            return self.classifier((h * m).sum(1) / m.sum(1).clamp(min=1e-9)).squeeze(-1)

    net = Desklib()
    missing, unexpected = net.load_state_dict(load_file(f"{d}/model.safetensors"), strict=False)
    missing = [k for k in missing if "position_ids" not in k]
    if missing or unexpected:
        raise RuntimeError(f"desklib weights: missing {missing[:5]} unexpected {unexpected[:5]}")
    net = net.cuda().eval()
    cls, sep = tok.cls_token_id, tok.sep_token_id
    jobs = []
    for i, r in enumerate(rows):
        ids = tok(r["text"], add_special_tokens=False)["input_ids"]
        for w in windows(ids, size - 2, anchor_end=True):
            if w:
                jobs.append((i, [cls] + w + [sep]))
    acc = {}
    with torch.no_grad():
        for b in _batches(jobs, bs):
            L = max(len(x[1]) for x in b)
            inp = torch.full((len(b), L), tok.pad_token_id, dtype=torch.long)
            att = torch.zeros((len(b), L), dtype=torch.long)
            for k, (_, w) in enumerate(b):
                inp[k, :len(w)] = torch.tensor(w)
                att[k, :len(w)] = 1
            logit = net(inp.cuda(), att.cuda()).float().cpu()
            for k, (i, w) in enumerate(b):
                acc.setdefault(i, []).append((float(logit[k]), len(w) - 2))
    out = []
    for i, r in enumerate(rows):
        ws = acc.get(i, [])
        n = sum(x[1] for x in ws)
        z = sum(x[0] * x[1] for x in ws) / n if n else None
        out.append({"id": r["id"], "desklib": None if z is None else
                    {"ai": z, "logit": z, "p_ai": 1 / (1 + 2.718281828 ** (-z)), "n_tokens": n,
                     "windows": [round(x[0], 3) for x in ws]}})
    return out


RUNNERS = {"binoculars": run_pair, "fdg_llama": run_llama, "meld": run_meld, "desklib": run_desklib}


@app.function(image=IMAGE, volumes={"/vol": VOL}, gpu="L40S", cpu=4, memory=32768, timeout=3 * 3600)
def score_all(rows: list[dict], only: list[str]) -> dict:
    import subprocess
    import time

    VOL.reload()
    merged = {r["id"]: {"id": r["id"]} for r in rows}
    timing = {}
    for name in only:
        t = time.time()
        try:
            for o in RUNNERS[name](rows):
                merged[o["id"]].update({k: v for k, v in o.items() if k != "id"})
        except Exception as e:  # one detector failing must not lose the others
            import traceback
            timing[name + "_error"] = f"{type(e).__name__}: {e}"[:500]
            print(traceback.format_exc()[-2000:], flush=True)
        timing[name] = round(time.time() - t, 1)
        print(f"{name}: {timing[name]} s", flush=True)
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True,
                         text=True).stdout.strip()
    return {"rows": list(merged.values()), "timing": timing, "gpu": gpu}


@app.local_entrypoint()
def score(inp: str, out: str, only: str = "binoculars,fdg_llama,meld,desklib"):
    rows = [json.loads(line) for line in pathlib.Path(inp).read_text().splitlines()]
    rows = [{"id": r["id"], "text": r["text"]} for r in rows]
    res = score_all.remote(rows, only.split(","))
    pathlib.Path(out).write_text("".join(json.dumps(r) + "\n" for r in res["rows"]))
    print(json.dumps({"n": len(res["rows"]), "timing": res["timing"], "gpu": res["gpu"]}), flush=True)
