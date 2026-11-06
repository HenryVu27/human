"""B31: do newer base models read as AI to Pangram, and is it the crawl date or deliberate synthetic data?

Question. B1 found three OLMo-2-13B base continuations read Human and one Qwen3.5-9B-Base continuation read
AI. Does a base model's Pangram signal track (H1) the date of its web crawl, which holds more AI text the
later it is, (H2) synthetic or instruction-like data added on purpose in pretraining or mid-training, or
(H0) neither (a family quirk, model size, decoding or noise)? Design, predictions and the literature
behind them: docs/specs/2026-11-05-b31-base-model-dating.md. Claims ledger: results/research/b31-claims.md.

Fixed before any B31 text is generated for scanning (a 4-sample smoke test on Pythia-2.8B excepted) and
committed before any scan: first as 7fad7fe (2026-11-05 23:51 CST) on branch b31-basedate in a worktree, then
copied to master at 23:59 when the main session asked B31 to share its checkout. Amendments carry their time.
Amended 23:58 (technical, no design change): Olmo 3's three 2T ablation checkpoints label their config
"olmo2-retrofit", a name vLLM does not know; their 355 tensors, names and parameter count match
Olmo3ForCausalLM, so the copy on the Modal Volume is relabelled (model_type olmo3, sliding window 4096 for
4097, which no B31 sequence reaches) and the original kept as config.orig.json.
Amended 2026-11-06 00:05, before any upload: Henry granted gated access, so two priority-2 arms are added,
generated and filtered by the same rules and shuffled into the same batches: gemma3-12b
(google/gemma-3-12b-pt, cutoff August 2024, pretrained by distillation from a teacher model) and
llama3.1-8b (meta-llama/Llama-3.1-8B, data to the end of 2023, no synthetic text stated in pretraining),
the latter only if Meta approves access before the first upload. Weights fetched by
experiments/modal/b31_gated.py with Henry's read token (a Modal secret B31 never reads).
Amended 2026-11-06 00:20 (date read at commit), after batches 0 to 2 were scanned and before any result was matched to an arm:
Meta approved Llama access after the first upload, so llama3.1-8b missed the shuffled batches. It is
generated and filtered by the same rules and scanned afterwards in its own batch, reported as an extension
(labelled so, with the caveat that it was scanned in a separate batch); it enters no primary contrast.

Stimuli (30 openings, the same for every arm).
- FineWeb: data/human.jsonl rows 600 to 619 (h0600 to h0619, the first 20 dev documents; Common Crawl
  CC-MAIN-2020-50, so written before ChatGPT). These are B1's documents, so B1's 4-bit generations can
  be scored on the same openings.
- Essays: 10 essays from data/essays.jsonl, published before 2022-11-30, 800 or more words, quoted share
  at most 0.05, one per author: sort the eligible essays by sha256("b31" + id) and take an essay when its
  author is not yet taken, until 10.
- Opening: the first 120 whitespace words, joined by single spaces (B1's rule). Only the continuation is
  scored.

Arms. Every base model gets the opening as plain text (no chat template, the tokenizer's own special
tokens), bf16 weights, vLLM on Modal, temperature 0.8, top-p 0.95, no repetition penalty, at most 512 new
tokens, three samples per opening with seeds 1000 * try + document index (try 0, 1, 2). The models, their
roles and their training-data metadata (with sources in the claims ledger) are in MODELS below.
- Instruct controls: B1's chat prompt ("Continue the following text. Output only the continuation." then
  the opening), same sampling, scanned on 15 openings only (stimulus indexes 0 to 9 and 20 to 24).
  Amended 2026-11-05 23:57, before any scan: B1's prompt gave Qwen3.5-9B a median of 114 words and 11 of 15
  openings failed "short", so both instruct arms are regenerated with "Continue the following text for
  about 400 words. Output only the continuation." The first samples are kept in results/b31_raw_superseded/.
- human: the true continuation (words 121 onward), Pangram's false-positive rate on these documents.
- qwen3.5-9b-q4 and olmo2-13b-q4: B1's own 4-bit MLX continuations (results/b1_generations.jsonl;
  temperature 0.8, top-p 0.95, repetition penalty 1.05 over the last 20 tokens, seed 0) for h0600 to
  h0619. One sample each, so a failed filter is an exclusion, not a retry.

Text rule. Strip the text. If it has 250 or more words, cut at the last sentence end (., ! or ?,
optionally followed by a closing quote or bracket) that falls between words 150 and 250, else at word 250.

Filters, in this order, the first failure is the reason counted:
1. short: under 150 words.
2. nonprose: under 80% of whitespace tokens contain a letter.
3. nonenglish: under 90% of letters are ASCII letters.
4. repetitive: more than 25% of word 4-gram occurrences repeat an earlier 4-gram, or a line of 5 or more
   words occurs 3 or more times.
5. recall or copy: more than 10% of the text's word 8-grams (lowercase, letters and digits only) occur in
   the source document; counted as "recall" if more than 10% occur in the true continuation, else "copy"
   (the model repeats its own opening).
Selection: for each model and opening, the first try (0, 1, 2) that passes is the text; if none passes,
the opening is excluded for that model and every failed try is counted by reason. The 4-bit arms go
through all five filters; the human arm through filters 1 to 3 (its text is the source).

Scanning. Before any upload, the projected cost is the sum over texts of ceil(words / 100). Priority 1 and 2
arms are scanned; priority 3 arms are added only if the projected total stays at or under 2,100 credits
(B31's budget is 2,500; the rest is kept for an optional crawl measurement). Each text becomes a .docx
(textutil) named by 8 random hex characters; results/b31_blind.json keeps the key. All texts are
uploaded in one seeded random order (seed "b31"), 100 per batch, so no batch holds one model. Pangram's
document label (Human, Mixed, AI) and AI share are recorded per text; nothing is rescanned unless the
dashboard errors on a file.

Analysis (results/b31_summary.json, numbers only).
- Per arm: labels, share not Human with a Clopper-Pearson 95% interval, mean AI share with a bootstrap
  interval over openings, by genre.
- Validity gates: human reads Human on 85% or more of texts; each instruct arm reads not Human on 70% or
  more. If a gate fails, base-model rates are read only relative to the human arm and the report says so.
- Primary contrasts, paired by opening (openings kept in both arms). Test: sign-flip permutation test on
  the paired difference in AI share, Holm-corrected across the two; exact McNemar on not Human reported
  beside it. A contrast supports its hypothesis if the corrected p is under 0.05 and the later arm is
  higher by at least 0.15 in mean AI share or 15 points in share not Human.
  P1 (H2, mid-training): olmo3-7b-s1 (end of pretraining) against olmo3-7b-s2 (end of mid-training).
  P2 (H1, crawl date, pretraining only): olmo2-7b-s1 (Common Crawl through 2022) against olmo3-7b-s1
  (through CC-MAIN-2024-51).
  Extension fixed now: if a primary contrast's corrected p falls between 0.05 and 0.20, a second sample
  per opening (the next passing try) is scanned for its two arms and the test is rerun on the mean of the
  two samples per opening, reported as an extension with that label.
- Secondary contrasts (uncorrected, reported as such): SECONDARY below. The key one for the mechanism of
  H2 is olmo3-7b-mct against olmo3-7b-genqa (same 2T start, 100B tokens each, synthetic math, code and
  thinking traces against synthetic QA and instruction data).
- Descriptive model-level logistic regression of not Human on crawl end year, LLM-generated text and
  instruction data in pretraining or mid-training, log parameter count and family.

Predictions (written before any B31 text exists).
- H1 (crawl date): P2 positive (olmo3-7b-s1 above olmo2-7b-s1 and pythia-6.9b); P1 small; the 2T ablation
  arms close to each other; mistral-small-24b (2025, no synthetic data claimed) above mistral-7b; phi-2
  close to pythia-2.8b.
- H2 (deliberate synthetic or instruction data): P2 null (pretraining-only checkpoints close to the human
  arm whatever their crawl date); P1 positive; olmo3-7b-genqa or olmo3-7b-mct above olmo3-7b-2T; olmo2-7b
  above olmo2-7b-s1; phi-2 above pythia-2.8b; mistral-small-24b low; Qwen and Nemotron high.
- H0: no contrast passes, and base arms sit near the human arm or differ in ways that follow neither crawl
  date nor training data (size, family).
- Refutations: H1 at the 2024 level of web pollution is refuted if P2's interval excludes a 0.15 rise and
  olmo3-7b-s1 is within 0.10 of olmo2-7b-s1; H2 for Olmo 3 mid-training is refuted the same way by P1.
  B31 cannot test H1 for crawls after 2024 cleanly: every base model with a 2025 or 2026 crawl here also
  has deliberate synthetic data or no documentation.
- Known confound: a mid-training stage also anneals the learning rate, which sharpens the distribution
  whatever the data. The 2T ablation arms all anneal; a difference between them is data, not annealing.
"""

