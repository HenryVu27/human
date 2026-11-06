"""B31 on Modal: fetch base-model weights into a Volume, then sample plain-text continuations with vLLM.

Driven by experiments/b31_basedate.py; the design, selection and exclusion rules are in its docstring.
Every call is an ephemeral `modal run`, so nothing stays deployed or idle:

  modal run experiments/modal/b31_modal.py::fetch --specs results/b31_fetch.json
  modal run experiments/modal/b31_modal.py::gen --jobs results/b31_jobs.json --outdir results/b31_raw

Weights go to the Volume "b31-weights" (Modal includes 1 TiB of Volume storage), downloaded by CPU
containers so no GPU time is spent waiting on the network. Generation runs one container per model,
bf16 weights, no quantization, vLLM with a per-request seed.
"""

import json
import pathlib

import modal

app = modal.App("b31-basedate")
VOL = modal.Volume.from_name("b31-weights", create_if_missing=True)
IMAGE = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.32.0", "huggingface_hub[hf_xet]")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1", "VLLM_LOGGING_LEVEL": "WARNING"})
)
PATTERNS = ["*.json", "*.safetensors", "*.py", "*.txt", "*.model", "*.tiktoken", "tokenizer*"]
CHAT_INSTRUCTION = "Continue the following text. Output only the continuation.\n\n"  # B1's instruct prompt


def model_dir(repo: str, revision: str) -> str:
    return f"/vol/models/{repo}/{revision}"


@app.function(image=IMAGE, volumes={"/vol": VOL}, cpu=4, memory=8192, timeout=3600)
def download(repo: str, revision: str) -> dict:
    from huggingface_hub import HfApi, snapshot_download

    files = [s.rfilename for s in HfApi().model_info(repo, revision=revision).siblings]
    patterns = PATTERNS if any(f.endswith(".safetensors") for f in files) else PATTERNS + ["*.bin"]
    path = snapshot_download(repo, revision=revision, local_dir=model_dir(repo, revision), allow_patterns=patterns,
                             ignore_patterns=["consolidated*"])  # Mistral repos ship the weights twice
    VOL.commit()
    size = sum(p.stat().st_size for p in pathlib.Path(path).rglob("*") if p.is_file())
    return {"repo": repo, "revision": revision, "gb": round(size / 1e9, 1)}


@app.function(image=IMAGE, volumes={"/vol": VOL}, cpu=1, timeout=600)
def patch_config(repo: str, revision: str, patch: dict) -> dict:
    """Relabel a config in place, keeping the original as config.orig.json (Olmo 3's 2T ablation checkpoints
    say model_type "olmo2-retrofit", an internal name; their tensors match Olmo3ForCausalLM exactly)."""
    path = pathlib.Path(model_dir(repo, revision)) / "config.json"
    orig = path.with_name("config.orig.json")
    if not orig.exists():
        orig.write_text(path.read_text())
    cfg = json.loads(orig.read_text()) | patch
    path.write_text(json.dumps(cfg, indent=1))
    VOL.commit()
    return {k: cfg[k] for k in patch}


@app.local_entrypoint()
def relabel(specs: str):
    for s in json.loads(pathlib.Path(specs).read_text()):
        print(s["revision"], patch_config.remote(s["repo"], s["revision"], s["patch"]), flush=True)


@app.function(image=IMAGE, volumes={"/vol": VOL}, gpu="L40S", timeout=3600)
def sample(spec: dict, prompts: list[dict], params: dict) -> list[dict]:
    from vllm import LLM, SamplingParams

    VOL.reload()
    kw = dict(model=model_dir(spec["repo"], spec["revision"]), dtype="bfloat16", seed=0, enforce_eager=True,
              max_model_len=params["max_model_len"], gpu_memory_utilization=0.85,
              trust_remote_code=spec.get("trust_remote_code", False))
    if spec.get("multimodal"):
        kw["limit_mm_per_prompt"] = {"image": 0, "video": 0}
    llm = LLM(**kw)
    sps = [SamplingParams(temperature=params["temperature"], top_p=params["top_p"],
                          max_tokens=params["max_tokens"], seed=p["seed"]) for p in prompts]
    if spec.get("chat"):
        instruction = spec.get("chat_instruction", CHAT_INSTRUCTION)
        convs = [[{"role": "user", "content": instruction + p["opening"]}] for p in prompts]
        outs = llm.chat(convs, sps, chat_template_kwargs=spec.get("chat_template_kwargs"))
    else:
        outs = llm.generate([p["opening"] for p in prompts], sps)
    return [{"key": spec["key"], "doc": p["doc"], "try": p["try"], "seed": p["seed"], "text": o.outputs[0].text,
             "finish": o.outputs[0].finish_reason, "n_tokens": len(o.outputs[0].token_ids),
             "prompt_tokens": len(o.prompt_token_ids)} for p, o in zip(prompts, outs)]


@app.local_entrypoint()
def fetch(specs: str):
    todo = json.loads(pathlib.Path(specs).read_text())
    for r in download.starmap([(s["repo"], s["revision"]) for s in todo], order_outputs=False):
        print(json.dumps(r), flush=True)


@app.local_entrypoint()
def gen(jobs: str, outdir: str):
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    calls = []
    for job in json.loads(pathlib.Path(jobs).read_text()):
        fn = sample.with_options(gpu=job["spec"].get("gpu", "L40S"))
        calls.append((job["spec"]["key"], fn.spawn(job["spec"], job["prompts"], job["params"])))
    for key, call in calls:
        try:
            rows = call.get()
        except Exception as e:  # one model failing must not lose the others
            print(f"FAILED {key}: {type(e).__name__}: {e}", flush=True)
            continue
        (out / f"{key}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(f"done {key}: {len(rows)} samples", flush=True)
