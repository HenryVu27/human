"""B30 generation on Modal (amendment of 2026-11-06 01:08 in experiments/b30_rewriter.py).

Runs experiments/gpu/gen13b_guard.py unchanged: OLMo-2-1124-13B in 4-bit NF4, the B30 adapter in its PEFT
form, the same Guard file and common-word list, the same sampling and seeds, with the PC's library
versions. Each container takes one shard of (seed, prompts) and runs the script on it, so a prompt's
seed is set exactly as on the PC; only the GPU differs. The base weights come from the Volume B31 filled
(b31-weights, models/allenai/OLMo-2-1124-13B/main), symlinked to the hub id the script loads, and the
adapter from the same Volume (adapters/b30-rewritepool, uploaded with `modal volume put`).

  modal volume put b31-weights results/gpu13b/out_rewritepool/lora-13b-v1 adapters/b30-rewritepool
  modal run experiments/modal/b30_gen.py [--shards 10] [--gpu L4]

Writes results/b30_gen_s{0,1}.jsonl: the PC's rows first (kept where both exist), then Modal's, each
row tagged with the machine that wrote it.
"""

import json
import pathlib
import subprocess

import modal

ROOT = pathlib.Path(__file__).resolve().parents[2]
SP = pathlib.Path("/private/tmp/claude-501/-Users-henryvu-personal/4e64b86d-db0b-493c-bcf7-4834f916f083/scratchpad/push/b30m")
app = modal.App("b30-gen")
VOL = modal.Volume.from_name("b31-weights")
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.11.0", "transformers==5.22.1", "peft==0.21.2", "bitsandbytes==0.50.2",
                    "accelerate==1.15.0", "safetensors", extra_index_url="https://download.pytorch.org/whl/cu128")
    .env({"HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1", "PYTHONUTF8": "1"})
    .add_local_file(ROOT / "experiments" / "gpu" / "gen13b_guard.py", "/w/gen13b_guard.py")
    .add_local_file(SP / "guard.py", "/w/guard.py")  # fetched from C:/hgpu, identical to src/humanizer/pipeline/guard.py
    .add_local_file(SP / "common.json", "/w/common.json")  # fetched from C:/hgpu
)


@app.function(image=IMAGE, volumes={"/vol": VOL}, gpu="L4", cpu=4, memory=32768, timeout=3 * 3600)
def gen(seed: int, rows: list[dict], gpu: str) -> dict:
    import os
    import shutil

    w = pathlib.Path("/w")
    os.makedirs(w / "allenai", exist_ok=True)
    if not (w / "allenai" / "OLMo-2-1124-13B").exists():
        os.symlink("/vol/models/allenai/OLMo-2-1124-13B/main", w / "allenai" / "OLMo-2-1124-13B")
    shutil.copytree("/vol/adapters/b30-rewritepool", w / "adapter", dirs_exist_ok=True)
    (w / "shard.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = w / "out.jsonl"
    out.unlink(missing_ok=True)
    p = subprocess.run(["python", "gen13b_guard.py", "--adapter", "adapter", "--prompts", "shard.jsonl",
                        "--out", "out.jsonl", "--seed", str(seed), "--hours", "2.8"],
                       cwd=w, capture_output=True, text=True)
    got = [json.loads(line) | {"machine": f"modal-{gpu}"} for line in out.read_text().splitlines()] if out.exists() else []
    return {"seed": seed, "rows": got, "log": (p.stdout + p.stderr)[-3000:], "rc": p.returncode}


def shard(jobs: list[tuple[int, dict]], n: int) -> list[tuple[int, list[dict]]]:
    """Longest-first greedy split by max_new_tokens, one seed per shard."""
    out = []
    for seed in sorted({s for s, _ in jobs}):
        mine = sorted((r for s, r in jobs if s == seed), key=lambda r: -r["max_new_tokens"])
        k = max(1, round(n * len(mine) / len(jobs)))
        bins = [[] for _ in range(k)]
        for r in mine:
            min(bins, key=lambda b: sum(x["max_new_tokens"] for x in b)).append(r)
        out += [(seed, b) for b in bins if b]
    return out


@app.local_entrypoint()
def main(shards: int = 10, gpu: str = "L4"):
    prompts = [json.loads(line) for line in (ROOT / "results" / "b30_prompts.jsonl").open()]
    raw = {s: ROOT / "results" / f"b30_gen_s{s}_modal.jsonl" for s in (0, 1)}
    pc = {0: SP / "b30_gen_s0_pc.jsonl", 1: None}
    done = {s: {json.loads(line)["id"] for f in (raw[s], pc[s]) if f and f.exists() for line in f.open()} for s in (0, 1)}
    jobs = [(s, r) for s in (0, 1) for r in prompts if r["id"] not in done[s]]
    work = shard(jobs, shards)
    print(f"{len(jobs)} generations in {len(work)} shards on {gpu}")
    for res in gen.starmap([(s, rows, gpu) for s, rows in work], order_outputs=False, return_exceptions=True):
        if isinstance(res, Exception):
            print("SHARD_ERROR", repr(res)[:500])
            continue
        with raw[res["seed"]].open("a") as f:
            f.writelines(json.dumps(r) + "\n" for r in res["rows"])
        print(f"seed {res['seed']}: {len(res['rows'])} rows, rc {res['rc']}; {res['log'].strip().splitlines()[-1] if res['log'].strip() else ''}")
        if res["rc"]:
            print(res["log"])
    for s in (0, 1):
        rows = {}
        for f in (pc[s], raw[s]):
            if f and f.exists():
                for line in f.open():
                    r = json.loads(line)
                    rows.setdefault(r["id"], r | ({"machine": r.get("machine", "pc")}))
        order = [p["id"] for p in prompts if p["id"] in rows]
        (ROOT / "results" / f"b30_gen_s{s}.jsonl").write_text("".join(json.dumps(rows[i]) + "\n" for i in order))
        print(f"b30_gen_s{s}.jsonl: {len(order)} of {len(prompts)}")
    print("ALL_DONE" if all(sum(1 for _ in (ROOT / "results" / f"b30_gen_s{s}.jsonl").open()) == len(prompts) for s in (0, 1)) else "INCOMPLETE")
