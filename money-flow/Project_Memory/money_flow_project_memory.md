# Money Flow Project Memory — Team Chronicle

## 2026-05-07T09:08:46Z SV1.13.1 - Capital Sizing Interpretation Hotfix

SV1.13.1 now explicitly labels the current evidence sizing model as constant initial-capital notional per opened trade. In the SV1.13 Hyperliquid public campaign, `initial_capital=10000` and `position_notional_pct=1.0`, so every opened trade uses `10000` notional. Realized equity is tracked for net PnL, closed-trade drawdown, mark-to-market drawdown, and return on initial capital, but it does not reduce, compound, or stop the next trade size.

This preserves evidence numbers and strategy rules while making interpretation safer. Dynamic account-equity sizing is not implemented in this hotfix and remains a separate future evidence phase before paper-trading design should rely on account-style sizing assumptions.

## 2026-05-07T08:03:28Z SV1.13.1 - Evidence Interpretation Truth For Founder Review

SV1.13.1 interprets the existing Hyperliquid public campaign evidence packs without regenerating packs, importing data, changing Money Flow rules, or approving paper/live trading. It adds a founder-readable interpretation report that separates individual scenario results from grouped aggregate research summaries.

The key truth is that grouped totals across symbols, fill timings, fee assumptions, and slippage assumptions are descriptive sums across research runs, not one tradable account/scenario PnL. The report makes ETH `sleeve_1h` concentration explicit, shows fill-timing and cost sensitivity, records drawdown/regime/no-trade observations, and keeps paper-trading design deferred until manual founder/operator review accepts a later scope.

## 2026-05-07T07:50:13Z SV1.13 Dashboard - Evidence Visualization For Founder Review

SV1.13 now has a static local `apps/dashboard/` surface for reviewing ignored local evidence artifacts in a human-readable way. The dashboard uses the supplied design files/tokens, loads the SV1.13 Hyperliquid evidence review plus component batch reports from `reports/strategy_validation*` when served from the repo root, and supports manual JSON loading.

This is visualization only. It does not generate evidence packs, import candles, call exchange endpoints, approve paper/live trading, optimize parameters, or change Money Flow rules. Manual founder/operator review of the Hyperliquid-only evidence remains the next Strategy Validation step.

## 2026-05-06T23:12:10Z SV1.13 - First Hyperliquid Public Campaign Evidence Packs

SV1.13 generates the first Hyperliquid public campaign Money Flow evidence packs from the imported `25848` public YTD/recent candles in the intended local `money_flow` DB. The DB remains migrated/current at Alembic head `20260430_0025`, BTC/ETH/SOL Hyperliquid research identity remains operator-verified by `Tercirafael`, non-trading, and non-strategy-eligible, and evidence review expands the public campaign into component-scoped packs for `sleeve_15m`, `sleeve_1h`, and `sleeve_4h`.

The result is `ready_for_founder_review`, not proof of profitability, not strategy recommendation, not paper/live approval, and not cross-venue Money Flow performance. Aster/Binance remain later comparative candidates after separate identity/import work; OKX/Coinbase remain blocked by public trade-count/source policy; Kraken remains blocked by public REST history limits. The next Strategy Validation step is manual founder/operator evidence review before any explicitly approved paper-trading design phase.

## 2026-05-06T22:23:16Z SV1.12.5.1 - Import State / Repo State Closeout

SV1.12.5.1 closes the dirty-tree/import-state gap before evidence-pack generation. The operator-approved Hyperliquid public campaign import is verified in the intended local `money_flow` DB: schema is current at Alembic head `20260430_0025`, BTC/ETH/SOL Hyperliquid research identity is operator-verified by `Tercirafael`, non-trading, and non-strategy-eligible, and the 9-file public YTD/recent campaign has `25848` persisted candles with the expected symbol/timeframe counts. At closeout time, no evidence packs had been generated yet. SV1.13 may run post-import evidence review only if audits remain clean; paper/live trading remains blocked by manual founder review and the standing pre-paper/live blockers.



## 2026-05-06T21:09:00Z External Strategy Review Caution - Coherent But Unvalidated

The external strategy review described Money Flow as a coherent long-only momentum strategy across 15m/1h/4h sleeves, but it was unvalidated at the time because no first real evidence packs existed yet. Track concerns as Strategy Validation questions, not accepted rule changes: no hard stop-loss, narrow RSI bands, lagging MACD exits, same-candle fill optimism, long-only bear-market exposure, possible cosmetic confidence scoring, 100% notional sizing/drawdown assumptions, and handcrafted-looking parameters. SV1.13 now provides first Hyperliquid public evidence for manual review, but out-of-sample validation, risk-adjusted metrics, and fee/slippage/drawdown truth remain required before paper trading or any ATR-stop/parameter-change phase.
## 2026-05-06T21:01:42Z External Review Caution - Paper/Live Trading Blockers

A 2026-05-06 external review reported critical/high blockers that must be resolved before paper trading, live trading, exposed API usage, or production-like deployment. Do not store actual secret values in memory. Track only sanitized actions: rotate any live credentials found in local `.env`; add API authentication/authorization before exposing execution-facing routes; enforce configured global risk limits; replace hardcoded drawdown truth with real drawdown calculation; fix Strategy Validation mark-to-market fee/drawdown reporting before founder evidence review; disable debug stack traces outside local-only development; make exchange live/demo mode fail-safe; and address medium/low strategy/adapters/config hardening. Current Strategy Validation candle-data research can continue, but evidence readiness alone is not paper/live readiness.
Prepared by the current standing team:
- Quant Engineer
- Exchange Architect
- Full-Stack Architect

Purpose:
A living reminder of how this project evolved, what decisions were made, what concerns were raised, and where the platform is trying to go. This document is intentionally opinionated and historical. It is meant to help future you and future teammates understand *why* the codebase looks the way it does.

---

## 1. The original starting point

The project began around a **Money Flow-inspired strategy**:
- based on 5 EMA, 10 EMA, 20 SMA, RSI, and MACD
- originally imagined as a multi-timeframe strategy using 15m, 1h, and 4h

Very early on, the concept shifted away from:
- “one blended multi-timeframe strategy”

toward:
- “three sleeves / three internal strategy lanes”
  - 15m
  - 1h
  - 4h

That was an important early move because it made the system easier to:
- test
- attribute
- debug
- extend later

At that stage, the architecture idea was:
- one shared account
- three strategy sleeves
- shared portfolio/risk/execution/control plane

This was already more platform-like than a typical single-bot script.

---

## 2. Why the project was built in Python first

The decision was to build in Python rather than Rust because the platform was still in the:
- architecture discovery phase
- exchange integration phase
- signal/research/prototyping phase

The reasoning was:
- Python is faster for iteration
- much of the system is integration-heavy and I/O-bound
- strategy research and debugging are much easier in Python
- Rust could later be introduced for specific performance-critical services:
  - market data normalization
  - execution routing
  - high-throughput stream handling

So the decision was not:
- Python forever

It was:
- Python first
- Rust later where it actually earns its complexity

---

## 3. Phase 1 — the real beginning of the platform

Phase 1 was the architectural scaffold.

Goals:
- define domain boundaries
- define config model
- define environment model
- define database scaffold
- define API scaffold
- define service interfaces
- avoid fake implementations

Important outcomes:
- typed domain models
- separation of domain / persistence / API schemas
- modular service boundaries
- one shared account model with sleeves on top
- Docker/dev setup
- architecture docs and Mermaid diagrams

This was not trading logic yet.
It was the “bones” of the platform.

What mattered most:
- the repo started as a platform scaffold, not a script pile.

---

## 4. Phase 1.1 — foundation hardening

Phase 1.1 cleaned up the early scaffold.

Key improvements:
- fixed README/doc issues
- tightened the role of `system_state`
- added explicit Hyperliquid-specific contract boundaries
- added universe policy
- added smoke tests
- validated migrations and API startup

This was where the team started insisting that:
- summaries are not enough
- validation matters
- docs should stop drifting from reality

This phase started the habit of:
- hardening before layering more logic on top

---

## 5. Phase 2 — exchange / data / state foundation

Phase 2 turned the scaffold into a real exchange-aware foundation.

It added:
- Hyperliquid adapter
- universe sync
- asset and symbol handling
- candle ingestion and persistence
- account snapshot sync
- order/fill/position reconciliation
- portfolio loader primitives
- control-plane API endpoints
- migration support

This was the phase where the system became aware of:
- tradable universe
- account state
- positions
- fills
- orders
- candles

Important insight:
The team started treating the platform as:
- exchange/data/state first
- strategy second

That was the right order.

---

## 6. Phase 2.1 — identity, checkpoints, and future venue hardening

Phase 2.1 fixed important structural weaknesses before strategy logic arrived.

Main improvements:
- stronger instrument normalization
- venue-aware persistence
- checkpoint semantics for candle sync
- execution-quality data placeholders
- explicit separation between exchange truth and sleeve attribution
- reduced coupling to Hyperliquid concrete classes

This phase also corrected a critical problem:
the code had been too symbol-shaped and too Hyperliquid-shaped.
2.1 started pushing it toward:
- canonical instruments
- venue mappings
- future venue readiness

This was a major turning point.

---

## 7. Phase 3 — indicator pipeline and first strategy layer

Phase 3 built:
- deterministic indicators
- persisted snapshots
- modular strategy family framework
- Money Flow as the first strategy family
- first real strategy decisions
- first real no-trade / invalid reasoning

At first, this phase was stronger as:
- an entry/no-trade engine

than as:
- a full strategy system

The team review found several issues:
- stale indicator risk
- non-idempotent decision persistence
- ambiguous instrument identity
- missing exit logic
- weak venue-safe semantics
- too much trust in summaries rather than code

This was the phase where the team formally changed its review standard:
- no more approving the next phase off handoff summaries alone
- actual code inspection would be required

That was an important governance turning point.

---

## 8. Phase 3.1 — strategy hardening

Phase 3.1 fixed the main issues in the strategy layer.

Important additions:
- explicit `instrument_key` vs `instrument_ref_id`
- stale-indicator rejection
- idempotent evaluation keys
- Money Flow `hold / reduce / close`
- better portfolio summary semantics
- builder/HIP-3 discovery vs eligibility separation
- stronger tests

This phase turned the strategy layer from:
- mostly “entry proposal logic”

into:
- a more complete decision layer with inspectable, idempotent, account-aware outputs

It also clarified a major strategic truth:
Money Flow is the **first strategy family**, not the platform.

---

## 9. Phase 3.2 — repo governance and operational memory

Phase 3.2 was not trading logic.
It was project-discipline work.

It added and normalized:
- `AGENTS.md`
- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- validation tests for operational docs

This phase matters because the team repeatedly noticed that:
- code was improving
- but docs and memory could drift
- and future contributors (human or AI) would lose context

So the repo now has a memory workflow:
- read before work
- log after work

That is an important part of making the platform durable.

---

## 10. Phase 3.3 — Client / VenueAccount / StrategyDeployment

Phase 3.3 recognized that the old model was still too single-account shaped.

It introduced first-class:
- `Client`
- `VenueAccount`
- `StrategyDeployment`
- `SleeveDeploymentConfig`

This was important because the next future was already visible:
- one client
- many accounts
- many venues
- many strategies eventually

But 3.3 still made `StrategyDeployment` the top-most strategy object.
That was better than before, but still not enough for the real long-term vision.

The team’s reaction:
- good progress
- still too narrow
- needed another architectural step before Phase 4

---

## 11. Phase 3.4 — StrategyMandate and account-group direction

Phase 3.4 added the next abstraction:

- `StrategyMandate`
- `MandateAccountBinding`
- `StrategyComponentConfig`

This was the big conceptual shift.

Instead of:
- one strategy on one account as the main top-level object

the platform started moving toward:
- one logical strategy umbrella
- spanning many account bindings
- with account-group semantics for future routing

This matched the real vision better:
- one Money Flow mandate
- potentially across Hyperliquid, Aster, OKX, etc
- future router chooses the venue/account path later

The team strongly agreed with this direction.

---

## 12. Phase 3.5 — cleanup of legacy deployment/sleeve baggage

Phase 3.5 cleaned out the transitional leftovers from 3.3/3.4.

It removed or deprecated active use of:
- legacy `StrategyDeployment`
- legacy `SleeveDeploymentConfig`
- legacy deployment refs
- legacy `ACTIVE_DEPLOYMENT_KEY`
- old schema columns teaching the wrong hierarchy

This was the moment where the platform became much cleaner conceptually:

Current intended hierarchy after 3.5:
- `Client`
  - `VenueAccount`
  - `StrategyMandate`
    - `MandateAccountBinding`
      - `StrategyComponentConfig`

That is the hierarchy the team now believes Prompt 4 should build on.

---

## 13. The main strategic realizations along the way

### A. This is not just a Money Flow bot
The biggest realization:
the repo is no longer a “Money Flow trading bot.”

It is becoming:
- a strategy platform
- with Money Flow as the first family

### B. This is not just a signal platform
Another key shift:
the platform is not just for generating signals.

The code and architecture are clearly being shaped toward:
- native signal generation now
- risk evaluation next
- order-intent generation after that
- future account-group-aware routing
- future execution
- future multi-venue support

### C. Strategy and routing are distinct layers
The strategy should say:
- “what do I want to do?”

The router should later say:
- “where/how do I express that across eligible accounts and venues?”

That distinction became especially important once the mandate/binding model appeared.

### D. Venue truth and attribution truth must remain separate
A repeated architectural theme:
- positions, fills, balances, orders = exchange truth
- sleeve/component attribution = internal overlay truth

This should not be collapsed.

### E. We do not trust summaries alone anymore
A major process change:
the team started requiring actual code inspection before approving new phases.

That should continue.

---

## 14. The current platform vision (after 3.5)

The platform is now best understood as:

### Core hierarchy
- `Client`
  - owns many `VenueAccount`s
  - owns many `StrategyMandate`s