import argparse
import hashlib
import json
import math
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path.home() / "personal" / "human" / "data"  # read only; data/ is not in a worktree
RES = ROOT / "results"
STIM = RES / "b31_stimuli.jsonl"
RAW = RES / "b31_raw"
TEXTS = RES / "b31_texts.jsonl"
EXCL = RES / "b31_exclusions.json"
BLIND = RES / "b31_blind.json"
PANGRAM = RES / "b31_pangram.jsonl"
SUMMARY = RES / "b31_summary.json"
MODAL = Path.home() / ".local" / "bin" / "modal"

OPEN_WORDS, MIN_WORDS, MAX_WORDS, TRIES = 120, 150, 250, 3
PARAMS = {"temperature": 0.8, "top_p": 0.95, "max_tokens": 512, "max_model_len": 2048}

# Training-data metadata from primary sources; evidence and status per fact in results/research/b31-claims.md.
# crawl: last Common Crawl snapshot (or year) in the data this checkpoint has seen, None if undocumented.
# llm: LLM-generated text seen ("none", "mid": mid-training or annealing only, "pre": in pretraining, None:
# undocumented). instr: instruction, QA or chat-format data seen, same codes. priority: 1 primary, 2 secondary,
# 3 scanned only if credits allow (see the docstring).
A2 = dict(family="olmo", params_b=7.3)
CHAT_400 = "Continue the following text for about 400 words. Output only the continuation.\n\n"
MODELS = {
    # Pythia: the Pile, sources to about September 2020, no LLM text, no instruction data.
    "pythia-6.9b": dict(repo="EleutherAI/pythia-6.9b", revision="main", family="pythia", params_b=6.9,
                        release="2023-02", crawl="2020", llm="none", instr="none", priority=1),
    "pythia-2.8b": dict(repo="EleutherAI/pythia-2.8b", revision="main", family="pythia", params_b=2.8,
                        release="2023-02", crawl="2020", llm="none", instr="none", priority=2),
    # OLMo 1 (0724): Dolma 1.7, Common Crawl to CC-MAIN-2023-06 (February 2023), FLAN about 1% and in the anneal.
    "olmo1-7b": dict(repo="allenai/OLMo-7B-0724-hf", revision="main", family="olmo", params_b=6.9,
                     release="2024-07", crawl="2023-06", llm="none", instr="pre", priority=3),
    # OLMo 2: stage 1 is DCLM-Baseline (Common Crawl through 2022), no LLM text, no instruction data. Stage 2
    # (Dolmino, 50B for 7B, 100B and 300B soups for 13B): FLAN 11 to 17%, synthetic math 11 to 21%.
    "olmo2-7b-s1": dict(repo="allenai/OLMo-2-1124-7B", revision="stage1-step928646-tokens3896B", **A2,
                        release="2024-11", crawl="2022", llm="none", instr="none", priority=1),
    "olmo2-7b": dict(repo="allenai/OLMo-2-1124-7B", revision="main", **A2,
                     release="2024-11", crawl="2022", llm="mid", instr="mid", priority=1),
    "olmo2-13b": dict(repo="allenai/OLMo-2-1124-13B", revision="main", family="olmo", params_b=13.7,
                      release="2024-11", crawl="2022", llm="mid", instr="mid", priority=1),
    # Olmo 3 7B: stage 1 is Dolma 3 Mix (Common Crawl to CC-MAIN-2024-51; no LLM-generated source, 13.6% PDFs
    # transcribed by olmOCR). Stage 2 (Dolmino, 100B: 20% code, 28% web, 19% math, 14% QA, 8% thinking, 6%
    # instruction, 5% PDFs; about half LLM-generated; web crawl to June 2025). Stage 3 (Longmino, 50B) = main.
    "olmo3-7b-s1": dict(repo="allenai/Olmo-3-1025-7B", revision="stage1-step1413814", **A2,
                        release="2025-11", crawl="2024-51", llm="none", instr="none", priority=1),
    "olmo3-7b-s2": dict(repo="allenai/Olmo-3-1025-7B", revision="stage2-step47684", **A2,
                        release="2025-11", crawl="2025-06", llm="mid", instr="mid", priority=1),
    "olmo3-7b": dict(repo="allenai/Olmo-3-1025-7B", revision="main", **A2,  # same weights as stage3-step11921
                     release="2025-11", crawl="2025-06", llm="mid", instr="mid", priority=1),
    # Olmo 3 Table 7 ablations: 100B mid-training tokens each from the 2T stage-1 checkpoint (step 476838).
    "olmo3-7b-2t": dict(repo="allenai/Olmo-3-1025-7B", revision="stage1-step476838", **A2,
                        release="2025-11", crawl="2024-51", llm="none", instr="none", priority=2),
    "olmo3-7b-genqa": dict(repo="allenai/Olmo-3-1025-7B", revision="stage2-step47684-mix-gen-mc-only-from-2T-ckpt",
                           **A2, release="2025-11", crawl="2025-06", llm="mid", instr="mid", priority=2),
    "olmo3-7b-mct": dict(repo="allenai/Olmo-3-1025-7B",
                         revision="stage2-step47684-mix-math-code-reasoning-web-from-2T-ckpt", **A2,
                         release="2025-11", crawl="2025-06", llm="mid", instr="none", priority=2),
    "olmo3-7b-r5": dict(repo="allenai/Olmo-3-1025-7B", revision="stage2-step47684-mix-round5-from-2T-ckpt", **A2,
                        release="2025-11", crawl="2025-06", llm="mid", instr="mid", priority=2),
    # Phi-2: GPT-3.5 synthetic textbooks (250B-token set) plus filtered RefinedWeb and SlimPajama.
    "phi-2": dict(repo="microsoft/phi-2", revision="main", family="phi", params_b=2.8,
                  release="2023-12", crawl="2023", llm="pre", instr=None, priority=2),
    # Nemotron Nano 2: Common Crawl to CC-MAIN-2025-13, 33% of 10.6T unique tokens synthetic, SFT-style data.
    "nemotron-9b": dict(repo="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Base", revision="main", family="nemotron",
                        params_b=8.9, release="2025-08", crawl="2025-13", llm="pre", instr="pre", priority=2,
                        trust_remote_code=True),
    # Mistral: no data documentation, except Small 3 (2025): "neither trained with RL nor synthetic data".
    "mistral-small-24b": dict(repo="mistralai/Mistral-Small-24B-Base-2501", revision="main", family="mistral",
                              params_b=23.6, release="2025-01", crawl=None, llm="none", instr=None, priority=2,
                              gpu="A100-80GB"),
    "mistral-7b": dict(repo="mistralai/Mistral-7B-v0.1", revision="main", family="mistral", params_b=7.2,
                       release="2023-09", crawl=None, llm=None, instr=None, priority=3),
    "mistral-nemo-12b": dict(repo="mistralai/Mistral-Nemo-Base-2407", revision="main", family="mistral",
                             params_b=12.2, release="2024-07", crawl=None, llm=None, instr=None, priority=3),
    # Qwen: instruction data in pretraining stated from Qwen-7B (2023) on; Qwen-made synthetic data from Qwen2 on;
    # Qwen3 "trillions" of synthetic tokens including QA and instructions; Qwen3.5 has no data report.
    "qwen1.5-7b": dict(repo="Qwen/Qwen1.5-7B", revision="main", family="qwen", params_b=7.7,
                       release="2024-02", crawl=None, llm=None, instr="pre", priority=3),
    "qwen2-7b": dict(repo="Qwen/Qwen2-7B", revision="main", family="qwen", params_b=7.6,
                     release="2024-06", crawl=None, llm="pre", instr="pre", priority=3),
    "qwen2.5-7b": dict(repo="Qwen/Qwen2.5-7B", revision="main", family="qwen", params_b=7.6,
                       release="2024-09", crawl=None, llm="pre", instr=None, priority=2),
    "qwen3-8b": dict(repo="Qwen/Qwen3-8B-Base", revision="main", family="qwen", params_b=8.2,
                     release="2025-04", crawl=None, llm="pre", instr="pre", priority=2),
    "qwen3.5-9b": dict(repo="Qwen/Qwen3.5-9B-Base", revision="main", family="qwen", params_b=9.7,
                       release="2026-02", crawl=None, llm=None, instr=None, priority=1, multimodal=True),
    # Gated, added 00:05. Llama 3: data "until the end of 2023", no synthetic text in the pretraining section.
    # Gemma 3: cutoff August 2024, pretrained with knowledge distillation from a teacher's logits.
    "llama3.1-8b": dict(repo="meta-llama/Llama-3.1-8B", revision="main", family="llama", params_b=8.0,
                        release="2024-07", crawl="2023", llm="none", instr=None, priority=2),
    "gemma3-12b": dict(repo="google/gemma-3-12b-pt", revision="main", family="gemma", params_b=12.2,
                       release="2025-03", crawl="2024", llm="distill", instr=None, priority=2, multimodal=True),
    # Instruct positive controls (chat template, B1's prompt, 15 openings).
    "olmo2-13b-instruct": dict(repo="allenai/OLMo-2-1124-13B-Instruct", revision="main", family="olmo",
                               params_b=13.7, release="2024-12", chat=True, priority=1,
                               chat_instruction=CHAT_400),
    "qwen3.5-9b-instruct": dict(repo="Qwen/Qwen3.5-9B", revision="main", family="qwen", params_b=9.7,
                                release="2026-02", chat=True, multimodal=True, priority=1,
                                chat_template_kwargs={"enable_thinking": False}, chat_instruction=CHAT_400),
}
CHAT_DOCS = list(range(10)) + list(range(20, 25))  # stimulus indexes the instruct arms are scanned on
LOCAL_ARMS = {"human": 1, "qwen3.5-9b-q4": 1, "olmo2-13b-q4": 1}  # arm: priority
PRIMARY = [("P1", "olmo3-7b-s1", "olmo3-7b-s2"), ("P2", "olmo2-7b-s1", "olmo3-7b-s1")]
SECONDARY = [("olmo3-7b-mct", "olmo3-7b-genqa"), ("olmo3-7b-2t", "olmo3-7b-genqa"), ("olmo3-7b-2t", "olmo3-7b-mct"),
             ("olmo3-7b-2t", "olmo3-7b-r5"), ("olmo3-7b-2t", "olmo3-7b-s1"), ("olmo3-7b-s2", "olmo3-7b"),
             ("olmo2-7b-s1", "olmo2-7b"), ("pythia-6.9b", "olmo2-7b-s1"), ("pythia-6.9b", "olmo3-7b-s1"),
             ("pythia-2.8b", "phi-2"), ("olmo3-7b-s1", "nemotron-9b"), ("mistral-7b", "mistral-small-24b"),
             ("olmo2-7b", "olmo3-7b"), ("olmo2-13b-q4", "olmo2-13b"), ("qwen3.5-9b-q4", "qwen3.5-9b"),
             ("olmo2-13b", "qwen3.5-9b"), ("qwen2.5-7b", "qwen3-8b"), ("qwen3-8b", "qwen3.5-9b"),
             ("human", "olmo2-13b"), ("olmo2-13b", "olmo2-13b-instruct"), ("qwen3.5-9b", "qwen3.5-9b-instruct")]


