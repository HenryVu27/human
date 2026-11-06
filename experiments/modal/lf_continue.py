"""Raw base-model continuations at length with vLLM (B34's B arm), the B31 setup with longer outputs.

bf16 weights from the Volume b31-weights, plain-text prompt (the human opening), temperature 0.8, top-p 0.95, a
per-request seed, no repetition penalty (as B31). One L40S container.

  modal run experiments/modal/lf_continue.py --prompts results/b34_cont_prompts.jsonl --out results/b34_cont_raw.jsonl

Input rows: {"id", "try", "seed", "opening", "max_tokens"}. Output rows add "text", "n_tokens", "finish".
"""

from __future__ import annotations

import json
import pathlib

import modal

app = modal.App("lf-continue")
VOL = modal.Volume.from_name("b31-weights")
IMAGE = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.32.0")
    .env({"HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1", "VLLM_LOGGING_LEVEL": "WARNING"})
)


@app.function(image=IMAGE, volumes={"/vol": VOL}, gpu="L40S", cpu=4, memory=32768, timeout=3600)
def sample(model: str, prompts: list[dict]) -> list[dict]:
    from vllm import LLM, SamplingParams

    llm = LLM(model=f"/vol/models/{model}", dtype="bfloat16", seed=0, enforce_eager=True, max_model_len=4096,
              gpu_memory_utilization=0.85)
    sps = [SamplingParams(temperature=0.8, top_p=0.95, max_tokens=p["max_tokens"], seed=p["seed"]) for p in prompts]
    outs = llm.generate([p["opening"] for p in prompts], sps)
    return [p | {"text": o.outputs[0].text, "n_tokens": len(o.outputs[0].token_ids), "finish": o.outputs[0].finish_reason}
            for p, o in zip(prompts, outs)]


@app.local_entrypoint()
def main(prompts: str, out: str, model: str = "allenai/OLMo-2-1124-13B/main"):
    rows = [json.loads(line) for line in pathlib.Path(prompts).read_text().splitlines()]
    res = sample.remote(model, rows)
    pathlib.Path(out).write_text("".join(json.dumps(r) + "\n" for r in res))
    print(len(res), "continuations", flush=True)