- `VenueAccount`
  - real exchange account truth
  - balances, positions, orders, fills, snapshots

- `StrategyMandate`
  - logical strategy umbrella
  - future routing/account-group umbrella
  - top-level “program” object

- `MandateAccountBinding`
  - membership of an account in a mandate
  - per-account policy/eligibility surface
  - future routing participation surface

- `StrategyComponentConfig`
  - family-specific internal components/config
  - for Money Flow today, these map to the 15m/1h/4h internal lanes

### Current phase boundaries
Implemented:
- exchange/data/state sync
- deterministic indicators
- Money Flow strategy decisions
- idempotent evaluation
- docs/governance workflow
- client/account/mandate/binding/component architecture

Not yet implemented:
- real risk approval
- intent creation flow
- routing
- execution
- CBBO
- child-intent fanout
- multi-venue live orchestration
- mature attribution engine
- advanced portfolio accounting

---

## 15. What the team currently sees as the next major phases

### Phase 4
Build:
- mandate-aware risk evaluation
- mandate-aware intent boundary
- initial sizing/policy checks
- idempotent intent creation
- support for `open / hold / reduce / close`
- no live execution yet

### Phase 5
Build:
- execution boundary
- order submission lifecycle
- submission/reconciliation for intents
- probably still Hyperliquid-first
- still not full smart routing

### Phase 6+
Build:
- execution-quality market data
- top-of-book and depth
- CBBO or venue-quality awareness
- child-intent fanout
- account-group routing
- future external execution backends if desired
- additional venue adapters
- portfolio maturity
- reporting / client experience layers

---

## 16. Three-year vision

### From the team’s perspective
Three years from now, if development continues on the current trajectory, this should be a:

- client-centric
- mandate-driven
- multi-account
- multi-venue
- signal + policy + routing + execution platform

The top-level object users care about will be the **StrategyMandate**, not a venue bot.

### From a new client onboarding perspective
A new client should eventually:
1. create a client profile
2. connect many venue accounts/subaccounts
3. create one or more strategy mandates
4. bind selected accounts into each mandate
5. configure family-specific components
6. let the platform later choose where/how to execute across the bound account group

### From a long-term client perspective
A client who has used it for 1+ years should think in terms of:
- mandates
- account groups
- performance
- policy
- venue/account participation
- execution quality

not:
- one exchange bot
- one strategy script
- one config file per venue

The platform should eventually feel like:
- a trading operating system
for strategies, not a bot farm.

---

## 17. Long-term design principles to keep protecting

1. **VenueAccount remains exchange truth**
2. **StrategyMandate remains the logical strategy umbrella**
3. **MandateAccountBinding remains membership/policy, not static router weights**
4. **StrategyComponentConfig remains the generic family-component abstraction**
5. **Routing should come later and should operate over eligible bindings/account groups**
6. **Do not let Money Flow vocabulary become the universal platform vocabulary**
7. **Do not let docs drift ahead of code**
8. **Do code inspection before phase approval**
9. **Do not reintroduce single-account assumptions**
10. **Keep strategy, risk, routing, and execution as separate layers**

---

## 18. Open concerns still worth remembering

These have been recurring concerns from the team:

- execution-quality market data still incomplete
- full attribution engine still incomplete
- repo handoff hygiene can still improve
- some family-specific “sleeve” naming may still linger beyond where it is ideal
- one process / one active mandate remains a current practical limitation
- routing and child-intent fanout are still future work, not present reality

These are not reasons to panic.
They are the next known frontiers.

---

## 19. Final reminder to future us

The platform has come a long way:
- from a Money Flow strategy idea
- to a multi-sleeve signal engine
- to a venue-aware exchange/data foundation
- to a strategy platform
- to a client/account/mandate/binding/component architecture

The biggest thing to remember is this:

> We are not building a single-exchange bot.
> We are building a strategy platform that will eventually generate signals, evaluate policy, form intents, route across account groups, and execute across multiple venues.

That is the north star.


---

## 20. Phase 4A — multi-venue adapter hardening

Phase 4A was the first deliberate move to pressure-test whether the platform was still too Hyperliquid-shaped.

The motivation was simple:
- if the code only works cleanly with Hyperliquid,
- then future routing / mandate / account-group ideas will be built on a false abstraction.

So the platform added three more venue integrations in controlled, read-only / QA mode:
- Aster
- OKX
- Coinbase Advanced Trade

Important point:
This phase did **not** aim for multi-venue execution parity.
It aimed to prove the shared model could tolerate:
- different product models
- different account models
- different symbol conventions
- different capability surfaces

This was the beginning of treating the platform as:
- multi-venue aware by architecture,
not just:
- Hyperliquid-first with future wishful thinking.

Key architectural lesson from 4A:
Adding venue adapters early was valuable because it exposed exactly where the shared model was still too implicitly Hyperliquid-shaped.

---

## 21. Phase 4.0.1 — mandate desired trade boundary

Phase 4.0.1 introduced one of the most important conceptual splits in the whole platform:

- `StrategyDecision`
- `MandateDesiredTrade`
- future `BindingRoutingCandidate`
- future child intent / `OrderIntent`

This mattered because the team explicitly did **not** want the system to keep behaving as if:

> one strategy decision directly becomes one account-targeted intent.

That assumption would have broken the long-term vision.

The key insight was:
- strategy should say what the mandate wants,
- not yet where it should be executed.

So 4.0.1 gave the platform a real place for:
- mandate-level desired action
- future routing candidate inspection
- quote normalization
- later child-intent targeting

However, the team review also found that 4.0.1 still had an important flaw:
- mandate desired trades were still too rooted in binding-scoped evaluation identity.

That meant it still did not fully solve the “one mandate desire vs many source bindings” problem.

So 4.0.1 was an important step,
but not the final version of that boundary.

---

## 22. Phase 4.0.2 — source policy and mandate-level trade identity hardening

Phase 4.0.2 hardened the planning boundary further.

It added or clarified:
- explicit `MandateMarketDataSourcePolicy`
- stronger `MandateDesiredTrade` aggregation / idempotency
- explicit convertibility rules
- corrected shared interface direction away from direct decision -> intent thinking
- better symbol-vs-instrument handling
- more explicit source venue vs future routing venue distinction

This phase mattered because the team realized the platform still lacked a clear answer to:

> Where does a mandate get its market truth from?

That is a different question from:

> Where should the trade eventually be routed?

4.0.2 encoded that distinction.

Key convertibility rules were tightened conceptually around:
- `PROPOSED + OPEN`
- `PROPOSED + REDUCE`
- `PROPOSED + CLOSE`
- `HOLD`
- `NO_TRADE`
- `INVALID`

The big architectural win of 4.0.2 was that the platform now had a much better chance of preventing mandate-level desired trades from fragmenting into one-per-binding simply because source evaluations came from different bound accounts.

This was one of the most important future-proofing steps in the whole project.

---

## 23. The current pre-4B boundary after 4.0.2

As of the latest accepted understanding, the platform should now be thought about like this:

### Strategy layer
Produces:
- `StrategyDecision`

### Planning boundary
Produces / formalizes:
- `MandateDesiredTrade`
- `BindingRoutingCandidate`
- quote / pricing normalization objects
- explicit source policy

### Future risk layer
Will:
- approve or reject desired trades
- not collapse back into direct decision -> intent behavior

### Future child-intent layer
Will:
- create binding/account-targeted child intents
- only when a target is actually known

### Future router
Will later decide:
- which binding(s) should receive child intents
- based on balances, liquidity, venue state, price, CBBO, and policy

The team’s strongest warning at this point was:

> approved mandate-scoped `OPEN` trades must not automatically become child intents before routing exists.

That rule remains load-bearing.

---

## 24. What the team sees as the correct 4B direction now

After 4.0.2, the correct next step is **not** the old/simple idea of:
- risk evaluation + direct order intent creation.

Instead, the right 4B direction is:
- risk evaluation over `StrategyDecision`
- approval/rejection lifecycle for `MandateDesiredTrade`
- child-intent creation **only where target binding/account is already naturally known**
- no premature routing

That means:
- mandate-scoped `OPEN` should generally stop at approved desired trade or an explicit routing-required state
- binding/account-scoped `REDUCE` and `CLOSE` can later create child intents when account truth already identifies the target

This distinction is one of the most important strategic boundaries in the current architecture.

---

## 25. The platform is now clearly more than a signal engine

The team is now fully aligned on this point:

The platform is no longer just:
- a Money Flow bot
- or a signal platform that hands everything off to some external executor

It is becoming:
- native signal generation
- policy/risk evaluation
- mandate-level desired trade formation
- future account-group-aware routing
- future child-intent generation
- future execution

This does **not** mean the platform already does all of that.

It means the architecture is now clearly trying to become:

> a strategy platform with its own signal generation now,
> and its own future policy/routing/execution stack later.

That is a major conceptual evolution from the project’s beginning.

---

## 26. Current open concerns after 4.0.2

Even after 4.0.2, the team still sees important unresolved concerns:

- execution-quality market data is still incomplete across venues
- routing and child-intent fanout remain future work
- one process / one active mandate is still a practical limitation
- generic “sleeve” wording still exists in parts of the codebase even though “component” is the better platform abstraction
- symbol-only fallback still needs to keep shrinking over time
- multi-venue source-policy support is still in an early single-source form
- handoff/archive hygiene can still improve

These are not signs of failure.
They are the next architectural frontiers.

---

## 27. Updated long-term north star

The original north star still stands, but it is now more specific.

We are not building:
- a single-exchange bot
- or just a signal engine
- or just a wrapper around someone else’s router

We are building toward:
- client-centric strategy umbrellas (`StrategyMandate`)
- reusable venue accounts (`VenueAccount`)
- account-group membership and policy (`MandateAccountBinding`)
- family-specific components (`StrategyComponentConfig`)
- strategy decisions
- mandate desired trades
- future routing candidates
- future child intents
- future routing and execution across many venues

The platform should eventually feel like:

> a strategy operating system
> that can generate, evaluate, route, and execute trading intent across a client’s account group.

That remains the north star.


## 28. Phase 4.1 — risk approval and child-intent boundary

Phase 4.1 was the first phase where the platform stopped being “just planning” and became a real approval pipeline.

It added:
- persisted `RiskEvaluation`
- desired-trade lifecycle states such as:
  - `draft`
  - `approved`
  - `rejected`
  - `routing_required`
- approval/rejection behavior over `MandateDesiredTrade`
- binding/account-targeted child-intent preparation for naturally binding-scoped actions
- downstream `OrderIntent` semantics that are now clearly child-intent territory rather than direct strategy output

The most important success of 4.1 was architectural, not tactical:

- strategy decisions remained proposals
- risk acted on `MandateDesiredTrade`
- mandate-scoped `OPEN` still stopped before routing
- `REDUCE` and `CLOSE` could prepare child intents only when binding/account truth already identified the target

This was the first phase that really made the platform feel like:
- signal generation
- planning
- approval
- future execution preparation

instead of just a strategy engine with nicer persistence.

Important caution from the team review:
4.1 was still more of a **first approval/policy gate** than a full portfolio risk engine.
The following were still largely not solved in a meaningful way:
- broad exposure policy
- concentration policy
- drawdown policy
- deeper kill-switch behavior
- cross-position / cross-binding conflict policy

So 4.1 was accepted, but not interpreted as “risk is solved.”

---

## 29. The ugliest issue after 4.1

The team’s strongest warning after reviewing 4.1 was:

> prepared child intents could still exist for venues that were not truly execution-capable enough yet.

That created a dangerous semantic gap between:
- `prepared`
and
- `submission-ready`

The platform now had realistic downstream child-intent preparation objects, but it still lacked a strong readiness gate saying whether a prepared child intent was actually eligible to be submitted in principle.

This was considered the ugliest problem because future contributors might otherwise confuse:
- “the system can prepare this order form”
with
- “the system is safe to send this order.”

That distinction became the reason for the next two architectural moves:
1. mature the currently integrated venues further
2. then build a first-class submission-readiness / execution-eligibility gate

---

## 30. Phase 4.1.1 — venue maturity before submission gating

Phase 4.1.1 was the corrective venue-maturity phase.

Its purpose was not to add routing or execution.
Its purpose was to stop treating the currently integrated venues as weak QA-only adapters and instead raise them to the highest realistic maturity for this stage.

Current integrated venues after 4.1.1:
- Hyperliquid
- Aster
- OKX
- Coinbase Advanced Trade

What 4.1.1 strengthened conceptually:
- explicit venue support levels
- venue-native prepared child-intent preview / preflight
- richer order constraints
- richer private-state/account-readiness surfaces
- clearer capability truth per venue
- more realistic meaning of “prepared”

This did **not** mean:
- live order submission
- cancel/amend
- routing
- CBBO
- fanout/splitting

It meant the current venues were now mature enough that the next phase could build a **submission-readiness / execution-eligibility gate** on top of something real rather than overcompensating for weak adapters.

Another important design principle from 4.1.1:
- current integrated venues should be treated as the most mature venues in the system for this stage
- future newly added venues may still begin life as `qa_read_only`

So the platform now supports a staged venue maturity model rather than one monolithic assumption.

---

## 31. What 4.2 must do

By the time 4.1.1 completed, the team’s recommendation was clear:

> The next step should be **submission-readiness / execution-eligibility gating**, not routing and not live execution.

Phase 4.2 must answer:
- is this prepared child intent actually eligible for submission in principle?
- if not, why not?
- if yes, what still blocks it because live submission is intentionally deferred?

The key distinctions 4.2 must make explicit are:
- venue/API semantic support
- adapter implementation support
- environment/account authorization
- phase-level live-submit deferral

That means the system must clearly distinguish:
- `prepared`
- `execution-eligible in principle`
- `phase-blocked`
- future `live-submission-enabled`

The team’s warning before 4.2:
- do **not** confuse prepared child intents with submission-ready child intents
- do **not** jump into routing
- do **not** jump into live execution
- do **not** assume current venue maturity means the gating problem is solved automatically