def words(text: str) -> list[str]:
    return text.split()


# ---------------------------------------------------------------- stimuli

def stimuli():
    fine = [json.loads(line) for line in (DATA / "human.jsonl").open()][600:620]
    essays = [json.loads(line) for line in (DATA / "essays.jsonl").open()]
    eligible = [e for e in essays if e["date"] < "2022-11-30" and int(e["words"]) >= 800 and float(e["quoted"]) <= 0.05]
    eligible.sort(key=lambda e: hashlib.sha256(("b31" + e["id"]).encode()).hexdigest())
    taken, picked = set(), []
    for e in eligible:
        if e["author"] not in taken:
            taken.add(e["author"])
            picked.append(e)
        if len(picked) == 10:
            break
    rows = []
    for i, d in enumerate([(r["id"], "fineweb", r["text"], r["dump"]) for r in fine]
                          + [(e["id"], "essay", e["text"], e["date"]) for e in picked]):
        doc, genre, text, date = d
        w = words(text)
        rows.append({"doc": doc, "index": i, "genre": genre, "date": date, "opening": " ".join(w[:OPEN_WORDS]),
                     "remainder": " ".join(w[OPEN_WORDS:]), "source": text})
    STIM.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(Counter(r["genre"] for r in rows), "authors:", sorted(e["author"] for e in picked))


