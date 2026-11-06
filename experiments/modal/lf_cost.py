"""Modal cost estimator for the long-form program: run it before every job and log the estimate.

Prices are Modal's per-second list prices read from modal.com/pricing on 2026-11-06, converted to hours. A GPU
container also pays for its CPU cores and memory, which the estimate includes (a common miss: 4 cores and 32 GiB
add about $0.44 an hour to any GPU).

  python experiments/modal/lf_cost.py                     # the phase table in the design doc
  python experiments/modal/lf_cost.py L40S 0.5 --cores 4 --gib 32
"""

from __future__ import annotations

import argparse

GPU_PER_HOUR = {"B200": 6.25, "H200": 4.54, "H100": 3.95, "A100-80GB": 2.50, "A100-40GB": 2.10, "L40S": 1.95,
                "A10": 1.10, "L4": 0.80, "T4": 0.59, "CPU": 0.0}
CORE_PER_HOUR = 0.0472   # $0.0000131 per physical core per second
GIB_PER_HOUR = 0.0080    # $0.00000222 per GiB per second


def cost(gpu: str, hours: float, cores: float = 4, gib: float = 32, containers: int = 1) -> float:
    return round(containers * hours * (GPU_PER_HOUR[gpu] + cores * CORE_PER_HOUR + gib * GIB_PER_HOUR), 2)


# Phase 2 jobs: (phase, job, gpu, hours, containers, cores, GiB, basis). Hours are estimates from measured phase 1
# throughput where available (detector panel, corpus shards) and from published or typical vLLM and LoRA throughput
# otherwise; see the design doc section 10 for the assumptions behind each line.
PLAN_SMALL = [
    ("2a", "B32 full corpus: 40 FineWeb shards", "CPU", 0.15, 40, 4, 16, "measured: about 6 to 9 min per shard"),
    ("2a", "B32 genre labels (9B instruct, 12k docs, prefill only)", "L40S", 0.3, 1, 4, 32, "about 8M prompt tokens"),
    ("2a", "B32 Dolma 3 contamination stream (if Olmo 3 is chosen)", "CPU", 0.3, 50, 2, 8, "4.4 TB in 50 slices"),
    ("2b", "B35 notes and rewording, 7k docs (27B instruct)", "H100", 1.5, 1, 4, 64, "8.4M output tokens at about 2k/s"),
    ("2b", "B35 AI posts for training, 6k docs (3 open 8 to 12B families)", "L40S", 2.0, 1, 4, 32, "16M output tokens at about 3k/s, 3 loads"),
    ("2d", "B37 stage A: 6 base models, 40 dev openings to 2,000 words", "H100", 1.2, 1, 4, 64, "load-dominated"),
    ("2d", "B37 stage B: LoRA on 1,500 pairs, 2 finalists (8B-class)", "L40S", 4.0, 1, 4, 32, "9M tokens each at about 1.5k/s"),
    ("2d", "B37 stage B: dev generation and panel", "L40S", 1.0, 1, 4, 32, ""),
    ("2e", "B37 writers: 12k pairs, about 60M tokens, 1 epoch (8B-class, LoRA)", "H100", 5.0, 1, 4, 64, "about 3.5k tokens/s"),
    ("2e", "B37 data-scale ablation (1,000-doc writer)", "H100", 0.8, 1, 4, 64, ""),
    ("2f", "B38 and B39 generation with the Guard, best of 4", "L40S", 1.5, 1, 4, 32, "3.2M output tokens at about 1k/s"),
    ("2f", "Open-model claim check on about 1,100 outputs (27B)", "H100", 1.2, 1, 4, 64, "6M prompt, 1.6M output tokens"),
    ("2f", "MELD on all dev and test outputs and corpus slices", "L40S", 0.7, 1, 4, 32, "measured panel throughput"),
    ("2c", "B34 base continuations at length (8 docs)", "L40S", 0.3, 1, 4, 32, ""),
    ("2c", "B36 CAI-old: B30 rewriter, 32 docs x 2 seeds, 4-bit transformers", "A10", 3.0, 1, 4, 32, "B30: $6 for 114 texts of 640 words"),
]
# A 24 to 32B writer changes B37 stage B, B37 training and generation.
PLAN_LARGE_DELTA = [
    ("2d", "B37 stage B with one 32B finalist (QLoRA, H100)", "H100", 4.5, 1, 4, 64, "9M tokens at about 600/s"),
    ("2e", "B37 writers on a 32B base", "H100", 24.0, 1, 4, 64, "60M tokens at about 700/s"),
    ("2f", "Generation on a 32B base", "H100", 2.5, 1, 4, 64, "about 400 tokens/s with the Guard"),
]


def table(plan) -> float:
    total = 0.0
    for ph, job, gpu, h, n, cores, gib, basis in plan:
        c = cost(gpu, h, cores, gib, n)
        total += c
        print(f"{ph:3} {gpu:5} {h:5.2f} h x{n:<3} ${c:7.2f}  {job}  ({basis})")
    print(f"    total ${total:.2f}")
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("gpu", nargs="?")
    ap.add_argument("hours", nargs="?", type=float)
    ap.add_argument("--cores", type=float, default=4)
    ap.add_argument("--gib", type=float, default=32)
    ap.add_argument("--containers", type=int, default=1)
    a = ap.parse_args()
    if a.gpu:
        print(cost(a.gpu, a.hours, a.cores, a.gib, a.containers))
    else:
        small = table(PLAN_SMALL)
        print()
        replaced = {"B37 stage B: LoRA on 1,500 pairs, 2 finalists (8B-class)", "B37 writers: 12k pairs, about 60M tokens, 1 epoch (8B-class, LoRA)",
                    "B38 and B39 generation with the Guard, best of 4"}
        large = table([p for p in PLAN_SMALL if p[1] not in replaced] + PLAN_LARGE_DELTA)
        print(f"\n8B-class writer ${small:.0f}; 24 to 32B writer ${large:.0f}; add 25% for smoke tests and reruns: "
              f"${small * 1.25:.0f} and ${large * 1.25:.0f}")