4.2 is the phase that should finally make the platform honest about what “ready” means.

---

## 32. Current strategic position before Phase 4.2

At this point, the platform is best understood as having these layers:

### Implemented / materially real
- exchange/data/state sync
- canonical instruments and venue mappings
- client/account/mandate/binding/component hierarchy
- deterministic indicators
- Money Flow strategy decisions
- mandate-level desired-trade planning
- source-policy-aware planning
- binding/account-targeted child-intent preparation for naturally binding-scoped actions
- venue-native order preview/preflight
- stronger multi-venue adapter maturity

### Not yet implemented
- full portfolio-grade risk engine
- submission-readiness / execution-eligibility gate
- best-binding selection
- routing / CBBO / account-group quote comparison
- multi-binding child-intent fanout
- live order submission
- cancel/amend
- multi-venue execution orchestration

This means the platform is no longer just:
- a signal engine
and not yet:
- a live execution system

It is now a serious **pre-execution trading platform substrate**.

---

## 33. Important reminders to the dev team before Phase 4.2

When beginning Phase 4.2, the dev team should remember:

1. `MandateDesiredTrade` is above child intents
2. `OrderIntent` is downstream child-intent territory
3. current venues are more mature now, but that does NOT mean they are live-enabled
4. the next problem is readiness semantics, not routing semantics
5. routing remains deferred
6. best-binding selection remains deferred
7. the platform still needs to distinguish:
   - source/planning venue
   - candidate routing venues later
8. generic platform-wide `sleeve` wording should keep shrinking over time
9. one process / one active mandate is still a practical limitation
10. the platform’s north star is still:
   - client-centric
   - mandate-driven
   - account-group-aware
   - multi-venue
   - signal + policy + routing + execution later

The most important immediate rule is:

> a prepared child intent must not be mistaken for a submission-ready child intent.

That rule should guide all 4.2 design decisions.

## 34. CODEX version of "explain the codebase" after Phase 4.2 (note added by project founder)

• This codebase is a trading platform scaffold that has grown into a real decision-and-preparation system, but it still stops short of live execution.

  At a high level, it does 4 things well right now:

  - ingests and normalizes exchange/account/market data
  - computes indicators and strategy decisions
  - converts approved strategy outcomes into mandate-level desired trades and, where appropriate, binding-scoped child intents
  - prepares venue-native order previews and evaluates submission readiness without actually sending orders

  The current architecture centers on:

  - Client
  - VenueAccount
  - StrategyMandate
  - MandateAccountBinding
  - StrategyComponentConfig

  That hierarchy is defined in core/domain/models.py. It means:

  - a client can own many exchange accounts
  - a mandate is one logical strategy umbrella
  - a mandate can bind many accounts
  - bindings are the future routing/account-group layer
  - components are strategy-family-specific configs; for Money Flow they still map to sleeve_15m, sleeve_1h, and sleeve_4h

  How the system flows

  1. Exchange adapters pull venue catalogs, account/private-state, and market-data reads.
     Main code: services/exchange/base.py, services/exchange/registry.py, venue adapters under services/exchange
  2. Market data and indicators are persisted, then the strategy layer evaluates them into StrategyDecision.
     Main code: services/market_data/service.py, services/indicators/service.py, services/strategy/engine.py, services/strategy/money_flow.py
  3. Planning converts convertible strategy decisions into MandateDesiredTrade.
     Main code: services/planning/service.py
  4. Risk evaluates the desired trade and either rejects it, approves it, or marks it routing-required.
     Main code: services/risk/engine.py
  5. Execution creates downstream OrderIntent only when a target binding/account is already known, derives a PreparedVenueOrder, and now evaluates execution readiness above that.
     Main code: services/execution/service.py

  That last split is important:

  - StrategyDecision is not an order
  - MandateDesiredTrade is not an order
  - OrderIntent is the future child-intent layer
  - PreparedVenueOrder is only a venue-native preview
  - ExecutionReadinessAssessment says whether that prepared intent is blocked, eligible in principle, or only phase-blocked

  What is implemented now

  - Hyperliquid, Aster, OKX, Coinbase Advanced Trade integrations
  - canonical instrument model and venue symbol mappings
  - persisted candles, indicators, signals, strategy decisions
  - Money Flow strategy family
  - desired-trade planning and first-pass approval
  - child-intent preparation for binding-scoped actions like reduce and close
  - venue-native preview/preflight
  - readiness gating above prepared intents
  - FastAPI inspection surface

  Main API is in apps/api/app/api/routes.py. Persistence is in db/models/trading.py. Config is in core/config/settings.py.

  What is intentionally not implemented

  - live order submission
  - cancel/amend
  - routing / best-binding selection
  - CBBO / cross-venue price aggregation
  - child-intent fanout across bindings
  - multi-venue execution orchestration

  So the platform is past “signal bot” stage, but it is still pre-execution. Today it can decide, approve, prepare, and assess readiness. It cannot send orders yet.

  If you want, I can give you one of these next:

  - a folder-by-folder repo walkthrough
  - a data model walkthrough
  - a “how one trade idea moves through the system” explanation
  - an investor-friendly explanation in plain English

## 35. Extra Explaining from CODEX (note added by project founder)

› - a folder-by-folder repo walkthrough
  - a data model walkthrough
  - a “how one trade idea moves through the system” explanation
  - an investor-friendly explanation in plain English

• Folder Walkthrough

  At a folder level, the repo breaks into a few clear layers:

  - apps/api is the control plane. It exposes inspection endpoints for mandates, venues, planning, readiness, and other operator-facing diagnostics. Start at apps/api/app/api/
    routes.py.
  - core/domain is the shared language of the system: instruments, venue/account truth, mandates, bindings, components, desired trades, order intents, prepared orders, and
    readiness outcomes. The center of gravity is core/domain/models.py and core/domain/enums.py.
  - core/interfaces defines service contracts. It tells you how exchange adapters, planning, risk, execution, portfolio, and strategy services are supposed to behave.
  - core/config holds environment-aware settings and policy toggles in core/config/settings.py.
  - db/models contains SQLAlchemy persistence for the whole platform state. db/models/trading.py is the main schema file.
  - db/migrations is the Alembic history showing how the platform evolved phase by phase.
  - services/exchange contains venue adapters. Hyperliquid is the oldest and most mature; Aster, OKX, and Coinbase Advanced Trade are integrated and execution-preparable but still
    not live-enabled.
  - services/market_data ingests and stores candles and market-state foundations.
  - services/indicators computes deterministic indicators.
  - services/strategy runs strategy logic. Money Flow is the current family in services/strategy/money_flow.py.
  - services/planning turns strategy decisions into mandate-level desired trades and routing candidates.
  - services/risk performs first-pass approval/rejection over desired trades.
  - services/execution does child-intent preparation, venue-native order preview/preflight, and execution-readiness assessment. It still does not submit live orders.
  - services/portfolio loads account truth: balances, positions, orders, and related snapshots.
  - tests is phase-oriented. The test names mirror the rollout history, which is useful because the architecture has been hardened incrementally.

  Data Model Walkthrough

  The core business hierarchy is:

  - Client
  - VenueAccount
  - StrategyMandate
  - MandateAccountBinding
  - StrategyComponentConfig

  That means one client can own many exchange accounts and many strategy umbrellas. One mandate can span many accounts through bindings. One account can also participate in many
  mandates. That is the future routing shape.

  The trade lifecycle models now split cleanly:

  - StrategyDecision: strategy-layer output, not an order
  - MandateDesiredTrade: approved mandate-level desired action, still not an order
  - OrderIntent: downstream child-intent territory for one binding/account
  - PreparedVenueOrder: venue-native preview of what that child intent would look like
  - ExecutionReadinessAssessment: evaluates whether that prepared child intent is blocked, phase-blocked, or eligible in principle

  Supporting truth models matter too:

  - canonical instruments and symbol mappings separate internal identity from venue-native symbols
  - venue accounts remain the boundary for balances, positions, open orders, fills, and snapshots
  - mandate market-data source policy separates planning/source venue from future routing venues
  - routing candidates and quote snapshots are derived planning objects, not final routing decisions

  If you want the shortest possible summary: the data model now separates “what the strategy wants” from “which account might eventually send it.”

  How One Trade Idea Moves Through the System

  Here is the current flow.

  1. Market data is pulled from a venue adapter and normalized into canonical instrument and candle records.
  2. Indicators are computed deterministically from stored market data.
  3. The strategy layer evaluates those indicators and emits a StrategyDecision.
  4. Planning checks whether that decision is convertible. If it is, it creates a MandateDesiredTrade.
  5. Risk evaluates that desired trade. It can reject it, approve it, or say it is routing-required.
  6. If the action is already naturally account-specific, like reduce or close, the execution layer can create an OrderIntent for the specific binding/account.
  7. That child intent is converted into a PreparedVenueOrder, which is a venue-native request preview with preflight checks.
  8. Phase 4.2 then evaluates execution readiness above that prepared order and tells you whether it is:
      - blocked by venue
      - blocked by adapter
      - blocked by environment or policy
      - phase-blocked
      - eligible for submission in principle

  What does not happen yet:

  - no routing across bindings
  - no best-binding selection
  - no live order submission
  - no cancel/amend path

  So the system can now decide, approve, prepare, and evaluate readiness, but it still stops before actual execution.

  Investor-Friendly Explanation

  In plain English, this is no longer a simple “trading bot.” It is the foundation of a real trading platform.

  What it already does:

  - connects to multiple exchanges
  - understands market data and account state
  - calculates strategy signals
  - turns those signals into structured trade plans
  - checks whether those plans are valid for a specific venue/account
  - prepares the exact order shape each exchange would need
  - tells the operator why an order is or is not eligible to be sent

  What it deliberately does not do yet:

  - it does not send live orders
  - it does not route trades across venues
  - it does not auto-split orders across multiple accounts

  That restraint is a strength, not a weakness. The team is building the dangerous parts last.

  Why that matters commercially:

  - the platform is already shaped for many clients, many accounts, and many venues
  - it has an audit trail for decisions and readiness
  - it is designed so future execution and routing can be added without redesigning the system again
  - it is reducing operational risk before touching live capital

  The simplest investor summary is:

  This codebase is a multi-venue trading platform that already knows how to observe markets, make structured trade decisions, translate them into venue-specific order previews, and
  evaluate execution readiness, but it is intentionally stopping one step before live order submission until the final gating and execution layers are complete.

---

## 36. Phase 4.3 — first attempt at truthful live submission

Phase 4.3 was the first phase that tried to move the platform from:
- prepared child intent
- and execution-readiness assessment

into:
- actual venue submission
- and persisted `SubmittedOrder` truth.

The intended goal was correct:
- keep mandate-scoped `OPEN` above routing
- only submit binding/account-targeted child intents
- preserve the layer split:
  - `StrategyDecision`
  - `MandateDesiredTrade`
  - `OrderIntent`
  - `PreparedVenueOrder`
  - `ExecutionReadinessAssessment`
  - `SubmittedOrder`

The team agreed that this was the right next architectural step.

However, the first 4.3 review found that the code was overstating what had actually been implemented.

The core problem was not the lifecycle model.
The lifecycle model was mostly right.
The problem was execution truth.

The review found two major issues:

1. submit paths were being described as “real” even though some venue-specific auth/signing behavior was still not convincingly implemented
2. submission was still too tied to venue-global integration context instead of being fully and truthfully `VenueAccount`-targeted

The team’s conclusion at that time was:
- good architectural direction
- but not yet truthful enough to approve as a real submission phase.

This became an important lesson:

> The platform must not claim submission support merely because it can preview an order, generate headers, and POST a payload. Submission support must be truthful about venue auth/signing semantics and about which exact account is being targeted.

That was the reason a follow-up correction phase was requested.

## 37. Phase 4.3.1 — corrective attempt on truthful submission and account targeting

Phase 4.3.1 attempted to fix the two main 4.3 review issues.

The handoff claimed that:
- venue-specific submit paths were now truthful for the current venue set
- Binance and Kraken were added to the same maturity branch
- submission was now truly `VenueAccount`-targeted end-to-end
- the code no longer depended on one venue-global integration context for execution truth

The actual review found that 4.3.1 did make meaningful progress:
- Binance and Kraken adapters were added
- same-venue multi-account targeting was tested
- the generic base submit path no longer pretended to be sufficient on its own
- the system was still preserving the correct mandate -> child-intent -> submitted-order layering

But the team still found a deeper issue:

At least some of the “truthful submit path” claims appear to still run ahead of the actual code reality.

The most important examples were:
- Coinbase Advanced Trade authentication appeared to use a custom Bearer-token construction in code, while current official Coinbase docs describe request authentication around per-request JWT generation with CDP key material
- Hyperliquid signing still appeared too hand-rolled and too far from the official SDK-oriented signing model, which the docs strongly recommend because there are multiple signing schemes and field-order/signing details are easy to get wrong

There was also an architectural concern around credential handling:
- `credentials_ref` / `wallet_ref` are named as references
- but the code path can still use them directly as if they were actual secret material

That may be temporarily workable in tests and local environments, but it is not yet a clean long-term secret-resolution model.

So the team’s practical view after reviewing 4.3.1 was:
- the platform still preserves the right boundaries
- the submission architecture direction is correct
- but the implementation may still be overstating how truthful some venue submit paths really are

This is a subtler issue than “submission exists or not.”
It is a truthfulness issue.

And truthfulness matters a lot here because the platform is already trying to distinguish:
- prepared
- eligible
- submitted

If the actual venue auth/signing semantics are not right, then a submitted order path is not really “true execution support” yet.

## 38. The architectural lesson from 4.3 / 4.3.1

The key lesson from these phases is:

> A multi-venue platform cannot treat “we know how to format an order request” as the same thing as “we have a truthful live-capable submission path.”

For a submit path to be truthful, it must satisfy all of the following:
- the lifecycle boundary is correct
- the intent is binding/account-targeted
- the adapter understands the venue’s actual authentication/signing model
- the actual targeted account context is used
- exchange/account truth is preserved in `SubmittedOrder`
- the platform does not overstate what is implemented in docs/tests/capabilities

