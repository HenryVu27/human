# Humanizer: design

Date: 2026-11-04. Status: draft for Henry's review.

## 1. Intent

Build a tool that takes any AI-written draft, with no human material behind it, and returns a piece that careful human readers and Pangram 4.x both judge to be human-written. The output must also be better writing than the input, not just different.

Why: Henry writes his blog (henryvu.blog) with Claude. After many rounds of rules, checks and skills, the posts still read as AI. Commercial humanizers make text worse and Pangram catches them anyway. The research below suggests the real cause of "AI-ness" sits somewhere no existing tool touches, so there is room for a real attempt.

Spending cap: $100 in total. The project should be cheap, and the cap is a design input, not a guess.

## 2. What the evidence says (the basis for the design)

1. **Rewording after the fact is a dead end against Pangram 4.** Pangram 4 is a large language model (LLM) fine-tuned on topic-matched pairs: a human text and a "synthetic mirror" written by a chat model on the same topic. It labels each clause by where its idea came from. Results from the Pangram 4 technical report:
   - It catches 98.8% of commercial humanizer output.
   - It misses only 0.43% of text rewritten by frontier models following the BLADER humanizer prompt.
   - A GPT-5.6 agent with 24 hours of API access found no systematic bypass.
2. **The signature comes mostly from post-training.** Post-training is the instruction tuning and preference tuning that turns a pretrained "base" model into a chat assistant. Evidence:
   - Base models match human grammatical profiles (Reinhart et al., PNAS 2025).
   - Llama-3-8B base continuations scored 98.8% human on Pangram, versus 17.1% for the instruct model (Xu et al. 2026).
   - GPT-4o fine-tuned on one author's complete works was flagged 3% of the time, versus 97% when prompted (Chakrabarty et al. 2025).
3. **Content choices carry signal that rewording keeps.** These survive rewording: covering every item equally, balanced hedging, safe examples, recap conclusions, and repeating the same move in every section. Expert readers caught 100% of humanized text by using exactly these cues (Russell et al., ACL 2025). Henry's context-engineering post shows them: seven components that each get a graded "personal" opener, and a "Lesson" box restated by the next paragraph.
4. **Pangram is catching up with base-model tricks.** HALO stitched together base-model samples, which cut Pangram 4's average AI score from 77% to 24% but at up to 30 times the cost. Pangram 3.3.2 flagged about 3% of HALO outputs, and Pangram 4 flags about 19%.
5. **Weight edits can remove an obstacle, not add an ability.** MIT CSAIL's weight-space programming work had GPT-6 Astra edit 0.016% of Qwen3.5-0.8B's weights to remove a looping direction. MATH-500 went from 7.9 to 48.1. The same approach did nothing for Gemma 3 270M, which had no looping to remove. If the assistant register is an obstacle on top of human-like ability from pretraining, it is the kind of thing such edits can remove.

The open gap, which no paper closes: a model that keeps instruct-level control and quality while writing with base-model statistics, for explanatory prose.

## 3. Goals, non-goals, anti-goals

Goals:
- A working tool: AI draft in, edited human-register piece out, plus a short report.
- Find out which writer approach (section 5.2) removes the post-training signature at acceptable quality, and report it with numbers, including negative results.

Non-goals:
- Humanizing text that has human source material behind it. That is a separate, easier problem (Henry speaks or writes notes, and the model only edits).
- Languages other than English. Fiction, poetry, chat replies, code comments.
- A product, a user interface, or hosting.

Anti-goals (failure even if Pangram says "Human"):
- Output that invents facts, numbers, names, dates, quotes or personal anecdotes to look human.
- Output that is worse than the input: typos, nonsense, meaning drift, or degraded fluency. This is the commercial-humanizer failure.
- Results that only hold because we tuned on Pangram's own scores (Goodhart's law).

## 4. Constraints

- **Total spend at most $100.** See section 7.
- **Hardware:** Henry's Mac (Apple M2 Pro, 16 GB RAM, about 115 GB free disk). It fits a 4B model at 16-bit precision or a 9B model at 4-bit. No local GPU beyond that.
- **Pangram stays a held-out judge.** It never sits inside a training or search loop, and no prompt, weight or setting is chosen by its scores on the held-out set.
- **No invented content.** Every factual element of the output must be supported by the input draft.
- **Accounts and money are Henry's to act on.** Henry buys the Pangram plan, creates the Pangram API key, and signs up for Tinker if used. Keys live in environment variables (`PANGRAM_API_KEY`, `TINKER_API_KEY`) in an untracked `.env`, never in code or logs.
- **Browser:** before using Claude in Chrome, verify it is the Chrome on this Mac (see the Mnemosyne inbox note of 2026-11-04).

