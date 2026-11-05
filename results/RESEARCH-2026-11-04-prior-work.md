# Prior work: what beats Pangram, 2026-11-04

Three research agents surveyed papers, open-source projects and posts on X (read only, with Henry's account). I checked two key claims against their primary pages: HALO (arXiv 2609.31876, Pangram v4, detection 77% to 24%) and phuryn/work-humanizer (Pangram 4, AI drafts 4% human, writer's own notes 4 of 4 human). Everything else is as the agents reported it and is not verified. Pangram 4.0 shipped 2026-07-29 with training on humanizer outputs, and 4.1 on 2026-10-19, so results measured on 3.x are stale.

## Bottom line

No one has publicly shown a fully AI-written draft passing Pangram 4.x with its facts kept. Every credible pass has one of two things:

- **Human-chosen content**: a base model continuing human text, or the writer's own notes as input.
- **Changed meaning**: invented facts, drift, or lower quality.

This is the same split B3 to B5 found.

## Evidence that bears on the split

| Source | Date | What it shows | Evidence |
|---|---|---|---|
| Pangram 4 technical report, 4.1 model card | 2026-07-29, 2026-10-19 | Trained on topic mirrors, hard negatives and humanizer outputs; DAMAGE (Pangram's humanizer study) treats humanization as something the detector should ignore. 97.7% recall on 12 commercial humanizers; 0.43% miss on blader rewrites | Vendor-run |
| HALO, Dhingra and Pruthi (arXiv 2609.31876) | 2026-09-25 | Agent plus OLMo-2-32B base continuation cuts Pangram v4 detection from 77% to 24% at up to 30 times the cost. Tasks grounded in a human document drop to 3% flagged; HealthBench, whose advice the AI structures itself, stays at 66% | Verified abstract; authors' own evaluation |
| Xu et al., "Base Models Look Human To AI Detectors" (arXiv 2605.19516), with HIP | 2026-05 | Llama-3-8B base output scores 98.8% human against 17.1% for the instruct model. Iterative base-model paraphrasing raises the human score but drifts meaning and invents facts by round 10 | Figures only; Pangram 3.x |
| PASTA, Anand et al. (arXiv 2605.30526) | 2026-05, v3 2026-10 | Ablating the instruct-minus-base activation direction during decoding cuts Pangram detection by 73 to 98 points on 7 of 11 models, from human prefixes only | Pangram version not given |
| phuryn/work-humanizer | 2026-10 | Prompt-only rewrites: 2 to 4% human. Emulate-1: 87% human but invents facts. Writer's own notes as input: 4 of 4 human | Verified page; small n |
| jialinyyzz/humanizer (Hugging Face), forum threads | 2026-10 | Fine-tuned AI-to-human rewriter; the owner and users report it fails Pangram on fully AI text and passes when the user supplies their own thoughts | Third-party reports |
| X: @PawelHuryn, @random_walker, @sayashk, Pangram CEO Max Spero | 2026-07 to 11 | Pangram "cares less about the words than about the reasoning structure"; agent loops lost their gradient against 4.x (scores above 0.99); "best way to pass pangram is with a base model and out-of-distribution context" | Posts, mostly no data |
| StealthRL, Adversarial Paraphrasing, MASH | 2025 to 2026 | RL or decoding against open detectors beats those detectors; no evidence of transfer to Pangram, and HIP reports StealthRL fails on it | Open detectors only |

## Agent rewrite loops

These are the approach Henry asked about.

- **Agents rewriting with Pangram or a detector as feedback have mostly failed on 4.x.** Scores sit near 1.0, so the loop gets no gradient (@random_walker; HALO reports the same when the agent had Pangram as a tool).
- **The partial successes start from a human-anchored seed and make small edits** (@sayashk, 2026-11-03, no data).
- **When it works on an easy prompt, the agent drifts into a meandering style or reward-hacks** with homoglyphs (@uzpg_).

## What this means for the humanizer

1. **Product route that works today:** the editor takes Henry's own notes (or the human-chosen points in a draft) and the fine-tuned writer turns them into prose. B3 group B and B5 cells D and E pass, as does work-humanizer's notes route.
2. **Research route:** change what an AI draft says, not how it says it. Cut generic padding (B6, running), or let a base model choose the points (HALO's route). This edits meaning, so the claim check still applies.
3. **Detector-proxy training** (RL or DPO against an open Pangram-like detector such as pangramlabs/EditLens) is untested against 4.x. The evidence so far suggests it fails without the content change.