The review also reaffirmed another important point:

> The platform is still not ready for routing, CBBO, or multi-binding fanout merely because basic submit paths exist or almost exist.

Submission comes before routing.
Truthful submission comes before smart routing.

## 39. Current caution before moving deeper into execution phases

The project is much stronger now than it was in the early Money Flow / Hyperliquid-first stages.

But the closer the platform gets to real execution, the more important this principle becomes:

> capability claims must be narrower and more honest, not broader and more optimistic.

The current standing caution for future phases is:
- do not confuse preview with live readiness
- do not confuse “likely works” with “truthfully implemented against venue auth/signing reality”
- do not let one integration-level credential context leak back into a system that is supposed to be truly `VenueAccount`-targeted
- do not let docs get ahead of code in execution semantics

The team still believes the long-term direction is correct:
- client-centric
- mandate-driven
- multi-account
- multi-venue
- signal + policy + desired-trade + child-intent + readiness + submitted-order + later routing/execution

But the closer the platform moves toward live behavior, the harsher the truth standard must become.

That is the current reminder to future us.


## 40. Phase 4.3.2 — execution-truth narrowed but not yet fully accepted

Phase 4.3.2 was the next corrective step after the first live-submission attempt and its follow-up review.

The intended goal of 4.3.2 was:
- fix the worst submission-truth issues
- keep submission truly `VenueAccount`-targeted
- make current venue submit-path claims more honest
- avoid drifting into routing or execution orchestration too early

The handoff for 4.3.2 claimed that the current venue set was now much safer because:
- submit-path claims were tied to real venue-local auth/signing behavior
- execution context was truly `VenueAccount`-targeted
- credential-reference labels were no longer being treated as if they were the secret material themselves

The review concluded that 4.3.2 was a meaningful improvement, but still not fully acceptable.

The most important blocker the team found was:

> for several venues, the payload representation used for signing still did not clearly match the exact payload representation being sent on the wire.

This is subtle, but very important.

Examples of why that matters:
- signing a form-encoded string but sending JSON
- signing a canonical JSON string but sending a differently shaped JSON body
- building auth/signing truth but still having transport truth drift

The team considered that a P0 execution-truth issue, because at this stage the platform is no longer just shaping child intents — it is trying to cross into truthful submission capability.

So 4.3.2 was not treated as a failure of direction.
It was treated as a reminder that:

> preview truth, auth truth, signing truth, payload truth, and account-targeting truth all have to align before the platform can honestly claim a venue has a real submission path.

That lesson is one of the most important execution-side lessons so far.

## 41. Manual credential validation after 4.3.2

A practical milestone happened around this point:
real credentials were added locally for:
- OKX
- Coinbase Advanced Trade
- Hyperliquid

After fixing local config issues, the developer was able to confirm:

- OKX authentication worked and the balance endpoint returned a valid response
- Coinbase authentication worked and the accounts endpoint returned valid account data
- Hyperliquid account-state lookup worked and the signing context appeared healthy

Important caveat:
these checks validated:
- authentication
- read paths
- signing context sanity

They did **not** validate:
- actual order submission
- exact signed-payload vs transmitted-payload fidelity
- full live venue execution truth

This mattered because it reduced uncertainty around auth/bootstrap, but it did not fully eliminate the need for one more narrow corrective execution-truth phase.

The team’s practical takeaway was:

- broad auth/bootstrap rework was probably no longer necessary
- but a final narrow submit-path truth phase still was

That was the reason for the revised, narrower Phase 4.3.3 prompt.

## 42. Phase 4.3.3 — the narrowed execution-truth phase

The revised 4.3.3 was intentionally much narrower than the earlier corrective prompt.

Its purpose was not to:
- redesign auth
- add routing
- add cancel/amend
- add orchestration
- broaden the execution feature set

Its purpose was only to:
- make sure signed payload equals transmitted payload
- make sure submission stays truly `VenueAccount`-targeted
- make sure docs and capability surfaces stop overclaiming
- make sure tests prove the exact execution-truth issue rather than only proving that “a header exists” or “a signature exists”

The team specifically wanted 4.3.3 to focus on:
- Hyperliquid
- Aster
- OKX
- Coinbase Advanced Trade
- Binance
- Kraken

and to do one thing well:

> if a venue is claimed as submission-capable at the implemented scope, that claim must be honest all the way down to the wire representation.

This phase was explicitly **not** allowed to turn into:
- routing
- best-binding selection
- CBBO
- child-intent fanout
- cancel/amend
- post-submit orchestration

The team’s mindset here was important:

> before the platform can become smart about where to route, it has to become boringly truthful about whether it can even submit correctly to one venue/account at a time.

That is exactly the kind of discipline we want to keep.

## 43. Current architectural reminder before deeper execution phases

At this point in the project, the platform should be understood like this:

### Strategy and planning side
- `StrategyDecision`
- `MandateDesiredTrade`

### Execution-preparation side
- `OrderIntent`
- `PreparedVenueOrder`
- `ExecutionReadinessAssessment`

### Exchange/account truth side
- `SubmittedOrder`

And the following are still intentionally separate and still deferred:
- routing
- best-binding selection
- CBBO / cross-venue quote comparison
- multi-binding fanout
- full execution orchestration

This matters because future contributors may be tempted to think:
- “submission works, so routing is next”

But the team’s actual view is stricter:

> truthful submission must come before routing, and post-submit lifecycle correctness must come before smart-routing ambition.

That is the order that protects the platform.

## 44. The execution-side standard is now much harsher than before

Early in the project, a lot of correctness work focused on:
- instrument identity
- stale data
- idempotency
- exchange truth vs attribution truth
- hierarchy cleanup
- planning boundaries

Now, as the platform approaches real submission, the standard gets tougher.

The team now expects execution-side truth to include all of the following:

- account-targeted execution context
- venue-accurate auth/signing semantics
- signed payload matching transmitted payload
- docs and capability claims staying behind code truth, not ahead of it
- explicit separation of:
  - prepared
  - eligible
  - submitted

This is a healthy sign.

It means the platform is no longer being judged like:
- a prototype bot
and is instead being judged like:
- a future real trading platform

That is uncomfortable sometimes, but it is exactly the right direction.

## 45. Updated pre-routing reminder to future us

The temptation will keep growing to say:

- “we already have signals”
- “we already have desired trades”
- “we already have child intents”
- “we already have venue previews”
- “we already have readiness”
- “we almost have submit paths”
- “so let’s just jump to routing”

The team’s reminder is:

> No.
> Routing should not be built on top of shaky submission truth.

Before routing becomes the next real frontier, the platform should be able to say with confidence:

- this venue/account was the one we intended to target
- this was the exact payload we signed
- this was the exact payload we sent
- this is the truthful submission result
- this is the truthful exchange/account state that came back

Only then does routing become worth the complexity it will introduce.

That remains the current execution-side north-star reminder.


## 46. Phase 4.3.3 — exact submit-body fidelity fixed

Phase 4.3.3 was the narrow corrective phase that focused on one execution-truth issue only:

> the exact payload representation used for signing had to match the exact payload representation sent on the wire.

This phase did **not** try to add routing, cancel/amend, orchestration, or new execution features.
It only fixed the last major submission-truth problem left after 4.3.2.

What changed conceptually:
- exact JSON/form submission helpers were added so venue adapters could transmit the same representation they sign
- Aster, Binance, OKX, Coinbase Advanced Trade, and Kraken were updated to stop relying on generic request serialization for signed submissions
- same-venue account targeting remained intact
- docs and capability wording were narrowed to “code/test-proven submit-path truth” instead of implying broader live validation than the platform actually has

The team review found that the original 4.3/4.3.1/4.3.2 progression had been mostly correct architecturally, but too optimistic semantically.
4.3.3 was the phase that finally made the platform’s submission claims narrower and more honest.

The key lesson from 4.3.3 is:

> A submission path is not truthful unless the venue-local auth/signing model, the targeted account context, and the exact wire payload all agree.

That is a harder standard than simply generating a signature or successfully calling a mocked transport.

## 47. What 4.3.3 does **not** mean

Even after 4.3.3, the platform is still **not** a routing engine and still **not** a full live execution system.

Still intentionally deferred:
- routing
- best-binding selection
- CBBO / cross-venue quote comparison
- child-intent fanout across bindings
- cancel/amend
- deeper post-submit orchestration and reconciliation
- portfolio-grade execution/risk deepening

So 4.3.3 should be understood as:
- submission truth cleanup
not as:
- the beginning of smart order routing

## 48. Updated reminder before Phase 4.4

The team’s current view is:

- if 4.3.3 is accepted, the next phase can deepen **post-submit lifecycle handling**
- but it is still too early to jump to routing

Why?
Because routing should sit on top of:
- truthful submit paths
- truthful account targeting
- clear submitted-order truth
- clearer post-submit state progression

not on top of partially-deepened execution semantics.

So the practical order remains:

1. truthful submission
2. post-submit lifecycle and reconciliation depth
3. cancel/amend groundwork
4. only then later routing / best-binding / CBBO / fanout

That remains the current execution-side north-star reminder.

## 49. Phase 4.3.3 — accepted execution-truth cleanup

After review, the team accepted 4.3.3 as the phase that finally cleared the remaining execution-truth blocker from the 4.3 submission work.

What 4.3.3 proved or corrected at the accepted architectural level:
- signed payload representation now matches transmitted payload representation for the implemented submit-capable scopes
- same-venue account targeting remained intact
- submission claims were narrowed to what is actually code/test-proven rather than what might be true in a broader live-production sense
- the platform no longer needed another narrow “submit truth” correction phase before moving on

This did **not** mean the platform had become a routing system.
It meant the platform now had a firmer execution boundary underneath the later routing ambitions.

The team’s acceptance logic here mattered:
- 4.3 and 4.3.1 were about crossing into submission
- 4.3.2 and 4.3.3 were about making that crossing honest
- only after that honesty was restored could the next execution-lifecycle phase be justified

The most important acceptance takeaway was:

> The platform can now talk about submit-capable venue paths for the implemented scope without quietly relying on mismatched signing/wire-format behavior.

That is a subtle improvement, but it is the kind of subtlety that separates a real trading platform from a demo.

## 50. What Phase 4.4 should now mean

Phase 4.4 is **not** the routing phase.

The team’s current view is that the correct next step after 4.3.3 is:
- post-submit lifecycle handling
- rejection/recovery semantics
- richer submitted-order state progression
- reconciliation depth
- cancel/amend groundwork

In other words, Phase 4.4 should answer:

> once a submitted order exists, how does the platform continue telling the truth about what happened next?

That is the right next question because the system now has:
- strategy decisions
- desired trades
- child intents
- prepared venue orders
- execution readiness
- submitted orders

But it still needs a stronger answer for:
- acknowledgment vs rejection
- ambiguous submit outcome
- partial fill vs full fill
- venue-side disappearance / missing order on reconciliation
- recovery semantics

The point is to deepen execution truth, not to jump over it.

## 51. Current position before routing

The founder’s instinct to push toward routing makes sense.
That is where many of the platform’s real-world competitive tests will eventually happen.

But the team’s current position is still:

> not yet.

The platform is now much stronger on:
- strategy truth
- planning truth
- risk boundary truth
- child-intent truth
- preview/preflight truth
- readiness truth
- submission truth

What is still missing before routing becomes the right frontier:
- deeper submitted-order lifecycle progression
- stronger rejection/recovery semantics
- better post-submit reconciliation depth
- cancel/amend groundwork
- more mature execution-quality market data for later cross-venue comparison

So the execution-side staircase still looks like:

1. truthful submission
2. post-submit lifecycle / reconciliation depth
3. cancel/amend groundwork
4. later routing / best-binding / CBBO / fanout

This is frustrating sometimes, but still the right order.

## 52. Editorial note on what was intentionally kept in memory

At this point, the memory file contains:
- historical architecture phases
- accepted architectural pivots
- founder notes
- CODEX explanatory notes
- execution-boundary lessons

The team reviewed whether old sections should be removed.
Current decision:
- no historical sections were removed yet
- the older sections still help explain *why* later corrections were necessary
- some earlier “future phase” sections are now historically outdated, but they remain useful as a record of what the team thought at the time

So this file is still intentionally a **chronicle**, not a polished spec.

If the founder later wants a second file such as:
- `money_flow_current_state.md`
or
- `money_flow_operator_brief.md`
that would be the right place to create a cleaner, non-historical summary.

For now, keeping the full historical arc has more value than pruning it aggressively.

## 53. Phase 4.4 / 4.4.1 — submitted-order lifecycle became real

Phase 4.4 was the point where the platform stopped treating `SubmittedOrder` as a static “submit happened” record and started treating it as a real exchange/account-truth lifecycle.

What 4.4 added conceptually:
- richer submitted-order states
- explicit reconciliation state
- lifecycle-event history
- ambiguity handling
- rejection handling
- cancel/amend groundwork

The key architectural move was:
- `SubmittedOrder` became a living post-submit truth layer
- not just a submission receipt

However, the first 4.4 review still found an important truth problem:
- Hyperliquid could still mask a partial fill behind open-order presence
- submit-time rejection could still leave the child-intent layer too optimistic

Phase 4.4.1 corrected that:
- Hyperliquid now combines open-order truth and fill truth before finalizing lifecycle state
- partially filled while still open is no longer flattened into generic `acknowledged`
- immediate venue rejection no longer leaves the child intent pretending it was successfully submitted

The main lesson from 4.4 / 4.4.1 was:

> truthful submission is not enough;
> the platform also needs truthful post-submit state progression.

That was the point where the team started treating:
- `submitted`
- `acknowledged`
- `partially_filled`
- `filled`
- `rejected`
- `unknown`
as real load-bearing distinctions rather than cosmetic status labels.

## 54. Phase 4.5 / 4.5.1 — cancel truth and recovery guidance

