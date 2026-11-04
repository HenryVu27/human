"""QLoRA fine-tune of OLMo-2-13B base on (notes -> human article) pairs, for the CUDA box.

Same data and prompt format as the MLX 7B run (data/lora): prompt + completion + EOS,
loss on the completion only. The 100k-token vocabulary makes full logits at 2,560
tokens the memory peak, so the loss runs through lm_head in checkpointed chunks.

Usage: python train13b.py --data DIR --out DIR [--smoke 5]
"""

import argparse
import json
import math
import random
import time

import torch
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

MODEL = "allenai/OLMo-2-1124-13B"
MAX_LEN = 2560


def load_rows(path):
    return [json.loads(line) for line in open(path, encoding="utf-8")]


def encode(tok, row):
    p = tok(row["prompt"]).input_ids
    c = tok(row["completion"], add_special_tokens=False).input_ids + [tok.eos_token_id]
    ids = (p + c)[:MAX_LEN]
    labels = ([-100] * len(p) + c)[:MAX_LEN]
    return ids, labels, len(p) + len(c) > MAX_LEN


def chunked_loss(causal_lm, ids, labels, chunk=512):
    h = causal_lm.model(input_ids=ids).last_hidden_state[:, :-1]
    y = labels[:, 1:]
    n = (y != -100).sum()
    head = causal_lm.lm_head

    def piece(hs, ys):
        return F.cross_entropy(head(hs).float().reshape(-1, head.out_features), ys.reshape(-1),
                               ignore_index=-100, reduction="sum")

    total = h.new_zeros((), dtype=torch.float32)
    for i in range(0, h.size(1), chunk):
        ys = y[:, i:i + chunk]
        if (ys != -100).any():
            total = total + checkpoint(piece, h[:, i:i + chunk], ys, use_reentrant=False)
    return total, n


@torch.no_grad()
def val_loss(causal_lm, data):
    tot, n = 0.0, 0
    for ids, labels, _ in data:
        t, k = chunked_loss(causal_lm, torch.tensor([ids], device="cuda"), torch.tensor([labels], device="cuda"))
        tot += t.item()
        n += k.item()
    return tot / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--smoke", type=int, default=0, help="optimizer steps for a smoke test; 0 = full epoch")
    a = ap.parse_args()

    import bitsandbytes as bnb
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, get_cosine_schedule_with_warmup

    torch.manual_seed(0)
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, device_map={"": 0}, attn_implementation="sdpa", dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
    # Not prepare_model_for_kbit_training: it upcasts embeddings and lm_head to fp32 (+2 GB at 13B).
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                                             target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                                             "gate_proj", "up_proj", "down_proj"]))
    causal_lm = model.base_model.model

    train = [encode(tok, r) for r in load_rows(f"{a.data}/train.jsonl")]
    valid = [encode(tok, r) for r in load_rows(f"{a.data}/valid.jsonl")]
    ids, labels, _ = train[0]
    b = labels.index(next(x for x in labels if x != -100))
    print("BOUNDARY:", repr(tok.decode(ids[max(0, b - 20):b])), "|||", repr(tok.decode(ids[b:b + 20])), flush=True)

    accum = 4
    steps = a.smoke or math.ceil(len(train) / accum)
    opt = bnb.optim.PagedAdamW8bit([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    sched = get_cosine_schedule_with_warmup(opt, 10 if not a.smoke else 1, steps)
    order = list(range(len(train)))
    random.Random(0).shuffle(order)

    summary = {"model": MODEL, "max_len": MAX_LEN, "truncated": sum(t for *_, t in train),
               "train_rows": len(train), "valid_rows": len(valid), "steps": steps, "loss_curve": [],
               "versions": {"torch": torch.__version__, "cuda": torch.version.cuda,
                            "gpu": torch.cuda.get_device_name(0)}}
    for m in ("transformers", "peft", "bitsandbytes"):
        summary["versions"][m] = __import__(m).__version__
    model.eval()
    if not a.smoke:
        summary["val_loss_before"] = val_loss(causal_lm, valid)
        print("val before", summary["val_loss_before"], flush=True)
    model.train()
    t0, it, run = time.time(), 0, []
    for step in range(steps):
        tot, n = 0.0, 0
        for _ in range(accum):
            ids, labels, _ = train[order[it % len(order)]]
            it += 1
            loss_sum, k = chunked_loss(causal_lm, torch.tensor([ids], device="cuda"), torch.tensor([labels], device="cuda"))
            (loss_sum / 2000).backward()  # fixed scale; per-token mean is reported below
            tot += loss_sum.item()
            n += k.item()
        opt.step()
        sched.step()
        opt.zero_grad(set_to_none=True)
        run.append(tot / n)
        if (step + 1) % 10 == 0 or a.smoke:
            el = time.time() - t0
            summary["loss_curve"].append([step + 1, sum(run) / len(run)])
            print(f"step {step + 1}/{steps} loss {sum(run) / len(run):.4f} {el / (step + 1):.1f}s/step "
                  f"peak {torch.cuda.max_memory_allocated() / 2**30:.1f}GB", flush=True)
            run = []
    summary["sec_per_step"] = (time.time() - t0) / steps
    summary["peak_gb"] = torch.cuda.max_memory_allocated() / 2**30
    model.eval()
    if not a.smoke:
        summary["val_loss_after"] = val_loss(causal_lm, valid)
        print("val after", summary["val_loss_after"], flush=True)
        model.save_pretrained(f"{a.out}/lora-13b-v1")
    summary["wall_s"] = time.time() - t0
    json.dump(summary, open(f"{a.out}/summary{'_smoke' if a.smoke else ''}.json", "w"), indent=1)
    print("TRAIN_OK", flush=True)


if __name__ == "__main__":
    main()
