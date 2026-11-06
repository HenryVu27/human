# Agent report: B33 calibration set build (every Pangram verdict B1 to B31 joined to its scanned text)

Saved verbatim from the agent's final report, 2026-11-06 about 02:00 CST. The agent had read access to the repo and
the scratchpads and wrote only `results/b33_calib.jsonl` (gitignored, texts) and `results/b33_calib_manifest.json`
(numbers only). Its build and check scripts are in the session scratchpad `b33/` folder.

## Brief given to the agent (summary)

Goal: the open-detector panel is calibrated against every text the project has already scanned with Pangram.
Join each verdict to the exact scanned text (reproducing each experiment's export step), record label, AI share
where recorded, words and origin; skip rather than guess; check 15 random rows against independent records and all
report tables. No repo edits, no git state changes, no Pangram, Claude CLI or Modal calls. Rule line passed: work
at expert depth, start from raw data, verify with an external check, report what you could not verify.

## Report

**Outputs**
- `results/b33_calib.jsonl`: 1,201 rows. 1,200 are `exact` and 1 is `probable`.
- `results/b33_calib_manifest.json`: numbers only, with per-cell counts, a text digest per experiment, the duplicate
  groups and the results of the checks.

No tracked repo file was changed and nothing was committed.

**Rows per experiment, with origin**
- B1: 4 (base). The 13B probe from report section 6, labelled `Probe13B`: 1 (local_writer).
- B3 20, B4 20, B5 40, B6 16, B7 30, B8 20, B9 40, B11 20, B13 20, B14 20, B16 20, B17 7, B18 6, B20 4, B24 10,
  B26 26 (V and M): all local_writer.
- B10: 20 (instruct).
- B12: 40 (R is local_writer, K is instruct).
- B15: 14 (O is edited_human, meaning Henry's post that he says was AI-rewritten; B is local_writer).
- B25: 26 (H human, D instruct). B27: 13 (instruct). B28: 76 (H human, S100/S50/S25 instruct).
- B29: 13 (12 instruct, plus 1 `recited_human`: Y_e2ee0c4c0, where Sonnet recited Sutton's essay at 99.6%
  similarity).
- B31: 675 (human arm 30, instruct arms 30, base 615 including B1's 4-bit texts).
- Totals: base 619, local_writer 347, instruct 165, human 62, edited_human 7, recited_human 1.
- Labels: Human 704, Mixed 189, AI 308. `ai_share` is recorded for B31, B1 and the probe (680 rows); it is null
  elsewhere because the dashboard uploads gave labels only.

**How each join was done**
- **The uploaded files survive.** The session scratchpad (`b3serve`, `b4docs` ... `b29y`) still holds every
  .docx/.txt uploaded for B3 to B29. Another session's scratchpad (`b31/upload/batch00-06`) and
  `results/b31_raw_up/7` hold B31's. Each was made minutes before its record commit. Every file was extracted with
  `textutil` and the repo text was required to match the file exactly after stripping outer whitespace. All 1,196
  match.
- **Per experiment, the scanned text is:**
  - B3/B4: the seed-0 texts files, checked against the recorded words too.
  - B5/B6/B7/B9: the raw generations.
  - B8, B11 to B14, B16, B18, B20, B24, B26: the pruned or picked `texts` field, not `raw`.
  - B10, B12 K: the Sonnet condensation as raw markdown.
  - B15/B17: the section body without its title.
  - B25 H, B28 H: the essay text.
  - B25 D: the draft passed through `b25_blog.plain` (loaded from the script read-only).
  - B27/B28 S/B29: the plain-text field in `data/`.
- **B31:** blind name to `b31_blind*.json` to (arm, doc) in `b31_texts*.jsonl`. All 675 match the recorded words,
  the uploaded file, and the label and ai_share in the raw batch transcripts `b31_pangram_b0-7.txt`.
- **B1 and the probe:** pasted, so no file exists. The texts reproduce exactly from `b1_generations.jsonl` and
  `gpu13b/out/dev_generations.jsonl` by the recorded cut rules. Pangram's reported word counts (374, 383, 347, 445)
  match the token count of the stored texts.
- **B1 qwen h0600 is the one `probable` row.** Its 391 matches only if straight apostrophes stay inside words, and a
  later note calls the first 391 words "an approximation" of what was scanned.

**External checks (all pass)**
- Label counts from the set match all 70 report table cells, transcribed by hand from REPORT-2026-11-04-lora.md and
  REPORT-2026-11-05 section 2.1.
- They also match all 67 experiment summary-json cells.
- B28 labels match the dashboard transcript `b28hs/page.txt`, 76 of 76.
- Spot check of 15 random rows (seed 0): 15 of 15 confirmed. Each was checked by finding the uploaded file from the
  text, re-reading the label from an independent record, and comparing a recorded word count. 11 of the 15 drew
  from B31, so one row per experiment was added: 26 of 26.
- Mean words match the report for B3, B4, B5, B8, B11 to B18, B20, B24.

**Findings**
1. `results/b33_calib.jsonl` was not gitignored at build time (fixed by the head session in ff23856 before any
   commit of results).
2. The uploaded files live only in `/private/tmp` scratchpads, which can be wiped. The manifest's per-experiment
   digests are the remaining integrity record.
3. 8 pairs of identical texts were scanned twice: seven B13 C / B14 B pairs, plus B12 R a0614 = B13 C a0614. Every
   pair got the same verdict. Deduplicate before computing detector statistics.
4. B6 report mean words (284 F, 380 G) match no count of the scanned texts. Whitespace counts give 279.4 and 387.6.
   The labels match. The report's per-text figures (69, 83, 99) are Pangram-style token counts, not whitespace
   counts.
5. Possible confounds for detector calibration: 14 rows are under 150 words, below Pangram's reliable floor; 45 rows
   contain markdown headings (B10, B12 K, 5 in B31); instruct rows read Human 13 of 165; human rows read Human 62 of
   62.

**Not verified**
- That each scratchpad file is byte-for-byte the one uploaded. This is inferred from names and timestamps; only B28
  and B31 have an independent per-file dashboard transcript.
- Pangram's exact tokenization.
- The pasted B1 and probe texts, which have no file.