Phase 4.5 deepened the post-submit layer again.

It added:
- broader venue-by-venue reconciliation beyond the Hyperliquid-first path
- explicit recovery recommendations
- truthful live cancel for the supported venue/account scopes
- amend groundwork
- API/operator inspection for recovery and actionability
- stronger test isolation from local `.env`
- repo-side review-bundle workflow

The key new execution idea was:
- post-submit lifecycle should not just say what happened
- it should also say what the next appropriate recovery action is

But 4.5 initially still had an important truth issue:
- some venue cancel responses were treated as if “cancel accepted” meant “canceled is now final truth”

That mattered especially for:
- OKX
- Coinbase Advanced Trade

because their cancel APIs can acknowledge or accept the request without that immediately meaning the order is finally canceled.

Phase 4.5.1 fixed that by introducing explicit intermediate states:
- `cancel_requested`
- `cancel_acknowledged`

and requiring later reconciliation to finalize:
- `canceled`

The key lesson from 4.5 / 4.5.1 was:

> cancel support is not truthful unless the platform distinguishes:
> cancel requested,
> cancel accepted,
> and cancel fully reconciled.

At this point the platform gained a much stronger execution vocabulary:
- submitted
- acknowledged
- partially filled
- filled
- rejected
- cancel requested
- cancel acknowledged
- canceled
- unknown
- reconciliation state
- recovery recommendation

without collapsing them into each other.

## 55. Phase 4.6 / 4.6.1 — bounded recovery execution and the first real amend path

Phase 4.6 was the first time the platform started doing more than just *describing* what recovery should happen.

It added:
- bounded post-submit recovery execution
- same-target recovery actions such as:
  - `reconcile_now`
  - `cancel_now`
  - `retry_same_target`
- one truthful native amend path:
  - OKX limit-order amend in the currently implemented scope
- stronger venue-by-venue lifecycle parity
- account-targeted recovery execution
- API surfaces for recovery and amend actions

This was a meaningful architectural shift:
the platform moved from:
- “here is the recovery recommendation”

toward:
- “here is a bounded recovery action the system can actually execute”

Then 4.6.1 forced one more important correction:
- same-target retry had been too generic for strict client-order-id reuse venues
- Aster and Binance needed fresh retry client order ids
- retry could not silently reuse the original deterministic submission id

So 4.6.1 made retry truth venue-specific:
- Aster retry now uses a fresh retry client order id
- Binance retry now uses a fresh retry client order id
- OKX retry remained fine as implemented
- same-venue account targeting stayed intact

The key lesson from 4.6 / 4.6.1 was:

> recovery execution must be as venue-specific and truthful as submission itself.

That means:
- retry cannot be generic unless venue semantics allow it
- amend cannot be claimed unless the venue/account/product scope really supports it
- recovery execution must stay:
  - same-target
  - same-venue
  - same-account
  - below routing

## 56. Phase 4.7 / 4.7.1 — deeper amend/cancel/reconcile truth below routing

Phase 4.7 was the first execution-depth phase after 4.6/4.6.1 that tried to make the current venue set feel more even below routing.

Its purpose was not to add:
- routing
- best-binding selection
- CBBO
- child-intent fanout
- mandate-scoped open target selection

Instead, it deepened the post-submit layer across the current six-venue matrix:
- Hyperliquid
- Aster
- OKX
- Coinbase Advanced Trade
- Binance
- Kraken

What changed conceptually:
- Hyperliquid was revisited explicitly instead of being left behind as a holdout
- Hyperliquid gained truthful cancel plus native limit-order amend in the currently proven perpetual scope
- Coinbase gained truthful native amend in the current spot limit-order scope
- Kraken cancel truth remained explicitly non-terminal until later reconciliation
- Aster reconciliation now preserved canceled/expired-after-partial-fill truth more honestly
- recovery execution stayed below routing and moved one step deeper without turning into hidden target reselection or hidden failover

Then 4.7.1 corrected the remaining truth-surface problems:
- persisted fill merge no longer overwrites terminal or cancel-pending truth
- Hyperliquid capability/status surfaces now reflect real cancel/amend support
- public cancel and amend capability truth is explicit rather than collapsed into one fake combined capability flag

The key lesson from 4.7 / 4.7.1 was:

> execution truth includes both lifecycle behavior and capability surfaces.
> It is not enough for the adapter to do the right thing if the public model still says the wrong thing.

## 57. Canonical docs became explicit around 4.7

Around the 4.7 period, the team finally had to be explicit about documentation hierarchy.

The correct rule is now:
- `docs/architecture.md` is the canonical architecture doc
- `docs/strategy.md` is the canonical strategy/execution-boundary doc

Historical or refresh drafts can be useful during editing, but they should not compete with the canonical docs once the platform is this deep into execution work.

The accepted reminder from this period is:

> preserve historical context in the memory file,
> but keep one clear canonical architecture doc and one clear canonical strategy doc for the current boundary.

That matters because the platform is no longer just evolving strategy semantics.
It is evolving:
- execution truth
- venue parity
- cancel/amend depth
- recovery behavior
- later orchestration

and those surfaces need one clear source of current truth.

## 58. Phase 4.8 / 4.8.1 — polling-first private-state truth below routing

Phase 4.8 did not add routing or new recovery actions.
It deepened the **private-state substrate** below routing.

What 4.8 added conceptually:
- explicit private-state truth surfaces for:
  - session state
  - private-state summary
  - open orders
  - recent fills
  - open positions
- explicit distinction between:
  - semantic stream support
  - adapter-implemented stream support
  - actual lifecycle update mode
- stronger direct account-targeted private-state reads where the venue/account scope supports them

It also stayed conservative:
- no adapter-level user-stream parity was added
- lifecycle updates remained polling-first
- no routing or cross-target orchestration was added

However, the first 4.8 review found a real truth problem:
- venue-polled private open orders were being surfaced as if they were `SubmittedOrder`s
- private-state source reporting could still overstate `venue_query` when runtime auth/path actually fell back to persistence
- `session-state` wording could still overclaim private venue/account session depth

Phase 4.8.1 fixed those boundary issues:
- venue-private open orders got their own truth surface
- fake `submitted_order_id="live-*"` fabrication was removed
- optional linkage to a real platform `SubmittedOrder` became explicit instead of implied
- runtime source reporting became truthful per surface
- `session-state` was narrowed explicitly to adapter/runtime bookkeeping

The key lesson from 4.8 / 4.8.1 was:

> venue-private order truth is not the same thing as platform-submitted order truth.

That distinction is now load-bearing below routing.

## 59. Phase 4.9 — deeper polling-first private-state parity

Phase 4.9 continued the same below-routing direction without adding new orchestration behavior.

Its main purpose was to deepen direct private order/account-state parity where some surfaces still depended on persistence fallback.

What changed conceptually:
- Hyperliquid gained direct account-targeted private open-order truth instead of persistence fallback
- Aster and Binance gained direct order-scoped private fill reads for same-target retry safety
- same-target retry became safer because it could now consult stronger live private-state evidence before proceeding
- semantic stream support remained separate from actual adapter implementation
- lifecycle mode remained explicitly polling-first

The platform still did **not** add:
- user-stream parity
- new recovery actions
- routing
- cross-target orchestration

So 4.9 should be understood as:
- deeper private-state substrate
not as:
- broader orchestration

The key lesson from 4.9 was:

> polling-first private-state truth can still materially improve execution safety and venue parity,
> even before user-stream parity exists.

## 60. Current state after 4.9 — are we ready for Phase 5 routing?

After 4.9, the platform is significantly deeper below routing than it was even a few phases ago.

What the platform now has materially and truthfully:
- canonical strategy/planning/risk/execution boundary
- truthful scoped submit paths
- truthful cancel lifecycle
- a real submitted-order lifecycle
- bounded same-target recovery execution
- venue-private order truth separate from submitted-order truth
- stronger direct private-state parity
- native amend only where code/test-proven:
  - Hyperliquid
  - OKX
  - Coinbase Advanced Trade

What it still does **not** have evenly enough for routing to feel mature:
- broad adapter-level user-stream parity
- fully even private order/account-state depth across all six venues
- broad native amend parity for Aster, Binance, and Kraken
- richer same-target orchestration beyond the current bounded action set
- routing-grade market-data / execution-quality depth
- best-binding / CBBO / cross-binding execution substrate

So the current team view is:

> The platform is close enough that routing feels like the next major frontier,
> but not mature enough below routing for a broad Phase 5 routing rollout to be the best immediate next move.

The more disciplined path is:

1. finish one more serious below-routing execution-depth pass
2. then begin routing in a controlled Phase 5 sequence

That likely means:

### Next execution-depth work before routing
- deeper adapter-level user-stream or session parity where provable
- broader direct account-state parity where persistence fallback still remains
- broader native amend parity only where truthful
- richer same-target orchestration below routing

### Then controlled routing phases
- Phase 5.0:
  - routing substrate only
  - no full smart order routing yet
  - explicit target-selection boundary
  - no hidden fanout
- Phase 5.1+:
  - best-binding selection
  - venue/account eligibility filtering
  - quote comparison / execution-quality inputs
  - later CBBO-style support
  - later child-intent fanout where one desired trade must become more than one child intent

The standing reminder remains:

> routing should sit on top of a stable, honest submit / reconcile / cancel / amend / recovery substrate.
> It should not be used to compensate for incomplete execution truth underneath.

## 61. Phase 4.10 / 4.10.1 / 4.10.2 — final below-routing execution-truth cleanup before routing substrate

Phase 4.10 was the final major below-routing execution-depth pass before the platform began Phase 5 routing substrate work.

It deepened the execution substrate without adding routing:
- Hyperliquid gained stronger direct private account-state truth, including direct open-position polling where account context exists
- Aster and Binance retry safety became more honest by using scoped private fill evidence instead of treating broad same-symbol history as exact order truth
- retry evidence became more careful about ambiguity, time-bounds, and query failure
- the platform remained polling-first and did not claim adapter-level user-stream parity

Phase 4.10.1 fixed three execution-truth issues:
- Hyperliquid no longer fabricates `mark_price=0` when `markPx` is missing
- mark price is derived from `positionValue / abs(szi)` only when that derivation is truthful
- otherwise mark price remains `None`
- Aster and Binance retry fill checks became submitted-at-bounded so stale pre-submit same-symbol fills do not incorrectly block retry
- Binance private-trade query failure now blocks retry before a new submitted order can be created

Phase 4.10.2 then closed the remaining semantic leak:
- the unsafe convenience wrapper that could drop evidence scope was removed
- ambiguous Aster/Binance account+symbol fill evidence now remains inside `SubmittedOrderPrivateFillEvidence`
- ambiguous evidence can block retry but cannot masquerade as exact submitted-order fill truth
- exact exchange-order-id evidence remains `order_scoped`

The key lesson from 4.10.x was:

> below-routing execution truth is not just about having more data;
> it is about preserving evidence scope so ambiguous venue-private evidence does not become fake submitted-order truth.

After 4.10.2, the team considered the below-routing substrate honest enough to begin Phase 5 as a controlled routing-substrate sequence.

## 62. Phase 5.0 — non-executing routing assessment substrate

Phase 5.0 began routing work, but deliberately did **not** build smart order routing.

Its purpose was to create the first routing substrate above the accepted execution layer.

Phase 5.0 added:
- routing request/input modeling
- persisted `RoutingAssessment`
- persisted `RoutingCandidateAssessment`
- candidate enumeration over mandate account bindings
- explicit eligible / ineligible binding outcomes
- explicit reason codes and missing-data reporting
- operator-facing routing assessment APIs

The most important boundary:

> `MandateDesiredTrade` with `routing_required` can now produce a routing assessment,
> but no target is selected, no child intent is created, and no execution occurs.

Phase 5.0 did not implement:
- best-binding selection
- price ranking
- CBBO
- fanout
- target choice
- child-intent creation
- submission

This was the correct first routing phase because it made the routing problem inspectable before making it actionable.

## 63. Phase 5.1 / 5.1.1 — explicit non-executing target choice

Phase 5.1 added a controlled target-choice layer on top of routing assessments.

It allowed an explicit operator-requested choice of one eligible candidate binding from a valid routing assessment.

Important properties:
- target choice is persisted as audit metadata
- target choice is not auto-generated by an optimizer
- target choice is non-executing
- `MandateDesiredTrade` remains `routing_required`
- no `OrderIntent` is created yet
- no submission occurs

Phase 5.1.1 hardened target-choice truth by revalidating the source desired trade immediately before recording successful target choice.

It blocks target choice if the desired trade is no longer:
- present
- `routing_required`
- mandate-scoped
- `open`
- untargeted

The key lesson from 5.1 / 5.1.1 was:

> target choice must be explicit and auditable,
> but it is still not execution.

## 64. Phase 5.2 / 5.2.1 — target choice to one child intent conversion

Phase 5.2 added the first controlled conversion from one recorded routing target choice into exactly one binding/account-targeted `OrderIntent`.

This was the first time a mandate-scoped open could move below the routing boundary into a specific account target.

Strict limits remained:
- one target choice becomes at most one child intent
- no fanout
- no splitting
- no readiness assessment yet
- no prepared order yet
- no submission
- no target reselection
- no best-binding logic

Phase 5.2.1 hardened lineage:
- target choice -> routing assessment linkage
- desired trade ownership/source lineage
- selected binding ownership
- selected venue account consistency
- symbol mapping consistency

The key lesson from 5.2 / 5.2.1 was:

> converting a routed target into a child intent is a serious boundary crossing,
> so lineage validation must be treated as load-bearing infrastructure.

## 65. Phase 5.3 / 5.3.1 — routed child-intent preparation and readiness inspection

Phase 5.3 allowed converted routed child intents to enter the existing prepared-order preview and execution-readiness paths.

This reused the already hardened execution substrate rather than inventing a separate routed execution path.

