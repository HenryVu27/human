"""Convert a PEFT LoRA adapter trained on the PC (OLMo-2-13B, QLoRA) into an mlx_lm adapter directory.

PEFT stores lora_A as (r, in) and lora_B as (out, r) with scale alpha / r; mlx_lm's LoRALinear
computes y + scale * (x @ lora_a) @ lora_b, so lora_a = A.T and lora_b = B.T.

Usage: uv run python experiments/peft_to_mlx.py PEFT_DIR OUT_DIR
"""

import json
import re
import sys
from pathlib import Path

import mlx.core as mx
from safetensors.numpy import load_file


def convert(src: Path, out: Path):
    cfg = json.loads((src / "adapter_config.json").read_text())
    w = load_file(str(src / "adapter_model.safetensors"))
    new, layers, keys = {}, set(), set()
    for k, v in w.items():
        m = re.fullmatch(r"base_model\.model\.(model\.layers\.(\d+)\.(\w+\.\w+))\.lora_([AB])\.weight", k)
        layers.add(int(m.group(2)))
        keys.add(m.group(3))
        new[f"{m.group(1)}.lora_{m.group(4).lower()}"] = mx.array(v.T.copy())
    out.mkdir(parents=True, exist_ok=True)
    mx.save_safetensors(str(out / "adapters.safetensors"), new)
    (out / "adapter_config.json").write_text(json.dumps({
        "fine_tune_type": "lora", "num_layers": len(layers),
        "lora_parameters": {"rank": cfg["r"], "scale": cfg["lora_alpha"] / cfg["r"], "dropout": 0.0,
                            "keys": sorted(keys)},
        "source": str(src)}, indent=1))
    print(len(new), "tensors;", len(layers), "layers;", sorted(keys))


if __name__ == "__main__":
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