def load_stimuli() -> list[dict]:
    return [json.loads(line) for line in STIM.open()]


# ---------------------------------------------------------------- Modal jobs

def jobs(keys: list[str], out: Path):
    stim = load_stimuli()
    specs = []
    for k in keys:
        m = MODELS[k]
        spec = {"key": k, **{f: m[f] for f in ("repo", "revision")}, "gpu": m.get("gpu", "L40S")}
        spec |= {f: m[f] for f in ("trust_remote_code", "multimodal", "chat", "chat_template_kwargs", "chat_instruction")
                 if f in m}
        prompts = [{"doc": s["doc"], "try": t, "seed": 1000 * t + s["index"], "opening": s["opening"]}
                   for t in range(TRIES) for s in stim]
        specs.append({"spec": spec, "prompts": prompts, "params": PARAMS})
    out.write_text(json.dumps(specs))
    fetch = [{"repo": MODELS[k]["repo"], "revision": MODELS[k]["revision"]} for k in keys]
    out.with_name(out.stem + "_fetch.json").write_text(json.dumps(fetch))
    print(f"{len(specs)} jobs, {sum(len(s['prompts']) for s in specs)} prompts -> {out}")


# ---------------------------------------------------------------- filters and selection

SENT_END = re.compile(r"[.!?][\"'”’)\]]*$")