Important behavior:
- routed child intents are detected through route-origin provenance
- route lineage is revalidated before preview/readiness
- prepared order preview gets routed lineage attached
- readiness assessment records routed lineage
- readiness remains phase-blocked with `routed_submission_deferred`
- no submission occurs

Phase 5.3.1 hardened routed readiness lineage further:
- stale desired-trade state blocks readiness
- stale target choice blocks readiness
- stale binding/account truth blocks readiness
- mismatched provenance blocks readiness
- symbol mapping drift blocks readiness

The key lesson from 5.3 / 5.3.1 was:

> routed child intents should use the same execution-readiness machinery,
> but only after proving their route lineage is still current and coherent.

## 66. Phase 5.4 / 5.4.1 — explicit routed submission handoff, still not SOR

Phase 5.4 added the first explicit routed submission handoff.

This was not auto-submit and not smart routing.
It allowed an already converted routed child intent to submit only through the existing explicit submit path and only when both gates are enabled:
- normal live submission gate
- routed submission phase gate

Important properties:
- no auto-submit
- no target reselection
- no fanout
- no CBBO
- no price/quality scoring
- no route executor
- no cross-binding recovery
- no cross-venue failover

The submitted order records routed lineage inside submitted-order raw payload so routed origin can be audited later.

Phase 5.4.1 fixed a truth-surface problem in the routed submission gate:
- if routed submission is blocked by the phase gate, the child intent remains `prepared`
- the block is recorded as `last_submission_block`
- it is not treated as a submission failure
- preview payload now reports the routed/live gate truth accurately

The key lesson from 5.4 / 5.4.1 was:

> explicit routed submission can exist before smart routing,
> but only if it is gated, non-automatic, lineage-checked, and honest about deferral.

## 67. Current Phase 5 state after 5.4.1 — before Phase 5.5

The platform now has a controlled routing sequence:

1. `MandateDesiredTrade` becomes `routing_required`
2. routing assessment enumerates eligible/ineligible bindings
3. target choice records one explicit operator-requested candidate
4. conversion creates exactly one binding/account-targeted child intent
5. routed child intent can enter preparation/readiness inspection
6. explicit routed submission can occur only when both routed and live submission gates are enabled
7. routed submitted-order lineage is present in raw payload, but not yet exposed as a first-class inspection surface

What is still **not** present:
- smart order routing
- best-binding selection
- CBBO
- scoring/ranking
- fanout/splitting
- automatic route execution
- target reselection
- cross-binding/cross-venue recovery
- route executor framework

The correct next phase is Phase 5.5:

> routed submitted-order lineage inspection.

The goal of 5.5 should be to make routed submitted orders easy to inspect and audit without changing execution behavior.

That means:
- expose routed vs non-routed submitted-order classification
- expose routing assessment id, target choice id, selected binding/account, selected venue, selected exchange symbol, readiness id, and gate facts where present
- do not infer or fabricate lineage for non-routed orders
- do not add orchestration, routing, fanout, target reselection, or smart routing

The current team stance:

> Phase 5 is now safely inside routing territory,
> but still not full SOR.
> Keep building inspectable routing lineage and audit truth before adding route intelligence.

## 68. Phase 5.5 — routed submitted-order lineage inspection

Phase 5.5 made routed submitted orders inspectable without changing execution behavior.

Before this phase, routed submitted-order lineage existed mostly inside `SubmittedOrder.raw_payload["routed_submission"]`. That was acceptable for the first routed-submission handoff, but too hidden for operators and future reviewers.

Phase 5.5 added read-only routed lineage inspection on submitted-order API surfaces.

What became inspectable:
- desired trade key
- routing assessment id
- routing target choice id
- selected binding/account
- selected venue
- selected exchange symbol
- readiness evaluation id
- no-auto-submit / no-fanout / no-scoring / no-target-reselection boundary facts

Important boundary:
- non-routed submitted orders do not fabricate routed lineage
- malformed routed payloads are bounded instead of crashing list/detail responses
- no new endpoint expansion, auto-submit, target reselection, fanout, scoring, CBBO, route executor behavior, or exchange behavior was added

The key lesson from 5.5 was:

> routed lineage must be operator-inspectable before routing behavior becomes more powerful.

## 69. Phase 5.6 — routed order-shape policy became explicit

Phase 5.6 started addressing an important routed-execution concern:

> a routed child intent should not silently inherit an unexamined order shape forever.

Earlier routed conversion used the current default:
- market order
- no limit price
- reduce_only false

Phase 5.6 made that default explicit through a `RoutedOrderShapeDecision` instead of leaving it as hardcoded silent behavior.

It also hardened malformed routed lineage handling:
- missing routed lineage fields are tracked
- malformed routed lineage fields are tracked
- submitted-order list/detail responses stay bounded and non-crashing

Important boundary:
- LIMIT routed order-shape policy remained deferred in 5.6
- slippage guards remained deferred
- market-data-derived limit-price sources remained deferred
- no target reselection, fanout, scoring, CBBO, auto-submit, route executor, or exchange changes were added

The key lesson from 5.6 was:

> even if the platform still defaults to market order shape, that default must be named, audited, and visible.

## 70. Phase 5.7 / 5.7.1 — routed post-submit lifecycle and retry lineage

Phase 5.7 made post-submit lifecycle and actionability route-aware.

That means routed submitted orders, routed recovery recommendations, routed recovery execution responses, and actionability responses can now expose selected route context without forcing operators to parse raw payloads.

What became inspectable:
- desired trade
- routing assessment
- target choice
- selected binding/account
- selected venue
- selected exchange symbol
- readiness id
- routed order-shape policy facts
- same-target / same-account / same-venue recovery boundaries

Important boundary:
- routed recovery/actionability remains same-target only
- route lineage does not authorize target reselection
- no alternate binding recovery
- no alternate venue recovery
- no fanout
- no route executor
- no auto-submit

Phase 5.7.1 then fixed routed retry lineage:
- same-target routed retry now preserves routed lineage on the retried `SubmittedOrder`
- non-routed retry still does not fabricate routed lineage
- duplicated routed lineage parsing was consolidated into `core/domain/routed_lifecycle.py`

The key lesson from 5.7 / 5.7.1 was:

> routed lineage must survive post-submit lifecycle actions, especially retry, without turning retry into hidden routing.

## 71. Phase 5.8 / 5.8.1 / 5.8.2 — routed order-shape policy v2

Phase 5.8 added explicit routed order-shape policy input for controlled target-choice-to-child-intent conversion.

The conversion path now accepts optional:
- `MARKET`
- `LIMIT`

Current behavior:
- omitted input remains backward-compatible:
  - market
  - no limit price
  - reduce_only false
- explicit LIMIT requires:
  - a positive limit price
  - modeled order-type support from the candidate assessment
- invalid or unsupported policy blocks before child-intent creation

Blocked cases include:
- missing limit price for LIMIT
- malformed price
- zero or negative price
- unsupported order type
- MARKET with limit price
- reduce_only true for mandate-scoped OPEN
- unsupported LIMIT order type on the selected candidate

Phase 5.8.1 hardened non-finite LIMIT price validation:
- NaN / sNaN / Infinity / -Infinity block before child-intent creation
- API non-finite values are rejected as client errors rather than internal server errors
- no child intent, prepared order, readiness evaluation, or submitted order is created

Phase 5.8.2 cleaned the reason surface:
- malformed/non-finite LIMIT inputs no longer claim `limit_price_explicit`
- valid finite LIMIT prices still record `limit_price_explicit`
- blocked policy facts stay clearer and less contradictory

Important idempotency behavior:
- repeated conversion remains idempotent
- a different policy after conversion cannot create a second child intent from the same target choice
- the existing child intent is preserved rather than silently mutated

Important boundary:
- this is still not best-binding
- still not price discovery
- still not CBBO
- still not slippage-guarded routing
- still not route execution
- still no fanout
- still no auto-submit

The key lesson from 5.8 / 5.8.1 / 5.8.2 was:

> routed order shape can become explicit before the platform is ready for smart routing, but price inputs must be decimal-safe, finite, and truthfully described.

## 72. Phase 5.9 / 5.9.1 / 5.9.2 — routed reconciliation and lifecycle-event audit truth

The originally discussed Phase 5.9 topic was route-readiness / routing-data sufficiency. The implemented 5.9 work instead focused on routed reconciliation and lifecycle-event audit visibility.

What 5.9 added:
- routed reconciliation responses preserve existing routed audit lineage
- lifecycle-event responses expose routed lifecycle context
- non-routed events do not fabricate route context
- malformed routed payloads remain bounded

Phase 5.9.1 fixed a collision problem:
- existing platform `raw_payload["routed_submission"]` remains authoritative
- adapter/update payloads with colliding `routed_submission` keys cannot overwrite or mutate platform route lineage

Phase 5.9.2 fixed the inverse collision problem:
- update payloads cannot create routed lineage on non-routed submitted orders
- top-level `routed_submission` remains reserved for platform-authored routed audit lineage only
- event raw payload may retain adapter collision facts, but lifecycle-event routed context still derives from the associated `SubmittedOrder` truth

Important boundary:
- route lineage is audit metadata
- it is not execution instruction
- it is not target reselection
- it is not route scoring
- it is not route execution

The key lesson from 5.9 / 5.9.1 / 5.9.2 was:

> routed lineage must be protected as platform-authored audit truth, especially when venue reconciliation payloads contain colliding keys.

## 73. Phase 5.10 — routing-substrate closeout regression

Phase 5.10 closed the routed-substrate phase with an end-to-end regression pass rather than new behavior.

The closeout regression exercises the accepted routed chain:

`MandateDesiredTrade -> RoutingAssessment -> RoutingTargetChoice -> OrderIntent -> PreparedVenueOrder -> ExecutionReadinessAssessment -> SubmittedOrder -> actionability / recovery / reconciliation / lifecycle events`

It verifies:
- typed routed lineage agrees across submitted-order detail/list, lifecycle context, actionability/recovery, reconciliation, and lifecycle events
- the selected same-venue secondary account is the only submitted target
- update payload `routed_submission` collisions remain non-authoritative
- no extra child intents or submitted orders are created
- no fanout, allocation, scoring, CBBO, route plan, target reselection, route executor behavior, or auto-submit appears

Phase 5.10 is best understood as:
- substrate diligence
- not new routing behavior

The key lesson from 5.10 was:

> closing Phase 5 means proving the substrate stayed bounded, not adding smart routing.

## 74. Current Phase 5 state after 5.10 — controlled routed execution substrate

After Phase 5.10, the platform has a controlled routed flow:

`StrategyDecision -> MandateDesiredTrade -> RoutingAssessment -> RoutingTargetChoice -> OrderIntent -> PreparedVenueOrder -> ExecutionReadinessAssessment -> SubmittedOrder`

The routed flow now supports:
- non-executing routing assessment
- operator-requested target-choice audit records
- exactly-one child-intent conversion in the normal controlled flow
- explicit routed order-shape policy input and decision output
- routed readiness inspection
- explicit gated routed submission of an already selected child intent
- routed submitted-order lineage inspection
- route-aware same-target post-submit lifecycle/actionability inspection
- routed same-target retry lineage preservation
- routed reconciliation and lifecycle-event audit visibility
- route-lineage collision protection

Still not implemented:
- smart order routing
- system-generated target recommendation
- best-binding selection
- CBBO
- venue ranking
- execution-quality scoring
- fanout / split allocation
- target reselection
- cross-binding recovery
- cross-venue failover
- route executor behavior
- auto-submit

The current team view:

> Phase 5 successfully built a controlled routed execution substrate. It is not yet SOR. That is good.

## 75. Important review caution before Phase 6

The architecture review found one important gap before Phase 6 should make system-generated target recommendations:

> the originally planned routing data sufficiency / route-readiness audit layer is not present yet.

Phase 5.9 became routed reconciliation/lifecycle audit work rather than a route-readiness audit. That work was useful, but it does not answer the question:

> what facts must be present before the platform is allowed to recommend a target?

Before Phase 6 recommends a binding/account/venue, the platform should have an inspectable route-readiness audit that checks facts such as:
- market-data freshness
- quote source confidence
- fee availability
- venue/account state visibility
- product support
- order-shape support
- private-state visibility
- source-policy compatibility
- missing data that prevents safe recommendation

This should still not be a selector. It should be an audit layer that Phase 6 can depend on.

The standing caution is:

> do not begin controlled target recommendation until route-readiness/data-sufficiency facts exist and are inspectable.

That does not invalidate Phase 5. It means Phase 6 should begin with a route-readiness audit step, or there should be a tiny Phase 5 closeout hotpatch to add that audit before Phase 6.

## 76. Phase 5.10.1 / 5.10.2 — route-readiness audit completed the missing Phase 5 gate

After the Phase 5 closeout review, the main missing piece before Phase 6 was clear:

> the platform needed a non-selecting route-readiness / data-sufficiency audit before it could recommend any target.

Phase 5.10.1 added that missing audit layer.

The route-readiness audit can inspect a routing-required desired trade or an existing routing assessment and classify candidate readiness facts without selecting, ranking, scoring, routing, converting, preparing, or submitting.

It introduced a useful distinction:

- ready for recommendation = data-sufficient under the current audit facts
- recommendation = a later step
- target choice = still a separate later operator/action layer
- child intent / readiness / submitted order = still downstream execution

The audit checks facts such as:
- desired-trade validity
- mandate/binding/account truth
- symbol and product support
- quote availability and freshness
- private-state visibility
- fee and balance availability
- order-shape support
- missing / stale / unavailable / unsupported / policy-blocking facts

Phase 5.10.2 then corrected audit truth:
- quote facts derived from existing routing-assessment snapshots are labeled as `derived_from_existing_assessment`, not fresh venue query
- missing or invalid desired-trade side / quantity blocks readiness
- malformed, non-finite, zero, or negative quote prices are reason-coded before any notional math
- default MARKET order-shape policy is labeled defaulted rather than explicit

The key lesson from 5.10.1 / 5.10.2 was:

> a target recommendation needs an audit of data sufficiency first.
> readiness audit is not a selector; it is the gate before the selector.

