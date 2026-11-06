"""B31: download gated base models (Llama, Gemma) into the B31 Volume with Henry's read token.

Kept apart from b31_modal.py so the main app never depends on the "huggingface" Modal secret, which Henry creates
himself; this code never reads or prints the token's value.

  modal run experiments/modal/b31_gated.py --specs results/b31_gated_fetch.json
"""

import json
import pathlib

import modal

app = modal.App("b31-gated")
VOL = modal.Volume.from_name("b31-weights", create_if_missing=True)
IMAGE = (  # same image as b31_modal.py, so Modal reuses the cached build
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.32.0", "huggingface_hub[hf_xet]")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1", "VLLM_LOGGING_LEVEL": "WARNING"})
)
PATTERNS = ["*.json", "*.safetensors", "*.py", "*.txt", "*.model", "*.tiktoken", "tokenizer*"]


def model_dir(repo: str, revision: str) -> str:
    return f"/vol/models/{repo}/{revision}"


@app.function(image=IMAGE, volumes={"/vol": VOL}, cpu=4, memory=8192, timeout=3600,
              secrets=[modal.Secret.from_name("huggingface")])
def download_gated(repo: str, revision: str) -> dict:
    import os

    from huggingface_hub import snapshot_download

    path = snapshot_download(repo, revision=revision, local_dir=model_dir(repo, revision), allow_patterns=PATTERNS,
                             ignore_patterns=["original/*", "consolidated*"], token=os.environ["HF_TOKEN"])
    VOL.commit()
    size = sum(p.stat().st_size for p in pathlib.Path(path).rglob("*") if p.is_file())
    return {"repo": repo, "revision": revision, "gb": round(size / 1e9, 1)}


@app.local_entrypoint()
def main(specs: str):
    todo = json.loads(pathlib.Path(specs).read_text())
    for r in download_gated.starmap([(s["repo"], s["revision"]) for s in todo], order_outputs=False,
                                    return_exceptions=True):
        print(json.dumps(r if isinstance(r, dict) else {"error": str(r)}), flush=True)