## 5. Design

### 5.1 Pipeline

```
AI draft
  -> [1] Editor (frontier model): editing plan as notes, no prose
  -> [2] Writer (de-post-trained model): prose from the notes
  -> [3] Checks: claim check, quality judge, local detector
  -> output + report
```

**[1] Editor.** A frontier model (Claude Opus 5.5 by default) reads the draft as a pile of claims and decides like a human editor:
- what to cut (weak points, coverage for its own sake, recaps)
- what order serves the argument
- where to go deep on one example instead of skimming four
- where the piece should end

Its guidance is written as editorial judgment, not banned words. It outputs structured notes: kept claims (each tied to the sentence in the draft that supports it), order, emphasis and length per section. It writes no prose, so its own register does not leak into the output. Output length is not fixed, and 60 to 80% of the input is typical (my call).

**[2] Writer.** A model with the post-training signature removed or never added writes the prose from the notes. Section 5.2 lists the candidates. Which one ships is decided by the experiments.

**[3] Checks.** Run on every output:
- **Claim check.**
  - Deterministic part: every number, date, proper noun and quotation in the output must appear in the draft.
  - Model-judge part: every claim in the output must be entailed by the draft.
  - Pass bar: zero unsupported specifics, and at least 95% of claims entailed.
- **Quality judge.** A pairwise comparison of output against input by a frontier model, with positions swapped to cancel order bias. The question asked is which piece a busy expert reader would rather read. Pass bar: the output wins at least 50% across a test set.
- **Local detector.** See section 6.1.

A failed check sends the piece back to the writer with the failing spans, for at most two retries (my call). After that the tool returns the best attempt with the failure stated in the report.

**Interface (my call):** a command-line tool, `humanize draft.md -o out.md`, that also writes `out.report.json` (claims kept and dropped, check results, local detector score). A Claude Code skill wrapper comes later if the tool works.

### 5.2 Writer candidates, cheapest first, each with a stop rule

| ID | Writer | Where | Stop rule |
|---|---|---|---|
| B1 | Base model continues human-written openings (probe only, not a writer) | Qwen3.5-9B-Base on Tinker, or 4-bit on the Mac | If Pangram 4.x labels at least half of 10 base continuations as AI, the base-model route is dead on Pangram 4.x. Stop B2 and B3, and report it. |
| B0 | Instruct model with the assistant-register direction removed by weight edits | Qwen3.5-4B base and instruct pair, on the Mac | If neither the scripted baseline nor the agent-directed edit lowers the local detector score by a clear margin (builder sets the margin before running) while keeping the claim check and instruction following, stop. |
| B2 | Base model writes from the editor's notes, laid out as a natural document prefix (for example, earlier human posts followed by the notes and a heading) | Qwen3.5-9B-Base | If quality judge win rate is below 30% after prompt-format iteration on the dev set, stop. |
| B3 | Base model LoRA (low-rank adaptation) fine-tuned on human explanatory writing, then used as in B2 | Qwen3.5-9B-Base on Tinker, or the Mac if Tinker is unavailable | If it does not beat B2 on the local detector or quality, drop it. |

B0 detail. The MIT setup, rebuilt at small scale:
- Load both 4B models.
- Build human/AI paired texts on matched topics.
- Compute activation differences between the pairs, and find a low-rank direction that separates the assistant register from human writing.
- Project that direction out of selected weight matrices.

Run two arms. The scripted arm uses mean-difference ablation with no agent. In the agent arm, a Claude Code session plays Astra: it has a Python kernel, a budget of forward passes, and the local detector plus an instruction-following check as feedback. If the scripted arm matches the agent arm, the agent adds nothing, and we say so.

### 5.3 Data

- **Human corpus** (for the local detector and for B3):
  - English explanatory prose dated before 2022 (before ChatGPT): technical blog posts, essays, long-form explainers.
  - 1 to 5 million tokens, with licensing that permits research use.
  - Sources are the builder's choice within these limits.