def cut(text: str) -> str:
    w = words(text.strip())
    if len(w) < MAX_WORDS:
        return text.strip()
    ends = [i for i in range(MIN_WORDS - 1, MAX_WORDS) if SENT_END.search(w[i])]
    n = ends[-1] + 1 if ends else MAX_WORDS
    # keep the original line breaks of the kept part
    kept, count = [], 0
    for line in text.strip().split("\n"):
        lw = line.split()
        if count + len(lw) <= n:
            kept.append(line)
            count += len(lw)
        else:
            kept.append(" ".join(lw[: n - count]))
            break
    return "\n".join(kept).strip()


def _grams(ws: list[str], n: int) -> list[tuple]:
    return [tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)]


def _norm(text: str) -> list[str]:
    return [t for t in (re.sub(r"[^a-z0-9]", "", w.lower()) for w in text.split()) if t]


def check(text: str, source: dict | None, upto: int = 5) -> str | None:
    w = words(text)
    if len(w) < MIN_WORDS:
        return "short"
    if sum(any(c.isalpha() for c in t) for t in w) / len(w) < 0.8:
        return "nonprose"
    letters = [c for c in text if c.isalpha()]
    if not letters or sum(c.isascii() for c in letters) / len(letters) < 0.9:
        return "nonenglish"
    if upto < 4:
        return None
    g4 = _grams([t.lower() for t in w], 4)
    if g4 and (len(g4) - len(set(g4))) / len(g4) > 0.25:
        return "repetitive"
    lines = Counter(ln.strip() for ln in text.split("\n") if len(ln.split()) >= 5)
    if lines and max(lines.values()) >= 3:
        return "repetitive"
    if source is not None:
        g8 = _grams(_norm(text), 8)
        src = set(_grams(_norm(source["opening"] + " " + source["remainder"]), 8))
        rem = set(_grams(_norm(source["remainder"]), 8))
        if g8 and sum(g in src for g in g8) / len(g8) > 0.10:
            return "recall" if sum(g in rem for g in g8) / len(g8) > 0.10 else "copy"
    return None


