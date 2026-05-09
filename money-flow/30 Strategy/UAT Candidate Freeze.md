# UAT Candidate Freeze

Up: [[00_Money_Flow_Command_Center|Money Flow Command Center]]

## Frozen Candidate

`money_flow_hyperliquid_eth_1h_baseline_uat_candidate`

| Field | Value |
| --- | --- |
| Venue | Hyperliquid |
| Product | USDC perpetual |
| Symbol | ETH |
| Sleeve | `sleeve_1h` |
| Rules | Current baseline Money Flow rules |
| Initial UAT mode | Observation / shadow only |

## Why Selected

- It is the only clearly above-starting-equity pocket in the accepted Hyperliquid public dynamic-equity evidence.
- It is the best current UAT behavior-observation candidate.
- Lower-RSI variants did not beat it.
- It is narrow enough to keep UAT0/UAT1/UAT2 scoped.

## What Is Excluded

- `sleeve_15m`
- `sleeve_4h`
- BTC `sleeve_1h`
- SOL `sleeve_1h`
- lower-RSI variants
- market-structure variants
- Aster / Binance / OKX / Coinbase / Kraken
- cross-venue comparison

## Warnings

- Profitability is not proven.
- Paper trading is not approved.
- Live trading is not approved.
- Exchange order submission is not approved.
- UAT validates plumbing and behavior, not performance.
