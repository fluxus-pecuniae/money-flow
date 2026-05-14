"""Paper-observation runtime primitives.

PT-RT1 deliberately separates public-mainnet strategy truth from testnet
plumbing probes. Nothing in this package creates production execution artifacts.
"""

from services.paper_runtime.pt_rt1 import (  # noqa: F401
    PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
    PT_RT1_MAINNET_INFO_URL,
    PT_RT1_TESTNET_INFO_URL,
    Candle,
    PaperLedger,
    TestnetProbeCandidate,
    TestnetProbePolicy,
    build_pt_rt1_summary,
    canonical_candle_close,
    compute_indicator_snapshot,
    evaluate_closed_candle_gate,
    resolve_top20_universe,
    validate_strategy_truth_payload,
)