- **Synthetic mirrors:** for each human text, a topic prompt answered by at least three model families (Claude, GPT, Gemini), following Pangram's mirroring recipe. These are the AI side for the local detector.
- **Test drafts:** frontier-model drafts of 500 to 2,000 words on topics drawn from held-out human texts. Split into a dev set (free to iterate on) and a frozen held-out set of 100 drafts whose topics do not overlap with dev. The held-out set is built once and never edited.

## 6. Evaluation

### 6.1 Tier 1: every iteration, free

- **Local detector:** a small classifier trained on human texts versus synthetic mirrors (architecture is the builder's choice; it must train on the Mac or within the Tinker budget). Two checks before it is trusted:
  - Area under the ROC curve (AUROC) on held-out mirrors.
  - Rank correlation with Pangram on the calibration set (section 6.2). If the Spearman correlation is below 0.5, treat local scores as weak, and spend a larger share of Pangram credits on dev checks.
  - Keep a frozen copy of the version that was calibrated. Later versions may be trained on pipeline outputs, but comparisons over time use the frozen copy.
- Claim check and quality judge as in 5.1.

### 6.2 Tier 2: Pangram at milestones

- **Settings:** bulk API, with the model selector pinned (call `GET /models` and pin `pangram-4` or its 4.x successor). Record the returned `version` with every result.
- **Fields recorded:** `prediction_short`, `fraction_ai`, `fraction_ai_assisted`, and per-window labels with `humanizer_score`, used for diagnosis.
- **Calibration set:** about 150 texts of about 500 words (human, raw AI, and pipeline outputs), scored once, to check the local detector.
- **Milestone runs:** held-out set H1 (100 drafts), cut to about 500 words each (about 50,000 words, about $20 with the bulk discount). At most 4 runs. These report results; they never choose anything.
- **Final run:** held-out set H2 (50 drafts of about 500 words, about $10), scored once. Also 5 to 10 full-length outputs (1,500 to 2,500 words).

### 6.3 Tier 3: human panel at the end

- At least 3 readers who use AI heavily (Henry recruits them from friends or colleagues, unpaid).
- Each sees a blind mix of pipeline outputs and real human posts on matched topics, and labels each as human or AI.

### 6.4 Success criteria

On the held-out set, all four of these together:
- at least 50% of outputs labeled "Human" by Pangram 4.x
- claim check passes on every output
- quality judge win rate against the input of at least 50%
- reader-panel accuracy of no more than 60%

Partial results (for example, Pangram passes but quality fails) are reported as such, not rounded up.

## 7. Budget and sequencing

| Phase | What happens | Spend |
|---|---|---|
| 1. Free build | Data, synthetic mirrors, local detector, claim check, quality judge, editor | $0 (frontier calls through Henry's Claude Code plan) |
| 2. Probe | B1 base-model continuations; score 10 base, 5 instruct, 5 human passages of about 500 words on Pangram | $5 Pangram developer credits, about $2 Tinker |
| 3. Writer experiments | B0 on the Mac; B2 and B3 on Tinker or the Mac; iterate on the local detector and dev set only | about $10 to $15 Tinker |
| 4. Pangram month | Henry buys Professional ($65, includes $200 API credits). Calibration (about $30), milestone runs ($20 each), final run (about $15) | $65 |
| 5. Panel | Blind reader test | $0 |

Total: about $80 to $90, which leaves headroom under $100. Phase 4 starts only when phase 3 has a writer worth scoring, because the plan's one-month clock starts at purchase. If Tinker is unavailable (waitlist or no access), B2 and B3 run on the Mac at 4-bit and phase 3 costs $0.

## 8. Decisions

Henry's decisions:
- The input is any AI text, with no human material behind it.
- The tool may edit like a human editor: cut, reorder and drop points, but invent nothing.
- The metric is the three tiers in section 6.
- Total spend is at most $100.
- Claude may browse and use Henry's signed-in Pangram and X accounts for research, after confirming it is driving the Chrome on this Mac.

Claude's calls (Henry should check these):
- Project location `~/personal/humanizer`, as a command-line tool first.
- The editor outputs notes, never prose.
- Target output length of 60 to 80% of the input, not enforced.
- Pass bars: 95% of claims entailed, quality win rate of at least 50%, panel accuracy of no more than 60%, and at least 50% "Human" on Pangram.
- Retry limit of two.
- B0 runs at 4B on the Mac rather than 9B on a rented GPU.
- Pangram is never used as an optimization signal.

Claude's calls made after the builder check (Henry was away; please check these too):
- **Model families without paid keys.** Synthetic mirrors and test drafts come from Claude (Haiku 4.5, Sonnet 5.5, Opus 5.5, called through headless Claude Code, `claude -p`) and from open instruct models run on the Mac (Qwen3.5 instruct plus one other open family, such as Gemma). That gives at least two vendors and three model families at no cost. GPT and Gemini are added only if Henry provides keys. Bulk Claude calls are kept moderate because the Claude account is shared with Henry's work computer: about 600 human/AI pairs for the detector, not thousands.
- **Target register.** The target is a generic human register, not Henry's voice. The B2 document prefix uses pre-2022 public human texts, never Henry's AI-written posts. Henry's published posts form a separate stress-test set that is reported but not part of the success criteria.
- **Who may use Pangram scores to decide what.**
  - Only the B1 probe (a go/no-go gate) and the calibration set (which validates the local detector) may influence decisions.
  - Writer and prompt selection uses the dev set with the local detector, the claim check and the quality judge.
  - There are two held-out sets. H1 (100 drafts) gets milestone runs, which report results but do not select anything. H2 (50 drafts) is scored once, at the end, for the final claim.
- **What counts as Human.** "Human" means `prediction_short == "Human"`. Mixed and AI both count as failures, the strict reading Epoch used. `fraction_human` is reported alongside. In the B1 probe only the base model's continuation is scored, with the human opening removed.
- **If B1 fails.** B0 still runs, but on the local detector only and at lower priority, because removing post-training directions is a different hypothesis from raw base text. If every writer fails, the deliverable is an editor-only tool plus a negative-results report.
- **Shipping form.** The shipped tool must run on the Mac with no per-use cost beyond the Claude plan for the editor. Tinker and rented GPUs are for experiments only, so a winning writer must export to 4-bit or 8-bit MLX and keep its quality there.

Henry's to answer when convenient (no work waits on them):
- Is there a deadline, and how much of his time is available?
- Who are the 3 or more heavy-AI-user readers for the panel?
- Does he want GPT or Gemini in the mix badly enough to supply keys?

## 9. Left to the builder

- Local detector architecture and training recipe.
- Human corpus sources (within the section 5.3 limits).
- Exact prompt formats for the editor, the base-model document prefix and the judges.
- B0 layer selection, rank of the removed direction, and the forward-pass budget.
- Which frontier models generate test drafts, as long as at least three families are used.
- Code layout and tests.

## 10. Risks and open questions

- **Pangram may already catch base-model text.** Pangram 4 likely trained on base-model and HALO-style outputs after those papers. The phase 2 probe exists to find this out for $5 before anything else is spent.
- **Quality from 9B base models may be too low** for long explanatory pieces. That is why B2 measures quality before detection.
- **Proxy drift.** As the writer changes, the local detector may stop tracking Pangram. The calibration check and the frozen copy guard against this.
- **The editor's choices are still AI choices.** Pangram labels ideas without a human source as AI-generated whatever the wording. If the writer approaches all fail while the editor's cuts already help, that tells us the ceiling sits in content choices. That would itself be a finding.
- **Release.** A general tool that passes Pangram is what cheaters want. If it works, share the results with Pangram before any public release. Whether to publish at all is Henry's decision when there is a result.

## 11. Sources

- Pangram 4 Technical Report: https://pangram-public.s3.us-east-1.amazonaws.com/pdf/pangram_4_technical_report.pdf
- Pangram API docs: https://docs.pangram.com/api-reference/ai-detection
- Pangram pricing: https://www.pangram.com/pricing
- Reinhart et al. 2025: https://arxiv.org/html/2410.16107v2
- Russell, Karpinska, Iyyer 2025: https://arxiv.org/html/2501.15654v2
- Xu et al. 2026, "Base Models Look Human To AI Detectors": https://arxiv.org/html/2605.19516v1
- Chakrabarty et al. 2025: https://arxiv.org/abs/2510.13939
- HALO, Dhingra and Pruthi 2026: https://arxiv.org/abs/2609.31876
- DAMAGE, Masrour et al. 2025: https://arxiv.org/html/2501.03437v1
- Epoch AI style-imitation study: https://epoch.ai/data-insights/ai-detectors-false-negatives
- Weight-space programming, Takehi et al. 2026: https://rikiyat.github.io/blog/weight-space-programming/
- Opus 5.5 weight-reading replication: https://github.com/csinva/weight-space-programming-autoresearch
- Tinker pricing: https://thinkingmachines.ai/tinker/pricing/