def select():
    stim = {s["doc"]: s for s in load_stimuli()}
    texts, excl = [], {}
    for path in sorted(RAW.glob("*.jsonl")):
        key = path.stem
        rows = [json.loads(line) for line in path.open()]
        by = {(r["doc"], r["try"]): r for r in rows}
        fails, kept = Counter(), 0
        docs = [d for d in stim if not MODELS[key].get("chat") or stim[d]["index"] in CHAT_DOCS]
        for doc in docs:
            for t in range(TRIES):
                r = by.get((doc, t))
                if r is None:
                    fails["missing"] += 1
                    continue
                text = cut(r["text"])
                why = check(text, stim[doc])
                if why:
                    fails[why] += 1
                    continue
                texts.append({"arm": key, "doc": doc, "genre": stim[doc]["genre"], "try": t, "text": text,
                              "words": len(words(text))})
                kept += 1
                break
        excl[key] = {"openings": len(docs), "kept": kept, "excluded": len(docs) - kept, "failed_tries": dict(fails)}
    # local arms
    for doc, s in stim.items():
        text = cut(s["remainder"])
        why = check(text, None, upto=3)
        if why:
            excl.setdefault("human", {"failed": Counter()})["failed"][why] += 1
        else:
            texts.append({"arm": "human", "doc": doc, "genre": s["genre"], "try": 0, "text": text, "words": len(words(text))})
    b1 = [json.loads(line) for line in (RES / "b1_generations.jsonl").open()]
    for model, arm in (("qwen", "qwen3.5-9b-q4"), ("olmo", "olmo2-13b-q4")):
        for r in b1:
            if r["model"] != model or r["source_id"] not in stim:
                continue
            text = cut(r["continuation"])
            why = check(text, stim[r["source_id"]])
            if why:
                excl.setdefault(arm, {"failed": Counter()})["failed"][why] += 1
            else:
                texts.append({"arm": arm, "doc": r["source_id"], "genre": "fineweb", "try": 0, "text": text,
                              "words": len(words(text))})
    TEXTS.write_text("".join(json.dumps(t) + "\n" for t in texts))
    EXCL.write_text(json.dumps(excl, indent=1, default=dict))
    per = Counter(t["arm"] for t in texts)
    print(json.dumps({k: per[k] for k in sorted(per)}, indent=1))
    print("texts", len(texts), "words", sum(t["words"] for t in texts))


