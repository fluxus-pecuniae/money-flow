# Research Log Schema (RLOG1)

Every research phase records a structured post-mortem as a fenced ` ```yaml `
block inside its `money-flow/03_Decision_Log.md` entry, under a top-level
`research_log:` key. `scripts/build_research_log.py` aggregates these blocks
(read-only), joins each to its committed `docs/*_summary.json` evidence, and
emits `docs/research_log.json`, which the dashboard Research Log renders.
CI runs `build_research_log.py --check` as a drift guard.

## Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `phase` | yes | Phase id (e.g. `SEL-EV1`). Unique across blocks. |
| `date` | yes | `YYYY-MM-DD`. |
| `class` | yes | One of `per_symbol_rule`, `cross_sectional_selection`, `variant`, `source_reconstruction`, `friction`, `audit`, `data_prep`. |
| `outcome` | yes | **The honest taxonomy — authored here, never inferred from a summary status string.** One of `fail` (hypothesis failed), `mixed` (partial/none promoted), `context` (diagnostic/audit/data work, not a pass/fail test), `pass` (cleared the gate — none to date). Renders red / amber / blue / green. A non-positive result must never be authored `pass`. |
| `badge` | no | Short badge text (defaults to the outcome). |
| `title` | yes | Human title for the timeline row. |
| `finding` | yes | One-line finding for the collapsed row. |
| `why` | yes | Why it failed (or why it matters, for `context`). |
| `worked` | yes | What worked. |
| `didnt` | yes | What didn't. |
| `lesson` | yes | The lesson. |
| `our_error` | yes | Text when the error was ours (cite a `K-0xx` where one exists, e.g. K-019), or `null` when the method was clean. |
| `our_error_note` | no | Shown when `our_error` is `null` (e.g. "the test caught its own overfit"). |
| `changed` | yes | What it changed going forward. |
| `hardened_gate` | no | String or list — feeds the "Lessons → hardened gates" rail. |
| `evidence_summary` | yes | Repo-relative `docs/*_summary.json` path to join. |
| `evidence_doc` | no | Repo-relative human report path. |
| `analytics` | no | List of `{label, kind, source}`: `kind: value` resolves a dotted path in the summary; `kind: computed` names a deterministic view in `build_research_log.py` (e.g. `exec_ev1_symbol_concentration`, `sel_ev1_random_benchmark`); `kind: table` resolves a dotted path to a `{columns, rows}` object. |

## Example

```yaml
research_log:
  phase: SEL-EV1
  date: 2026-06-10
  class: cross_sectional_selection
  outcome: fail
  badge: no selection skill
  title: Cross-Sectional Breakout Selection
  finding: >-
    Failed the matched-cadence random benchmark OOS (beat 2 of 50 seeds).
  why: >-
    The train-chosen config overfit; the ranking signal carries no forward
    information.
  worked: >-
    The method - the no-lookahead simulator + random benchmark caught the
    overfit cleanly.
  didnt: >-
    The signal - breakout strength and vol-adjusted momentum rank no better
    than chance.
  lesson: >-
    In-sample selection PnL is worthless; the bar is beating random OOS after
    friction.
  our_error: null
  changed: >-
    Random-benchmark + rotation-diversity became the standard selection gate.
  hardened_gate: beat random OOS, or it's nothing
  evidence_summary: docs/sel_ev1_selection_evidence_summary.json
  analytics:
    - label: Random benchmark headline
      kind: computed
      source: sel_ev1_random_benchmark
```

## Workflow

1. Write the block into the phase's Decision Log entry (additive — never
   rewrite the factual record).
2. Run `.venv/bin/python scripts/build_research_log.py`.
3. Commit the regenerated `docs/research_log.json` with the phase.

Boundaries: the aggregator is read-only over committed docs; display/tooling
only. No runtime, strategy, order, testnet, or approval behavior.