## 77. Phase 6.0 / 6.0.1 — controlled single-ready-candidate target recommendation

Phase 6.0 introduced the first system-generated target recommendation layer.

This is still **not** smart order routing.

The only recommendation policy currently implemented is:

> `single_ready_candidate_only`

That means:
- exactly one ready candidate from a route-readiness audit can produce a recommendation
- zero ready candidates blocks
- multiple ready candidates block
- no ranking
- no scoring
- no best-binding
- no CBBO
- no fanout
- no route plan
- no target-choice creation
- no child-intent creation
- no readiness creation
- no submitted-order creation
- no auto-submit

Phase 6.0.1 then added current-truth hardening:
- recommendation success revalidates the current `StrategyMandate`
- missing or inactive mandate blocks
- stale desired-trade symbol drift blocks
- inactive or non-trading symbol mapping blocks
- audit-level blockers remain visible even when zero-ready or multiple-ready candidate status is the primary outcome

The important architectural boundary is:

`RouteReadinessAudit -> RoutingTargetRecommendation`

not:

`Recommendation -> TargetChoice -> ChildIntent -> Submit`

The recommendation is only an inspectable recommendation record. It does not execute anything.

The key lesson from 6.0 / 6.0.1 was:

> controlled target recommendation can begin without becoming SOR,
> but only if it is non-executing, policy-narrow, and revalidates current truth.

## 78. Current caution after Phase 6.0.1

The platform has now crossed from pure routing substrate into the first controlled recommendation layer.

That is a meaningful milestone.

But the current recommendation policy is intentionally narrow:
- it recommends only when there is exactly one ready candidate
- it does not decide between multiple candidates
- it does not score candidates
- it does not compare venues
- it does not evaluate execution quality
- it does not create downstream target choices or orders

The architecture review still sees three important hardening areas before recommendation-driven workflow becomes more powerful:

1. Recommendation freshness should account for the underlying quote observation time, not only audit record age.
2. Route-readiness audits should expose recommendation linkage truth once recommendations are created, or otherwise avoid misleading `recommendation_created` semantics.
3. Recommendation-to-target-choice conversion, when introduced later, must remain explicit/operator-reviewed and must not auto-convert silently.

The current north-star reminder is:

> Phase 6 recommendation is allowed to be a controlled policy layer.
> It must not become hidden best-binding, hidden scoring, or hidden route execution.

## 79. Phase 6.0.2 / 6.1 / 6.1.1 — recommendation truth and explicit priority policy

After Phase 6.0 / 6.0.1 introduced the first controlled recommendation layer, more truth-hardening was needed before recommendation could be trusted as a durable platform artifact.

Phase 6.0.2 tightened recommendation-time truth:
- recommendation freshness now depends on the candidate quote observation time, not just the age of the audit record
- the source route-readiness audit now reflects that a recommendation record was actually created from it
- recommendation therefore became less like a loose cached opinion and more like a bounded recommendation artifact with explicit freshness semantics

Phase 6.1 then added the first optional multi-candidate recommendation policy:
- `explicit_binding_priority`

This is still not best-binding selection.
It is not venue ranking.
It is not scoring.

It is simply:
- an operator-configured binding preference
- lower positive integer wins
- missing priorities block
- malformed priorities block
- ties block

That matters because the platform still refuses to fake route quality.
If there are many acceptable candidates, the system will only break the tie if a declared operator policy says how.

Phase 6.1.1 then hardened that policy surface:
- bounded `policy_name` input
- explicit priority clearing semantics
- omitted priority updates preserve current values instead of erasing them silently

The key lesson from 6.0.2 / 6.1 / 6.1.1 was:

> recommendation can become slightly richer without becoming smart routing,
> but only if policy remains explicit, inspectable, and operator-owned.

## 80. Phase 6.2 / 6.2.1 / 6.2.2 — explicit recommendation acceptance into target choice

Phase 6.2 added a very important workflow step:

> recommendation is not action.
> recommendation must be explicitly accepted before it becomes a routing target choice.

That preserved a healthy boundary.

What 6.2 added:
- explicit operator-triggered recommendation acceptance
- successful recommendation -> exactly one non-executing target choice
- current-truth and quote-freshness revalidation before acceptance
- no child intent yet
- no prepared order yet
- no readiness yet
- no submitted order yet

That means the system can now:
- produce a recommendation
- but still require a separate act before it becomes a chosen route

Phase 6.2.1 then hardened same-audit idempotency:
- one route-readiness audit cannot create many accepted target choices through duplicate successful recommendations
- repeated successful same-audit acceptance returns the original target choice
- the original acceptance timestamp is preserved instead of being overwritten

Phase 6.2.2 then tightened that boundary further:
- blocked recommendations cannot “inherit” accepted-looking truth merely because the same audit once produced a successful acceptance
- successful and blocked recommendation outcomes now stay more semantically separate

The key lesson from 6.2 / 6.2.1 / 6.2.2 was:

> target choice must remain a deliberate acceptance boundary,
> not a side effect of recommendation history.

## 81. Phase 6.3 / 6.4 / 6.4.1 — recommendation-backed conversion and readiness

Phase 6.3 connected recommendation-backed routing to the existing execution substrate.

It added:
- explicit conversion from an accepted recommendation-backed target choice into exactly one routed child `OrderIntent`
- preservation of recommendation, audit, target-choice, selected binding/account/venue/symbol, and order-shape lineage in child-intent provenance
- idempotent reuse of the same child intent on repeated conversion attempts from the same accepted recommendation path

This was a major step because Phase 6 now had:
- recommendation
- acceptance
- conversion

without yet collapsing into submission.

Phase 6.4 then allowed those recommendation-backed child intents to flow into:
- existing prepared-order preview
- existing execution-readiness inspection

Again, the architecture discipline was good:
- recommendation-backed execution reused existing substrate
- it did not invent a parallel execution system

Phase 6.4.1 then hotpatched a subtle but important truth issue:
- routed order-shape policy drift vs current child-intent shape now blocks preview/readiness
- stale stored quote observations at this layer now block readiness with the correct `quote_stale_at_readiness` semantics

The key lesson from 6.3 / 6.4 / 6.4.1 was:

> recommendation-backed workflow can move into execution inspection
> without bypassing the normal prepared/readiness boundary,
> but only if recommendation lineage and order-shape policy are revalidated again.

## 82. Phase 6.5 / 6.6 — manual routed-flow harness and timing visibility

Phase 6.5 and 6.6 did not deepen live execution semantics much, but they were still valuable.

Phase 6.5 added:
- a manual routed-flow inspection harness
- a JSON trace of the controlled routed workflow
- explicit operator/developer ability to walk the current chain through readiness without default submission

That matters because the platform had become deep enough that a manual end-to-end inspection tool was useful for:
- humans
- debugging
- demos
- operational understanding

Phase 6.6 then added:
- local per-step timing visibility
- top-level timing summary
- step elapsed times
- continued no-default-submission behavior

The team should remember:
this timing is:
- local harness/service timing
not:
- production routing latency
not:
- route executor telemetry
not:
- exchange network latency

The key lesson from 6.5 / 6.6 was:

> once the routed substrate becomes deep enough, a controlled manual harness is useful,
> but it must remain visibly a harness, not hidden automation.

## 83. Phase 6.7 / 6.10.1 / 6.10.2 / 6.10.3 — explicit single-target recommendation-backed routed execution closeout

Phase 6.7 through 6.10 completed the first recommendation-backed single-target execution path.

This is still not smart routing.
But it is much more than non-executing substrate.

What the platform can now do in the accepted controlled path:
- recommendation
- acceptance
- target choice
- child-intent conversion
- prepared-order preview
- execution-readiness inspection
- explicit gated submitted-order creation for that selected target
- recommendation-aware post-submit lifecycle/actionability/reconciliation inspection
- routed workflow aggregation by desired trade

That is a serious milestone.

Then 6.10.1 / 6.10.2 / 6.10.3 tightened the dangerous edge cases around submission:

### 6.10.1
- added a persistence-backed submit lease
- concurrent explicit submit calls for one child intent cannot both reach adapter submission before a `SubmittedOrder` exists
- first/latest submitted-order provenance stays separate and explicit

### 6.10.2
- if the adapter submit returns but local `SubmittedOrder` persistence fails,
  the system records terminal uncertainty:
  - `adapter_submit_persistence_unknown`
- later submits for that child intent block with manual reconciliation required

### 6.10.3
- if the adapter call may already have started but no reliable return path exists,
  the system records:
  - `adapter_submit_may_have_started`
- later submits again block with manual reconciliation required

This is one of the strongest execution-discipline parts of the whole project.

The key lesson from 6.7 through 6.10.3 was:

> explicit recommendation-backed single-target execution can be allowed before SOR,
> but only if ambiguity, concurrency, and lineage are handled more conservatively than most teams would tolerate.

That is exactly the right instinct for a real trading platform.

## 84. Current state after Phase 6.10.3 — Phase 6 is complete, but Phase 7 must stay disciplined

At this point, Phase 6 has gone well beyond routing substrate.
It now includes:

- route-readiness/data-sufficiency audit
- non-executing recommendation
- recommendation acceptance
- accepted-target conversion
- recommendation-backed preview/readiness
- explicit gated recommendation-backed submission
- recommendation-aware post-submit lifecycle inspection
- routed workflow aggregation
- submit ambiguity and concurrency hardening

That means Phase 6 is materially complete as a:

> controlled single-target recommendation-backed execution phase

The platform still does **not** have:
- best-binding selection
- scoring
- CBBO
- fanout
- target reselection
- route executor behavior
- auto-submit
- true smart order routing

That is good.

The next phase should not throw away that discipline.

Phase 7 should be about:
- controlled automation around the already-built single-target recommendation-backed path
- operator approval and dry-run remaining first-class
- strong reversibility and explicit config gates
- no hidden smart routing
- no fake “optimal execution” language
- no fanout
- no target reselection

The standing reminder is:

> Phase 7 should automate a narrow, truthful path the platform already understands.
> It should not use automation as an excuse to jump into full SOR before the data, controls, and operator tooling are ready.

## 85. Phase 7.0 through 7.6 — controlled automation stays same-target and approval-bound

Phase 7 began correctly: it added automation substrate without pretending the platform has smart routing.

The completed Phase 7 progression is:

- Phase 7.0: non-executing routing automation policy and dry-run plans.
- Phase 7.1: durable approval records and reversible gates.
- Phase 7.1.1: expiry, stale-lineage, and active-scope uniqueness hardening.
- Phase 7.1.2: approvals only for currently approvable steps, not manual-only or dry-run-only states.
- Phase 7.2: one approval-consuming action hook for recommendation acceptance into a target choice.
- Phase 7.2.1: target-choice creation/reuse and approval consumption happen coherently in one commit.
- Phase 7.3: one approval-consuming action hook for target-choice conversion into one child intent.
- Phase 7.3.1: direct negative coverage for blocked states and wrong lineage around target-choice conversion.
- Phase 7.4: one approval-consuming action hook for prepared-order preview/readiness inspection.
- Phase 7.5: one approval-consuming action hook for submitted-order handoff through the existing explicit submit path.
- Phase 7.5.1: `consumption_pending` approval truth when a submitted order exists but approval consumption fails afterward.
- Phase 7.6: closeout safety regression and docs alignment only, with no new production behavior.

The accepted Phase 7 action boundaries are:

```text
RoutingTargetRecommendation -> RoutingTargetChoice
RoutingTargetChoice -> OrderIntent
OrderIntent -> PreparedVenueOrder preview -> ExecutionReadinessAssessment
ExecutionReadinessAssessment -> SubmittedOrder handoff
```

Each boundary consumes its own active, non-expired, non-revoked, non-stale-lineage, current-scope approval for exactly that stage.

Phase 7.5 is the only Phase 7 stage that reaches the existing explicit submit path, and only for the exact already-ready child intent. Phase 7.5.1 makes post-submit approval-consumption failure inspectable as `consumption_pending`; repeat calls must reuse existing submitted-order truth rather than submit again.

Phase 7 still does **not** create:

- route plans
- route executor state
- fanout/split allocations
- ranking/scoring/CBBO artifacts
- target reselection
- best-binding selection
- cross-venue retry
- broad auto-submit

The key lesson from Phase 7 is:

> controlled automation is acceptable only when every transition is explicit,
> approval-scoped, current-lineage-bound, same-target, and separately testable.
> It must not become a hidden route executor.

## 86. Obsidian is now the strategic brain; repo docs remain code truth

Phase 7.3 also moved full strategic memory into the Obsidian vault:

```text
money-flow/Project_Memory/money_flow_project_memory.md
```

The repo-root `money_flow_project_memory.md` is now only a pointer.

Future agents should start with:

- `money-flow/00_Money_Flow_Command_Center.md`
- `money-flow/01_Current_Phase.md`
- `money-flow/05_Agent_Coordination.md`
- `money-flow/Project_Memory/money_flow_project_memory.md`

The Obsidian vault is for founder intent, long-horizon memory, phase context, decisions, and agent/subagent coordination.

It is not a substitute for:

- `CHANGELOG.md`
- `REPO_TREE.md`
- `KNOWN_ISSUES.md`
- `TODO.md`
- `README.md`
- `docs/architecture.md`
- `docs/strategy.md`

The coordination rule is important: agents should update their own row in `money-flow/05_Agent_Coordination.md` before substantial work and after handoff, and they should not overwrite another agent's active row without an agreed handoff.

## 87. Strategic position after Phase 7.6

Phase 7 is now accepted complete.

The platform has a full controlled routed automation chain:

- dry-run automation plans
- durable approval records
- recommendation acceptance approval hook
- target-choice conversion approval hook
- preview/readiness approval hook
- submitted-order handoff approval hook
- `consumption_pending` approval truth
- closeout regression proving same-target, current-lineage, no-SOR behavior

This is powerful, but it is also operationally complex.

The project should not move into smart routing yet. The next bottleneck is operator visibility:

- Can an operator quickly see where one desired trade is in the chain?
- Can they see what was recommended and accepted?
- Can they see which approvals exist and why one is active, consumed, revoked, expired, stale-lineage, or `consumption_pending`?
- Can they see readiness and submit blockers without parsing raw payloads?
- Can they see adapter-submit uncertainty and submit lease state?
- Can they tell what manual action is safe, unsafe, or unknowable?

That is the right next problem.

## 88. Phase 8.0 — operator observability and manual-resolution inspection

Phase 8.0 implemented the right next step: read-only operator observability and manual-resolution inspection over the accepted Phase 7 chain.

Phase 8.0 adds a read-only operator workflow summary by desired trade. It shows:

- current routed workflow artifacts
- approval states and approval-gate truth
- manual-resolution requirements
- submitted-order handoff safety facts
- submit lease and concurrency facts
- blocking and uncertainty reason codes
- next safe operator action, where knowable

The important design decision was to keep Phase 8.0 read-only. It does not add manual-resolution marker mutation, administrative cleanup endpoints, or any trading action from inspection.

Phase 8.0 is not:

- smart routing
- best-binding selection
- CBBO
- ranking/scoring
- fanout
- target reselection
- route executor behavior
- cross-venue recovery
- new exchange behavior
- new action stages
- auto-submit
- auto-resolution of trading uncertainty

The one important scope lesson remains:

> Manual-resolution markers are mutation and should be treated as risky control-plane work.
> Phase 8.1 should design them explicitly if needed, with actor stamps, timestamps, reason codes, audit visibility, and a hard separation between operator acknowledgement and exchange/account truth.

Phase 8.0 makes the platform safer before future SOR by making uncertainty and operator responsibility visible without pretending to resolve it.

## 89. Phase 8.0.1 — Obsidian memory baseline cleanup

Phase 8.0 left the working tree dirty because an earlier Obsidian brain refresh had updated the full project memory and many Obsidian notes before Phase 8.0 was implemented.

The cleanup decision is:

- accept the earlier Obsidian refresh as intentional strategic-memory work
- update stale "Phase 8.0 proposed" wording to reflect that Phase 8.0 is now implemented
- keep repo-root `money_flow_project_memory.md` as a pointer only
- keep full strategic memory in `money-flow/Project_Memory/money_flow_project_memory.md`
- record the cleanup in Obsidian coordination/decision notes and repo operational docs

This cleanup adds no product behavior. It is workflow hygiene so future agents start from a clean Phase 8.0/8.0.1 baseline before Phase 8.1.

## 90. Phase 8.0.2 — operator-summary submit-lease truth

Phase 8.0.2 was a narrow truth hotfix on the read-only operator summary.

It fixed the case where an unexpired active child-intent submit lease existed but the operator summary could still make approval-gated submit look safe. After the hotfix, an active lease is surfaced as `submission_in_progress`, repeat-submit safety is blocked with explicit reason truth, and the next safe operator action does not present approval-gated submit as safe while a submission may already be in progress.

This changed no trading behavior. It did not add manual-resolution mutation, new action stages, route executor behavior, fanout, target reselection, broad auto-submit, or smart routing.

## 91. Strategy Validation became the current priority

After Phase 8.0.2, the project deliberately pivoted away from routing/SOR expansion and back to the core business question:

> Does Money Flow show enough evidence to justify paper-trading design?

This is why the SV track exists. Strategy Validation is not a side feature. It is the research-truth layer needed to prove or disprove whether Money Flow has edge before adding more trading workflow complexity.

The hard boundary for the entire SV track is:
- no Money Flow rule optimization unless a correctness bug is found
- no paper trading
- no live execution
- no routing or exchange-order behavior
- no treating backtest output as proof of profitability

## 92. SV1.0 through SV1.0.1 — first validation and report truth

SV1.0 added the first deterministic Money Flow backtest/reporting framework over persisted candles. It reuses the current Money Flow rules, computes indicators in memory, simulates research-only trades with explicit assumptions, and creates no live trading artifacts.

SV1.0.1 hardened report truth:
- fill timing is explicit
- same-candle close fills are labeled research-only and potentially optimistic
- next-candle open/close fills are supported
- closed-trade drawdown and mark-to-market drawdown are separated
- Markdown reports include assumptions, limitations, component metrics, trade summaries, and reason counts

This was the first step toward founder/operator evidence review rather than anecdotal strategy belief.

## 93. SV1.1 through SV1.2.1 — comparative, regime, coverage, and window truth

SV1.1 added comparative batch validation across explicit components, fill timings, symbols, date windows, fees, and slippage assumptions. It is descriptive only: it reports observed results and does not optimize or recommend a variant.

SV1.2 added data coverage and deterministic market-regime analysis. Regimes are descriptive labels derived from candle data, not strategy filters.

SV1.2.1 fixed load-bearing research-truth issues:
- all validation windows use candle closes in `(start_at, end_at]`
- adjacent windows do not double-count boundary candles
- expected close-slot coverage is aligned with that convention
- unaligned windows are warning-coded
- coverage cannot exceed 100%
- blocked runs remain visible in grouped comparisons

This window convention remains authoritative for all later campaign and evidence-pack work.

## 94. SV1.3 through SV1.4.1 — campaigns, evidence packs, review discipline, and write integrity

SV1.3 added named, repeatable Money Flow research campaigns and evidence packs. Campaign configs expand explicit symbols, components, fill timings, windows, fees, slippage, capital, and sizing through the existing batch runner and save normalized config, manifest, JSON, Markdown, and README outputs.

SV1.4 added canonical editable campaign configs, pre-run data-readiness audits, evidence-pack review checklists, and manual paper-trading readiness criteria. These criteria are founder/operator review aids only, not automated approval.

SV1.4.1 made evidence packs collision-safe. Repeated same-campaign same-timestamp runs no longer silently overwrite prior research records. The default policy writes a unique suffix, and manifests record requested/final run identity and collision truth.

## 95. SV1.5 through SV1.5.1 — historical-data readiness and import integrity

SV1.5 added historical-data readiness support:
- campaign `window_convention` metadata validation
- founder-readable Markdown readiness audits
- offline public CSV/JSON candle import/upsert tooling

SV1.5.1 hardened the import/config truth:
- contradictory inclusive-start window-convention text is rejected
- existing candle identity conflicts do not retarget symbol/instrument ids
- row duration must match the selected timeframe
- malformed, non-finite, zero, negative, or internally inconsistent OHLCV rows are rejected
- negative trade counts are rejected
- invalid files roll back without partial inserts or updates

The current candle model still lacks per-candle source provenance, so import source/provenance is summary-level unless a future schema phase adds import-batch linkage.

## 96. SV1.6 through SV1.7 — first evidence review and data-gap reporting

SV1.6 added the first canonical evidence-review summaries over the canonical BTC and multi-symbol campaign configs. It can generate collision-safe evidence packs only when data-readiness audits are clean, and otherwise reports insufficient data without treating missing data as a strategy failure.

SV1.7 added first-real DB/data gap reporting:
- sanitized DB URL/source
- DB reachability
- candle-table existence
- persisted candle count when available
- blocked campaign rows when DB/schema/candles are unavailable
- `partial_evidence_ready_with_data_gaps` for mixed outcomes

The local SV1.7 attempt did not generate real evidence packs because the default `postgres` host was unresolved and the reachable local Postgres endpoint did not contain the Money Flow `candles` table.

## 97. SV1.8 through SV1.8.1 — schema truth before evidence packs

SV1.8 made DB/schema/migration bootstrap truth explicit and added a `--db-status-only` evidence-review CLI path. The local check found the explicit `127.0.0.1:54322/postgres` target reachable in that phase, but unmigrated: no `alembic_version` and no `candles`.

SV1.8.1 added a hard schema gate:
- evidence packs require `migrated_schema_ready`
- Alembic migration truth must be current
- required `candles`, `instruments`, and `symbols` tables must exist
- a `candles` table alone is not enough
- top-level no-live/no-exchange flags aggregate from campaign results

This prevented the first real evidence packs from being generated from partial or unknown schema truth.

## 98. SV1.9 — intended DB target and candle import requirements

SV1.9 made first-real evidence status operationally precise.

Evidence-review DB status now reports:
- sanitized DB driver, host, port, name, and user
- target-role classification
- intended strategy-validation DB truth
- maintenance-database warnings
- required-table and migration status
- canonical candle import requirements for blocked/missing rows

The local SV1.9 probes generated no evidence packs:
- default intended `money_flow` DB target used unresolved host `postgres`
- explicit `127.0.0.1:54322/postgres` override was unreachable in that shell
- the explicit override is also a maintenance database target requiring operator confirmation

As of SV1.9.1, no first real canonical evidence packs had been generated yet. The blocker at that time was DB/schema/candle readiness, not a Money Flow strategy result.

## 99. SV1.9.1 — evidence-target truth, import timestamp truth, and memory governance

SV1.9.1 fixed trust issues before SV1.10 can attempt first real evidence packs:
- ambiguous/non-intended maintenance DB targets now block evidence generation by default
- `postgres`, `template0`, and `template1` are not accepted canonical evidence targets by default
- no DB-target override exists yet
- timezone-naive candle timestamps are rejected by default
- `--assume-naive-utc` is a non-default import override that records `timestamp_assumption=assume_naive_utc` and warning/source provenance
- override-derived imports should be treated as exploratory/non-canonical unless founder/operator review explicitly accepts them
- import summaries now include source label, path/name/hash, row counts, imported environment/venue/timeframe, timestamp assumption, and naive-override truth
- generated evidence packs, review outputs, import outputs, local candle files, and local DB artifacts are excluded from source/review bundles
- Obsidian command center, dashboard, timeline, roadmap, coordination, decision log, and this full project memory were refreshed through SV1.9

Routing/SOR expansion is not the current priority. The current priority is Strategy Validation evidence/data readiness.

Paper trading is not approved yet. The next safe step is to prepare a reachable migrated non-maintenance Money Flow DB, import or verify enough timezone-explicit BTC/ETH/SOL candles for canonical campaigns, and generate first real evidence packs only after DB target, schema, and data-readiness truth are clean.

## 100. SV1.12.x — public identity verified, partial candle files prepared

On 2026-05-05, a research-only data-preparation pass verified BTC, ETH, and SOL Hyperliquid perpetual USDC identity values against official public Hyperliquid docs and the public `meta` Info endpoint. The research manifest was updated with verified asset ids/meta indexes, `szDecimals`, quantity steps, derived price precision values, leverage, and margin table ids while keeping `operator_verified=false`, `is_strategy_eligible=false`, and `is_trading_eligible=false`.

The same pass queried public `candleSnapshot` for the canonical January 2026 windows. Hyperliquid public data produced complete local timezone-explicit CSVs for the 12 `1h` and `4h` BTC/ETH/SOL requirements under `/tmp/money-flow-sv112x-candles`. The six `15m` requirements remain missing because the public endpoint returned zero rows for those January 2026 15m windows, consistent with the public recent-candle limitation.

Guarded import is still blocked. Identity was not seeded because founder/operator approval was not supplied, and requirement-aware preflight for the 12 available files cannot pass against the intended DB until operator-verified BTC/ETH/SOL research identity rows exist. No candles were imported and no evidence packs were generated.

## 101. SV1.12.4 — public YTD/recent Hyperliquid campaign selected

The same day, the public-data plan changed because January 2026 15m candles were too old for public Hyperliquid `candleSnapshot`. January 2026 remains valuable as an archival/vendor/operator-data campaign, but it is no longer the public Hyperliquid first-evidence baseline.

The public first-evidence data plan now uses:

- BTC/ETH/SOL `1h` from `2026-01-01T00:00:00Z` to `2026-05-05T00:00:00Z`
- BTC/ETH/SOL `4h` from `2026-01-01T00:00:00Z` to `2026-05-05T00:00:00Z`
- BTC/ETH/SOL `15m` from `2026-03-15T00:00:00Z` to `2026-05-05T00:00:00Z`

The initially suggested `15m` start of `2026-03-14T00:00:00Z` still missed the first close slots, so the selected 51-day window starts on `2026-03-15T00:00:00Z`. All 9 selected public CSVs were produced locally under `/tmp/money-flow-sv1124-public-ytd-recent/csv` with timezone-explicit timestamps and exact local close-slot coverage.

Guarded import is still blocked. The intended DB lacks operator-verified BTC/ETH/SOL research identity rows, so requirement-aware preflight cannot pass yet. No identity was seeded, no candles were imported, no evidence packs were generated, and no paper/live trading boundary changed.

## 102. SV1.12.5 — supported venue public candle readiness

On 2026-05-06, the public-data-friendly YTD/recent candle plan was extended across all registry-supported venue adapters: Hyperliquid, Aster, Binance, OKX, Coinbase Advanced Trade, and Kraken. This remained research-only and used public endpoints/local files only.

Hyperliquid remains the nearest guarded-import path from SV1.12.4: 9 public BTC/ETH/SOL YTD/recent files exist locally, but operator-verified non-trading identity still needs founder/operator approval before preflight/import can pass. Aster and Binance produced 18 additional complete timezone-explicit native-trade-count candidate files under `/tmp/money-flow-sv1125-supported-venues-public/csv`, but requirement-aware preflight blocks because those venue identity rows are not verified/seeded in the intended DB.

OKX and Coinbase Advanced Trade produced complete close-slot OHLCV files for the selected windows, but their public candle payloads do not include trade count, so they are not canonical import-ready under the current CSV contract. Kraken public REST OHLC returned incomplete selected-window coverage, so Kraken needs archive/vendor/operator data for this plan.

No identity was seeded, no candles were imported, no evidence packs were generated, and no paper/live trading boundary changed. The next Strategy Validation bridge should seed Hyperliquid non-trading research identity first if the founder/operator approves it; broader venue comparison requires Aster/Binance identity verification, OKX/Coinbase trade-count sourcing or a contract decision, and Kraken archive/vendor/operator coverage.