# ---------------------------------------------------------------- blinding and upload files

def priority(arm: str) -> int:
    return MODELS[arm]["priority"] if arm in MODELS else LOCAL_ARMS[arm]


def cost(texts: list[dict]) -> int:
    return sum(math.ceil(t["words"] / 100) for t in texts)


def blind(outdir: Path):
    """Priority 1 and 2 arms always; priority 3 only if the projected total stays at or under 2,100 credits."""
    texts = [json.loads(line) for line in TEXTS.open()]
    core = [t for t in texts if priority(t["arm"]) <= 2]
    extra = [t for t in texts if priority(t["arm"]) == 3]
    print("projected credits: priority 1-2", cost(core), "priority 3", cost(extra))
    texts = core + extra if cost(core) + cost(extra) <= 2100 else core
    rng = random.Random("b31")
    rng.shuffle(texts)
    outdir.mkdir(parents=True, exist_ok=True)
    keymap, used = {}, set()
    for i, t in enumerate(texts):
        name = rng.randbytes(4).hex()
        while name in used:
            name = rng.randbytes(4).hex()
        used.add(name)
        batch = i // 100
        d = outdir / f"batch{batch:02d}"
        d.mkdir(exist_ok=True)
        (d / f"{name}.txt").write_text(t["text"] + "\n")
        subprocess.run(["textutil", "-convert", "docx", str(d / f"{name}.txt")], check=True)
        (d / f"{name}.txt").unlink()
        keymap[name] = {"arm": t["arm"], "doc": t["doc"], "batch": batch, "words": t["words"]}
    BLIND.write_text(json.dumps(keymap, indent=1))
    print(len(keymap), "files in", outdir, "batches", 1 + (len(keymap) - 1) // 100,
          "words", sum(v["words"] for v in keymap.values()))


# ---------------------------------------------------------------- Pangram results

def record(path: Path):
    """path: JSON lines {"name", "label", "ai_share", "batch"} transcribed from the dashboard."""
    keymap = json.loads(BLIND.read_text())
    rows = [json.loads(line) for line in path.open()]
    out = []
    for r in rows:
        k = keymap[r["name"]]
        out.append(k | r)
    PANGRAM.write_text("".join(json.dumps(r) + "\n" for r in out))
    print(len(out), "verdicts;", Counter(r["label"] for r in out))


# ---------------------------------------------------------------- analysis

def clopper_pearson(k: int, n: int, a: float = 0.05) -> tuple[float, float]:
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
    return round(float(lo), 3), round(float(hi), 3)


