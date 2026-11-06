# Research agent report: long-context open base models for the long-form program (2026-11-06)

## Brief given to the agent

Work at expert depth, start from raw data, verify with an external check, report what you could not verify.

GOAL BEHIND THE TASK: the humanizer project (~/personal/human) is moving from OLMo-2-13B (4,096-token context, 4-bit on a 16 GB GPU) to a long-context open base model, served with vLLM on Modal GPUs, that can be fine-tuned (QLoRA or LoRA) on thousands of pre-ChatGPT blog posts of 1,500 to 4,000 words and then write whole posts (up to about 6,000 tokens of output with up to 6,000 tokens of input notes or draft). Faithfulness rule: the output may add no facts, names, numbers, dates or quotes; today a Hugging Face logits processor (the "Guard") bans tokens that would start a name or number not in the input. The design must pick among candidate base models by a rule fixed in advance on development metrics. Today is 2026-11-06.

TASKS
1. Verify each candidate on its Hugging Face model card, the Hugging Face API (https://huggingface.co/api/models/<id>: createdAt, gated, license, config.json max_position_embeddings and rope_scaling), and its technical report: Olmo 3 base 7B and 32B (allenai/Olmo-3-1025-7B, allenai/Olmo-3-1125-32B; also any Olmo 3.1 or later base release), Gemma 3 27B pt (google/gemma-3-27b-pt), Llama 3.1 8B and 70B base, Mistral Small 24B base (2501, and any 3.1 or 3.2 base with 128K context), Qwen3.5 base models (which sizes have base checkpoints; context length), and any other 2025 to 2026 open base model with long context and open training data (for example Marin, Apertus, SmolLM3, OLMo variants, Nemotron base). For each give: exact repo ID, release date, parameter count, native trained context and how it was extended (stages, RoPE theta or YaRN), claimed long-context evaluation (RULER or similar), license and gating, whether the pretraining data is open and searchable, the stated data cutoff, the vLLM version and architecture class that supports it, bf16 weight size, and which single Modal GPU (L40S 48 GB, A100 80 GB, H100 80 GB) fits it for inference at 16K context and for QLoRA training at 8K sequence length.
2. Contamination checking: what tools exist to check whether a given document is in Olmo 3's training data (Dolma 3): infini-gram, OLMoTrace, WIMBD, or a public API; endpoints, which corpora they index, rate limits, and whether Dolma 3 / Olmo 3 data mixes are indexed. Same for FineWeb if any.
3. vLLM faithfulness hooks in the current vLLM (the project uses vllm==0.32.0 on Modal; find the current release and its docs): how to apply a custom per-request logits processor in the V1 engine (the LogitsProcessor class interface, how to register it, whether it can depend on per-request state such as the allowed names and numbers of that request's input), whether `bad_words` or `allowed_token_ids` in SamplingParams handle multi-token sequences, and structured-output alternatives. Give a minimal code sketch of a per-request processor that bans any token which would begin a capitalized word or digit string not present in that request's input.
4. Long-context fine-tuning on one GPU: current recipes (PEFT QLoRA with gradient checkpointing, Unsloth, Axolotl, TRL) and measured memory or throughput numbers for 7B to 32B at 8K to 16K sequence length.

RULES: read only. WebSearch and WebFetch. Do not sign in, create accounts, accept licenses, or download and run code. No emojis, no em dashes, spell out acronyms on first use, no blockquotes.

OUTPUT: write your full report to `/Users/henryvu/personal/human/results/research/longform-base-models.md`, starting with a "Brief given to the agent" section (paste this brief), then "## Report". Under 1,300 words; a table for task 1; every item marked V (read in primary source) or U with links; end with "What I could not verify". Return the same report as your final message.

## Report

V = read in the primary source (Hugging Face (HF) API, config, card, paper, vLLM code or docs). U = unverified or my arithmetic. KV = key-value cache; QLoRA = 4-bit quantized low-rank adaptation; RoPE = rotary position embedding (YaRN scales it); RULER and HELMET are long-context benchmarks.

**Bottom line**
- Base RULER at 16K is highest for Mistral Small 3.1 24B and Llama 3.1 8B; HELMET at 16K ranks Gemma 3 27B first (49.9), Llama 8B last (43.5) ([Olmo 3 paper](https://arxiv.org/abs/2512.13961) Table 12, V).
- In the table only Olmo 3 ships its exact training data. New: base model `google/gemma-4-31B`, Apache-2.0, ungated (V).
- Finding (V, [registry at v0.32.0](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/model_executor/models/registry.py)): vLLM 0.32.0 runs `Olmo3ForCausalLM` through the Transformers backend, not native code. Measure its speed and KV use.

### 1. Candidates

Columns 1 to 8 V (HF API, config, cards; RULER from Olmo 3 Table 12 unless noted). Created is HF repo creation; public release was 2025-11-20 for Olmo 3 and 2024-07-23 for Llama 3.1. Fit column U (my arithmetic). Gemma, Mistral 3.1, Ministral 3 and Qwen3.5 include a vision encoder.

| Repo ID | Created | Params (bf16) | Context; extension | RULER 16/32/65K | License | Data; cutoff | vLLM 0.32 class | 16K serve / 8K QLoRA |
|---|---|---|---|---|---|---|---|---|
| `allenai/Olmo-3-1025-7B` | 2025-09-12 | 7.30B (14.6 GB) | 65,536; 8K pretrain, 50B-token stage, YaRN x8 on full-attention layers, 3 of 4 layers sliding (4,096) | 84.1/78.8/68.0 | Apache, open | Open; Dec 2024 | `Olmo3ForCausalLM` (Transformers) | L40S / L40S |
| `allenai/Olmo-3-1125-32B` | 2025-11-04 | 32.23B (64.5 GB) | Same, 100B tokens | 90.4/86.2/79.7 | Apache, open | Open; Dec 2024 | Same | 80 GB (L40S in FP8) / 80 GB |
| `google/gemma-3-27b-pt` | 2025-03-01 | 27.43B (54.9 GB) | 131,072; 32K pretrain, RoPE x8 on global layers, 5 local (1,024) per global | 85.4/87.1/84.6; 72.9 at 128K ([report](https://arxiv.org/abs/2503.19786)) | Gemma, gated | Closed; unstated | `Gemma3ForConditionalGeneration` | 80 GB / 80 GB |
| `google/gemma-4-31B` | 2026-03-12 | 31.27B (62.5 GB) | 262,144; proportional RoPE on 10 of 60 layers; recipe unpublished | None (instruct 96.4 at 128K, [report](https://arxiv.org/abs/2607.02770)) | Apache, open | Closed; Jan 2025 | `Gemma4ForConditionalGeneration` | 80 GB / 80 GB |
| `meta-llama/Llama-3.1-8B` | 2024-07-14 | 8.03B (16.1 GB) | 131,072; six stages from 8K, about 800B tokens ([paper](https://arxiv.org/abs/2407.21783)) | 93.1/91.4/86.9 | Llama 3.1, gated | Closed; Dec 2023 | `LlamaForCausalLM` | L40S / L40S |
| `meta-llama/Llama-3.1-70B` | 2024-07-14 | 70.55B (141 GB) | Same | Not checked | Llama 3.1, gated | Closed; Dec 2023 | `LlamaForCausalLM` | 4-bit on 80 GB / 80 GB, Unsloth only |
| `mistralai/Mistral-Small-24B-Base-2501` | 2025-01-23 | 23.57B (47.1 GB) | 32,768 | None | Apache, open | Closed; unstated | `MistralForCausalLM` | 80 GB / L40S |
| `mistralai/Mistral-Small-3.1-24B-Base-2503` | 2025-03-16 | 24.01B (48.0 GB) | 131,072; theta 1e9 | 93.8/92.4/88.8 | Apache, open | Closed; unstated | `Mistral3ForConditionalGeneration` | 80 GB / L40S |
| `mistralai/Ministral-3-14B-Base-2512` | 2025-10-31 | 13.95B (27.9 GB) | 262,144; distilled from Mistral Small 3.1, YaRN x16 from 16,384 ([paper](https://arxiv.org/abs/2601.08584)) | None | Apache, open | Closed; unstated | `Mistral3ForConditionalGeneration` | L40S / L40S |
| `Qwen/Qwen3.5-9B-Base` | 2026-02-26 | 9.65B (19.3 GB) | 262,144 native; 24 Gated DeltaNet plus 8 attention layers | None | Apache, open | Closed; unstated | `Qwen3_5ForConditionalGeneration` | L40S / L40S |
| `swiss-ai/Apertus-v1.5-8B-base` | 2026-09-23 | 8.84B (17.7 GB) | 262,144; unstated | 81.3/76.1/67.5 at 64K (card) | Apache, gated | Public sources; unstated | None; swiss-ai fork | L40S / L40S |

Also checked (V): no Olmo 3.1-or-later or Mistral Small 3.2 base; Qwen3.5 bases only at 0.8B to 9B and 35B-A3B, none for 3.6 or 3.8; Marin 8B and 32B have 4,096 context; SmolLM3 is 3B (65,536); Nemotron 3 Nano Base is a Mamba hybrid with partly open data; `IFM/K2-V2` is 70B with fully open data.

Other findings:
- U: KV per 16K sequence is about 8.6 GB for Olmo 3 7B (32 KV heads), 4.3 GB for Olmo 3 32B, 2.1 GB for Llama 8B; Olmo 3 32B in bf16 on 80 GB serves 1 to 3 at once.
- V ([7B card](https://huggingface.co/allenai/Olmo-3-1025-7B)): Olmo 3 mid-training is 8% thinking and 6% instruction data, so the base has seen assistant prose. Dolma 3 rows carry `cc_dump`, so the post-ChatGPT share is measurable.
- V ([config code](https://github.com/huggingface/transformers/blob/main/src/transformers/models/olmo3/configuration_olmo3.py)): Transformers applies Olmo 3's YaRN to full-attention layers only, as trained.
- U: 6,000 tokens of notes plus 6,000 of output need 12K; 8K training truncates the longest pairs.

### 2. Contamination checking

- infini-gram (V, [docs](https://infini-gram.readthedocs.io/en/latest/api.html)): POST `https://api.infini-gram.io/`; indexes include `v4_olmo-mix-1124_llama` (OLMo 2 pretraining, 4.58T tokens), DCLM-baseline, Dolma v1.7, Pile, C4. No Dolma 3 or FineWeb; no stated rate limit.
- infini-gram mini (V, [docs](https://infini-gram-mini.readthedocs.io/en/latest/api.html)): `https://api.infini-gram-mini.io/`; seven 2025 Common Crawl snapshots, DCLM, Pile.
- OLMoTrace (V): Playground only, no documented API; its backend ([index_mappings.py](https://github.com/allenai/infinigram-api/blob/main/packages/infini-gram-processor/src/infini_gram_processor/index_mappings.py)) has an active `olmo-3-0625-32b-instruct` index. Whether that equals the released mixes: U.
- WIMBD (V, [repo](https://github.com/allenai/wimbd)): Dolma v1.7 and Tulu 2 only.
- Dolma 3 (V): `allenai/dolma3_mix-6T` (4.41 TB, ODC-By, ungated) plus Dolmino and Longmino: an exact check streams them against n-gram shingles of our posts.
- FineWeb: no public exact-match index found (U).

### 3. vLLM faithfulness hooks

- V ([PyPI](https://pypi.org/project/vllm/#history)): current release 0.33.0 (2026-11-02); 0.32.0 is from 2026-10-18. Model Runner V2 has been the default for dense models since 0.25.0 ([notes](https://github.com/vllm-project/vllm/releases/tag/v0.25.0)).
- V ([docs at v0.32.0](https://docs.vllm.ai/en/v0.32.0/features/custom_logitsprocs.html)): subclass `vllm.v1.worker.gpu.sample.logits_processor.LogitsProcessor`. Methods: `__init__(vllm_config, req_states)`, `add_request(req_idx, sampling_params) -> bool`, optional `apply_staged_writes()` and `validate_params`, `apply(logits, ctx)`. Per-request state arrives in `SamplingParams.extra_args` (server: `vllm_xargs`; docs show only numbers, so send lists as JSON strings, U). Register via `LLM(logits_processors=[...])`, `--logits-processors module:Class` or the `vllm.logits_processors` entry point; fixed at load. The legacy `BatchUpdate` interface needs `VLLM_USE_V2_MODEL_RUNNER=0`.
- V ([SamplingParams](https://docs.vllm.ai/en/latest/api/vllm/sampling_params/)): `bad_words` takes multi-token entries but bans only the completing token, as a deny list; `allowed_token_ids` is one static whitelist. Neither expresses "not in this input." Structured outputs take regex or EBNF (extended Backus-Naur form) grammars ([docs](https://docs.vllm.ai/en/latest/features/structured_outputs.html), V); a grammar would also need sentence-initial capitals (U).

```python
import json, torch
from transformers import AutoTokenizer
from vllm.v1.worker.gpu.sample.logits_processor import LogitsProcessor

class NewEntityGuard(LogitsProcessor):
    """Ban word-initial capitals and digits unless they start a word in guard_allowed."""
    def __init__(self, vllm_config, req_states):
        self.tok = AutoTokenizer.from_pretrained(vllm_config.model_config.tokenizer)
        V, n, dev = req_states.vocab_size, req_states.max_num_reqs, req_states.device
        risky = torch.zeros(V, dtype=torch.bool)
        for i in range(min(V, len(self.tok))):
            s = self.tok.decode([i]); t = s.lstrip()
            risky[i] = bool(t) and (t[0].isdigit() or (t[0].isupper() and s != t))
        self.risky = risky.to(dev)
        self.allow = torch.zeros(n, V, dtype=torch.bool); self.allow_dev = self.allow.to(dev)
        self.dirty = []

    def add_request(self, req_idx, sp):
        raw = (sp.extra_args or {}).get("guard_allowed")
        words = json.loads(raw) if isinstance(raw, str) else raw
        self.allow[req_idx] = words is None  # None: allow all
        for w in words or []:
            for v in (w, " " + w):
                ids = self.tok.encode(v, add_special_tokens=False)
                if ids: self.allow[req_idx, ids[0]] = True
        self.dirty.append(req_idx)
        return words is not None

    def apply_staged_writes(self):
        for i in self.dirty: self.allow_dev[i].copy_(self.allow[i])
        self.dirty.clear()

    def apply(self, logits, ctx):
        ban = self.risky & ~self.allow_dev[ctx.expanded_idx_mapping.long()]
        return logits.masked_fill(ban, float("-inf"))
```

Limits (U): `guard_allowed` must include sentence starters. Only word starts are policed: an allowed " Mar" can continue into "Martin", and capitals right after a quote slip through. Fixing both needs the previous token (`req_states.all_token_ids`, layout undocumented) and a per-request prefix tree.

### 4. Long-context fine-tuning on one GPU

- Unsloth, vendor-measured (V, [benchmarks](https://unsloth.ai/docs/basics/unsloth-benchmarks)): Llama 3.1 8B QLoRA, rank 32, batch 1, maximum context 191,728 on 48 GB versus 15,502 for Hugging Face with FlashAttention-2; Llama 3.3 70B 89,389 versus 6,916 on 80 GB.
- Unsloth short-context floor (V, [requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements)): 7B 5 GB, 14B 8.5, 27B 22, 32B 26, 70B 41. Gemma 4 31B "works with 22GB", context unstated ([guide](https://unsloth.ai/docs/models/gemma-4/train)). Olmo 3 is absent from Unsloth's model list.
- TRL (V, [guide](https://huggingface.co/docs/trl/main/en/reducing_memory_usage)): checkpointing on by default, packing, padding-free batching, activation offloading. Axolotl's Cut Cross-Entropy plugin covers olmo3, gemma4, qwen3_5, mistral3, llama (V, [docs](https://docs.axolotl.ai/docs/custom_integrations.html)); 262K-token vocabularies need it (fp32 logits about 8.6 GB at 8K, U).
- U: Olmo 3 32B QLoRA at 8K needs about 26 GB weights, 5.4 GB checkpointed activations, 3 to 7 GB logits: tight on L40S, easy on 80 GB; 16K doubles activations.

### What I could not verify

- Independent memory or throughput figures for 7B to 32B QLoRA at 8K to 16K.
- Base RULER for Gemma 4, Qwen3.5, Ministral 3, Mistral Small 2501 and Llama 3.1 70B; data cutoffs for Gemma 3, Mistral and Qwen3.5.
- Whether vLLM's Transformers backend saves sliding-window KV for Olmo 3; whether the sketch runs (not executed).
- OLMoTrace index coverage of Dolma 3; infini-gram rate limits.
