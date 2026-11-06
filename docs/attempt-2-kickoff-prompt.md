# Attempt 2 kickoff prompt

Henry pastes the block below into a fresh Claude Code session started in `~/personal/human`.

```
You are taking over the humanizer research project in ~/personal/human for attempt 2.

The goal: turn an AI-drafted blog post, above all my own technical posts on henryvu.blog (1,500 to 3,000+ words, drafted with Claude), into prose that Pangram 4.x and careful readers judge human-written. It must be better writing than the draft, and it must add no facts, numbers, names, dates, quotes or anecdotes.

Attempt 1 ran 2026-11-04 to 2026-11-06 (experiments B0 to B38) and is closed.

Read first, in this order:
1. docs/attempt-1-closeout.md. It covers findings, what worked, dead ends, open questions, full setup for the Mac, the Windows PC, Modal, Pangram, Claude in Chrome and the Claude CLI, resources left, and lessons.
2. CLAUDE.md (project rules).
3. results/LABNOTEBOOK.md (one row per experiment, the search log, the credit ledger).
4. The "Where this stands" sections and sections 30 to 39 of results/REPORT-2026-11-04-lora.md.
5. docs/specs/2026-11-04-humanizer-design.md and docs/specs/2026-11-06-longform-program.md.
6. results/RESEARCH-2026-11-04-prior-work.md and results/research/.
7. docs/private/machines.md (local only) for machine and account details.

Treat every finding from attempt 1 as a claim to test, not a fact. Be as ready to refute as to confirm, and check the important ones against the raw files before you build on them.

Your job in this session:
1. Research first.
   - What has changed since 2026-11-06: Pangram versions and documentation, new papers and open-source work on detection and humanization, long-context open base models.
   - Fields that bear on the open questions: stylometry, content planning, authorship, detector evaluation, editing workflows.
   - Run parallel research agents where the breadth justifies it, and save each raw report under results/research/ with a search-log row in the notebook.
2. Then propose attempt 2 as a full program, not a single next experiment. Cover:
   - the goal behind the goal;
   - candidate routes, with the evidence for and against each from attempt 1 and the new research. Include the untested cells in closeout section 5;
   - the decisive experiments, with powered sample sizes, pre-registered rules and paired designs;
   - how output quality will be measured. Attempt 1 never validated quality;
   - what infrastructure to reuse or build;
   - costs per phase in Modal dollars and Pangram credits;
   - validators and red teams for every result;
   - stop rules.
   Write it as docs/specs/<date>-attempt-2-design.md and bring it to me before running anything that costs money.

Rules that carry over (details in the closeout and CLAUDE.md):
- Money and accounts:
  - Total project spend is capped at $100.
  - No money, accounts or API keys without my explicit yes.
  - Modal: stay inside the $30 monthly free credit unless I approve more.
  - Pangram credits are mine to spend (8,717 left on 2026-11-06), but budget them and record every scan in the ledger.
- Pangram is a held-out judge. It never selects a prompt, weight or writer, except the B1 gate and detector calibration, and a local judge trained on its labels with a final test set that judge never sees (my 2026-11-06 exception).
- Fix selection, exclusion and decision rules in the script docstring and commit them before any scan. Amendments carry the time from `date`.
- Machines and tools:
  - No heavy jobs on the Mac. Training and generation go to the PC (under the C:\gpu-lock lock, shared with my umwelt project) or Modal.
  - Bulk `claude -p` calls go through humanizer.llm, at most 4 workers.
  - Before any Claude in Chrome action, confirm it is this Mac's Chrome with a one-time 127.0.0.1 token.
- Repo:
  - The repo is public. Texts derived from essays or corpora stay gitignored.
  - Commit only your own files with a pathspec.
  - Push only when I ask.
  - Never read .env.
- My context-engineering post describes a project whose details stay private. Keep the post's own wording about it (for example "diabetes management coaching agent") and add nothing about the project, its owner or its users, anywhere.
- Never be the only judge of your own work. Validate with something outside the model: raw-file recomputes, outside-judge agents given the artifact and not your reasoning, and red teams.
- Pass this line to every subagent: "work at expert depth, start from raw data, verify with an external check, report what you could not verify".
- Work without waiting for me. Stop only for money, my accounts, or my drafts.
- Writing: no emojis, no em dashes, no fluff, acronyms spelled out on first use, no blockquotes in anything I will paste.
```