def mcnemar_exact(b: int, c: int) -> float:
    from scipy.stats import binomtest
    return 1.0 if b + c == 0 else float(binomtest(b, b + c, 0.5).pvalue)


def signflip(diffs: list[float], reps: int = 20000) -> float:
    rng = random.Random(31)
    obs = abs(sum(diffs))
    hits = sum(abs(sum(d if rng.random() < 0.5 else -d for d in diffs)) >= obs - 1e-12 for _ in range(reps))
    return (hits + 1) / (reps + 1)


def contrast(by: dict, a: str, b: str) -> dict:
    docs = sorted(set(by.get(a, {})) & set(by.get(b, {})))
    if not docs:
        return {"a": a, "b": b, "paired": 0}
    na = [by[a][d]["label"] != "Human" for d in docs]
    nb = [by[b][d]["label"] != "Human" for d in docs]
    up = sum((not x) and y for x, y in zip(na, nb))
    down = sum(x and (not y) for x, y in zip(na, nb))
    diffs = [by[b][d]["ai_share"] - by[a][d]["ai_share"] for d in docs]
    return {"a": a, "b": b, "paired": len(docs), "not_human_a": sum(na) / len(docs), "not_human_b": sum(nb) / len(docs),
            "diff_points": round(100 * (sum(nb) - sum(na)) / len(docs), 1), "b_only": up, "a_only": down,
            "p_mcnemar": round(mcnemar_exact(up, down), 4),
            "mean_ai_share_diff": round(sum(diffs) / len(diffs), 3), "p_signflip": round(signflip(diffs), 4)}


def analyze():
    rows = [json.loads(line) for line in PANGRAM.open()]
    by: dict[str, dict] = {}
    for r in rows:
        by.setdefault(r["arm"], {})[r["doc"]] = r
    arms = {}
    rng = random.Random(7)
    for arm, d in sorted(by.items()):
        n = len(d)
        labels = Counter(v["label"] for v in d.values())
        k = n - labels["Human"]
        shares = [v["ai_share"] for v in d.values()]
        boots = sorted(sum(rng.choice(shares) for _ in shares) / n for _ in range(5000))
        arms[arm] = {"n": n, "labels": dict(labels), "not_human": round(k / n, 3), "not_human_ci": clopper_pearson(k, n),
                     "mean_ai_share": round(sum(shares) / n, 3), "mean_ai_share_ci": (round(boots[124], 3), round(boots[4874], 3)),
                     "by_genre": {g: {"n": sum(v["genre"] == g for v in d.values()),
                                      "not_human": sum(v["genre"] == g and v["label"] != "Human" for v in d.values())}
                                  for g in ("fineweb", "essay")} if all("genre" in v for v in d.values()) else None}
    prim = [contrast(by, a, b) | {"name": n} for n, a, b in PRIMARY]
    ps = sorted(range(len(prim)), key=lambda i: prim[i].get("p_signflip", 1))
    running = 0.0
    for rank, i in enumerate(ps):  # Holm step-down on the sign-flip p-values
        running = max(running, min(1.0, prim[i].get("p_signflip", 1) * (len(prim) - rank)))
        prim[i]["p_holm"] = round(running, 4)
    for c in prim:
        big = c.get("mean_ai_share_diff", 0) >= 0.15 or c.get("diff_points", 0) >= 15
        c["supports"] = bool(c.get("p_holm", 1) < 0.05 and big)
    sec = [contrast(by, a, b) for a, b in SECONDARY]
    SUMMARY.write_text(json.dumps({"arms": arms, "primary": prim, "secondary": sec}, indent=1))
    for a, v in arms.items():
        print(f"{a:22s} n={v['n']:3d} not_human={v['not_human']:.2f} {v['not_human_ci']} ai_share={v['mean_ai_share']:.2f} {v['labels']}")
    for c in prim + sec:
        print(json.dumps(c))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["stimuli", "jobs", "select", "blind", "record", "analyze"])
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--out", default=str(RES / "b31_jobs.json"))
    ap.add_argument("--file")
    a = ap.parse_args()
    if a.step == "stimuli":
        stimuli()
    elif a.step == "jobs":
        jobs(a.models or list(MODELS), Path(a.out))
    elif a.step == "select":
        select()
    elif a.step == "blind":
        blind(Path(a.out))
    elif a.step == "record":
        record(Path(a.file))
    else:
        analyze()
