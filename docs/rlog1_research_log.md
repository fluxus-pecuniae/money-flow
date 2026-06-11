# RLOG1 — Research Log: Honest Post-Mortems, Auto-Joined + Analytics

Display + docs/tooling only. No runtime, strategy, data-source, order,
testnet, or approval change. The aggregator is read-only over committed docs;
the Decision-Log backfill only **added** fenced blocks (the factual record is
unchanged).

## What shipped

- **Must 1 — schema + backfill.** A machine-readable post-mortem convention:
  each research phase's `money-flow/03_Decision_Log.md` entry carries a fenced
  ```yaml `research_log:` block (`phase`, `date`, `class`, **`outcome`** ∈
  `fail`/`mixed`/`context`/`pass`, `why`, `worked`, `didnt`, `lesson`,
  `our_error`, `changed`, `evidence_summary`, optional `analytics` +
  `hardened_gate`). Backfilled honestly into 12 phases: SEL-EV1, EXEC-EV1,
  SV2.3, SV2.2, GOAL-STRAT1, GOAL-STRAT2, SOR-EV1/EV2/EV3, MF-ORIG-EV1.1,
  MF-ORIG-EV2, EV-AUDIT1 (e.g. EXEC-EV1 `our_error` = the missing
  concentration gate that let ZEC slip through, fixed via leave-one-out;
  MF-ORIG-EV1.1 `our_error` = K-019 fee double-count, corrected; SEL-EV1
  `our_error` = null — the test caught its own overfit). Schema doc:
  `docs/research_log_schema.md`.
- **Must 2 — aggregator.** `scripts/build_research_log.py` (read-only,
  deterministic, offline): parses the blocks, joins each phase's committed
  `docs/*_summary.json`, resolves analytics (named computed views + dotted
  paths), joins active lanes from `current_truth.json`, derives the
  "Lessons → hardened gates" rail from authored `hardened_gate` fields, and
  emits `docs/research_log.json` newest-first. `--check` exits non-zero on
  drift (CI-wired). **`outcome` comes only from the authored taxonomy — never
  inferred from a raw status string.**
- **Must 3 — render.** The dashboard Research Log now renders the prototype
  (`docs/dash_rlog1_prototype.html`) from `research_log.json`: standing strip
  (130+ hypotheses / 7 families / passed 0 / production NONE / live NOT
  APPROVED / "no price-rule edge"), the red verdict banner, the newest-first
  expandable post-mortem timeline with the six facets, per-phase analytics on
  expand (EXEC-EV1 per-symbol concentration: ZEC 132%, ex-ZEC −36k, 15/23
  negative; SEL-EV1 random benchmark: 2/50 seeds beaten + near-miss configs;
  SV2.3 aggregate; GOAL-STRAT1 budget; SV2.2 coverage), evidence links, the
  lessons rail, the active-lanes card, and the boundaries footer. Badges:
  `fail`=red, `mixed`=amber, `context`=blue, `pass`=green — **a non-positive
  result can never render green** (the naive
  `verdict||audit_verdict||gate_status||status` coloring is gone).
  Theme-aware across dark/light/red-zone.
- **Must 4 — tests + CI.** `tests/test_rlog1_research_log.py` (6 tests):
  reproducible build + `--check`; the pinned regression that upbeat raw
  status strings ("…ready_for_founder_review", "…complete") keep their
  authored non-positive outcomes; per-phase entries with all facets; real
  joined analytics; renderer uses the authored outcome only. CI blocking
  lane runs the suite plus `build_research_log.py --check`. DASH-QA1 gained
  check #10 (≥12 post-mortems, zero green badges, SEL-EV1 renders fail,
  facets visible) — **10/10 green**.
- **Must 5 — self-updating.** AGENTS.md post-task workflow now requires every
  research phase to write its `research_log` block and run the aggregator;
  the CI drift guard enforces it.

## Verification

- `scripts/build_research_log.py --check` → ok; rebuild byte-identical.
- `tests/test_rlog1_research_log.py` → 6 passed; static-asset +
  operational-docs guards green; DASH-QA1 10/10.
- Three themes rendered with zero page errors; screenshots in
  `docs/rlog1_screenshots/`.
- Cache-buster `rlog1-research-log-20260611`.

## Boundaries

Read-only aggregation + display. No runtime, strategy, data-source, order,
testnet, or approval change. Decision-Log backfill additive only. K-033
(placeholder Research Log) is resolved by this phase.
