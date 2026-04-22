# KNOWN_ISSUES

Last reviewed: `2026-04-22T19:49:16Z`

## Open Items

### K-001

- `status`: `open`
- `area`: `execution-quality market data`
- `summary`: `Top-of-book and order-book depth interfaces exist, but no live implementation is wired yet.`
- `impact`: `Phase 4+ execution-quality sizing/slippage logic will need additional market-data work.`

### K-002

- `status`: `open`
- `area`: `portfolio attribution`
- `summary`: `Exchange-truth positions are preserved correctly, but the full strategy-attribution engine is still deferred.`
- `impact`: `Risk and execution policy work must continue to treat attribution overlays as incomplete.`

### K-003

- `status`: `open`
- `area`: `Hyperliquid classification`
- `summary`: `Builder-deployed / HIP-3 classification is explicit and isolated, but still depends partly on venue metadata quality.`
- `impact`: `Future venue-policy work should keep this classification reviewable and test-covered.`

### K-004

- `status`: `open`
- `area`: `operational docs discipline`
- `summary`: `Phase 3.2 adds governance checks, and the Phase 6.3 source-control baseline now tracks repo memory on `master`, but future contributors must keep the docs updated for the process to remain useful.`
- `impact`: `This is operational rather than code risk; drift will accumulate if changelog and repo-memory updates are skipped. Review bundles, handoff archives, local secrets, virtualenvs, caches, local database/runtime state, and logs are intentionally excluded from source control.`

### K-005

- `status`: `open`
- `area`: `runtime orchestration`
- `summary`: `The active runtime is now mandate-first, but one process still targets one selected mandate at a time.`
- `impact`: `Phase 4 must keep risk and intent work scoped to the selected mandate and should not assume multi-mandate orchestration exists yet.`

### K-006

- `status`: `open`
- `area`: `routing architecture`
- `summary`: `Phase 5.0 adds non-executing routing assessments for routing-required mandate-scoped opens, Phase 5.1 adds operator-requested non-executing target-choice audit records for one eligible candidate from an assessment, Phase 5.2 can convert one explicit valid target choice into exactly one binding/account-targeted child intent, Phase 5.2.1 hardens assessment / desired-trade / binding lineage validation before conversion, Phase 5.3 lets converted routed child intents enter existing prepared-order preview/readiness inspection after route-lineage revalidation, Phase 5.3.1 hardens that readiness boundary, Phase 5.4 adds a controlled explicit routed submission handoff, Phase 5.5 through Phase 5.9.2 expose and protect routed submitted-order lineage/lifecycle/reconciliation audit metadata, Phase 5.10 closes the routed lifecycle substrate, Phase 5.10.1 adds non-selecting route-readiness/data-sufficiency audits before recommendation, Phase 5.10.2 hardens route-readiness audit truth, Phase 6.0.0 adds controlled non-executing target recommendation only for exactly one ready candidate from an existing audit, Phase 6.0.1/6.0.2 harden recommendation current-truth and quote-freshness checks, Phase 6.1 adds optional deterministic `explicit_binding_priority` recommendation using nullable binding-level operator preference, Phase 6.1.1 bounds recommendation policy input plus explicit priority clearing semantics, Phase 6.2 adds explicit operator-triggered acceptance of a successful recommendation into exactly one non-executing target choice, Phase 6.2.1 hardens same-audit acceptance idempotency plus original acceptance timestamp truth, Phase 6.2.2 prevents blocked recommendations from using same-audit idempotency to appear accepted, Phase 6.3 explicitly converts an accepted recommendation-backed target choice into exactly one routed child `OrderIntent`, and Phase 6.4 lets that child intent use existing prepared-order preview/readiness inspection with recommendation/audit/quote/current-truth revalidation. Multiple ready candidates still block by default; explicit priority can recommend only one lower-priority ready binding and blocks on missing/malformed priority, ties, or stale selected-candidate quote observations. Recommendation acceptance, accepted target-choice conversion, and recommendation-backed readiness revalidate current truth before new artifacts or eligible readiness; duplicate successful same-audit acceptance returns the original target choice, and duplicate conversion returns the existing child intent. No live routing execution beyond submitting the already selected child intent, best-binding selection, CBBO logic, child-intent fanout, auto-submit, target reselection, route executor behavior, cross-binding recovery, cross-venue retry/failover, or mandate-scoped OPEN bypass exists yet.`
- `impact`: `Mandate-scoped opens now pass honestly through routing-required plus routing assessment / route-readiness audit / optional non-executing recommendation / explicit recommendation acceptance or operator target-choice audit / optional one-child-intent conversion / routed readiness inspection / explicit gated routed submission / routed submitted-order lineage, lifecycle/actionability, reconciliation, and lifecycle-event audit inspection, with routed same-target retry retaining audit lineage. Route-readiness audits expose missing/stale/unsupported/unavailable/policy-blocked/blocking facts and data-source labels; `ready_for_recommendation` means data-sufficient only. Recommendations default to `single_ready_candidate_only`: zero ready candidates and multiple ready candidates block without ranking/scoring/price comparison. If the caller explicitly requests `explicit_binding_priority`, lower positive `target_recommendation_priority` wins only when exactly one ready candidate has the winning operator preference; missing, malformed, tied, or stale-quote selected priority data blocks. API `policy_name` is limited to accepted policies, omitted priority updates preserve the existing value, and `clear_target_recommendation_priority=true` intentionally clears it. Success still rechecks audit freshness plus stored candidate quote freshness plus current desired-trade/mandate/binding/account/symbol truth, source audits report `recommendation_created=true` after a recommendation record exists, Phase 6.2/6.2.1/6.2.2 acceptance sets recommendation/source-audit `target_choice_created=true` only after exactly one target choice exists from an explicit operator action on an otherwise successful recommendation, and Phase 6.3 sets recommendation/source-audit `child_intent_created=true` only after a valid child intent exists. Phase 6.4 preview/readiness inspection for recommendation-backed child intents now exposes routed lineage directly and blocks on stale recommendation-backed quote, mandate, binding/account, or symbol truth before eligible readiness. Application-level same-audit idempotency now prevents duplicate successful recommendations from one route-readiness audit from creating multiple accepted target choices, while preserving original acceptance timestamps; blocked same-audit recommendations cannot be marked accepted by that idempotency path. Phase 6.3 service-level same-desired-trade/same-audit conversion reuse prevents duplicate child intents in normal controlled flow. Future DB-level serialization may still be considered before automation. Auto-submit, fanout, target reselection, cross-binding/cross-venue recovery, venue-quality scoring, and CBBO remain separate future work.`

### K-007

- `status`: `open`
- `area`: `multi-account portfolio summaries`
- `summary`: `The mandate bootstrap summary avoids pretending a single account snapshot is a multi-account aggregate; a real mandate-level aggregate snapshot is still deferred.`
- `impact`: `Operators can inspect bound-account counts and account-scoped truth, but later portfolio phases must add true mandate-level account aggregation.`

### K-008

- `status`: `open`
- `area`: `multi-venue execution-preparable depth`
- `summary`: `Hyperliquid, Aster, OKX, Coinbase Advanced Trade, Binance, and Kraken now have code/test-proven scoped submit paths, broader post-submit reconciliation, bounded same-target recovery execution, truthful cancel behavior for the current supported scopes, selective native amend on Hyperliquid/OKX/Coinbase Advanced Trade/Kraken, and polling-first private-state visibility with sharper boundary truth: venue-private open orders remain distinct from SubmittedOrders, session-state is explicitly adapter/runtime bookkeeping, Hyperliquid private open orders and open positions now use direct venue query where account context exists, Hyperliquid direct open-position mark prices remain nullable unless venue markPx or a positionValue/szi derivation is available, and summary source fields describe the runtime path actually used. Venue parity is still uneven: Aster and Binance native amend remain unsupported, Aster/Binance summary-layer recent fills remain persistence-backed, most non-Hyperliquid open positions are still persistence-backed, and no adapter-level user-stream parity exists yet.`
- `impact`: `The platform can now submit, reconcile, classify recovery outcomes, cancel, amend on the currently proven scopes, inspect deeper venue/account private-state truth below routing, and block unsafe same-target retries using live open-order proof or submitted-at-bounded ambiguity-scoped same-account/same-symbol private fill evidence where supported. That ambiguous retry evidence is no longer exposed as plain submitted-order fill truth, but later execution phases still need broader amend parity, fuller direct account-state depth, and real user-stream/session parity before routing automation or wider live multi-venue execution is possible.`

### K-009

- `status`: `open`
- `area`: `planning source policy`
- `summary`: `Mandate market-data source policy is now explicit and persisted, but the current runtime still supports only one active planning/source venue per mandate and still expects that source venue to align with the process's active exchange/market-data adapter.`
- `impact`: `Phase 4.1 now enforces explicit source-policy during approval, but later phases must still add composite pricing/source support and fuller decoupling between planning-source selection and runtime market-data orchestration.`

### K-010

- `status`: `open`
- `area`: `live execution remains deferred`
- `summary`: `Phases 4.6 through 4.10.2 add bounded same-target recovery execution and private-state inspection depth. Phase 5.0 through Phase 5.10.2 add the non-executing routing substrate, routed order-shape policy, route-readiness audit, and read-only routed lifecycle/reconciliation audit surfaces. Phase 6.0.0 adds non-executing `single_ready_candidate_only` recommendation, Phase 6.0.1/6.0.2 harden recommendation current-truth and quote-freshness revalidation, Phase 6.1 adds optional explicit binding-priority recommendation using operator-configured `target_recommendation_priority`, Phase 6.1.1 tightens policy-name validation plus explicit priority clearing, Phase 6.2 explicitly accepts successful recommendations into non-executing target choices, Phase 6.2.1 prevents one route-readiness audit from producing multiple accepted target choices through duplicate successful recommendations, Phase 6.2.2 prevents blocked same-audit recommendations from being marked accepted by that idempotency path, Phase 6.3 explicitly converts accepted recommendation-backed target choices into exactly one routed child intent, and Phase 6.4 lets those child intents enter existing preview/readiness inspection with recommendation-aware lineage and truth checks. User-stream/event-driven lifecycle parity, broader amend parity for Aster/Binance, smart routing, best-binding selection, auto-submit, mandate-scoped OPEN bypass, slippage guards, routed limit-price source beyond explicit operator/request input, cross-binding/cross-venue recovery, and multi-binding execution orchestration are still deferred.`
- `impact`: `The platform can now transition from prepared -> eligible -> submitted -> reconciled on supported non-routed child-intent paths and, for routing-required mandate-scoped opens, into non-executing routing candidate assessment, non-selecting route-readiness audit, optional non-executing recommendation under default single-ready-candidate or explicit binding-priority policy, explicit recommendation acceptance or operator target-choice audit, one-child-intent conversion with explicit order-shape provenance, routed preparation/readiness inspection, explicit same-target routed submission when gates allow, and read-only routed submitted-order lineage/lifecycle/actionability/reconciliation-event inspection that survives same-target routed retry and reconciliation updates. Routed conversion still defaults to MARKET/no-limit/non-reduce-only, but explicit LIMIT can be requested only with a valid positive finite limit price and modeled order-type support. Accepted recommendation-backed conversion now preserves recommendation/audit/target-choice lineage and returns an existing child intent for repeated or same-audit duplicate conversion attempts; Phase 6.4 then allows explicit preview/readiness inspection through existing endpoints while still creating no submitted orders, exchange submit calls, route executor behavior, fanout, ranking/scoring, CBBO, target reselection, or auto-submit. The platform still avoids silently reusing invalid retry client order ids on strict-reuse venues, mislabeling venue-private open-order views as SubmittedOrders, exposing ambiguous Aster/Binance retry evidence as plain submitted-order fills, retrying past live open-order proof / submitted-at-bounded ambiguity-scoped private fill evidence, or converting route-readiness/recommendation/routed submission/reconciliation into fanout, scoring, CBBO, target reselection, route execution orchestration, cross-binding/cross-venue recovery, or slippage-controlled routed execution.`

### K-011

- `status`: `open`
- `area`: `routed order-shape policy`
- `summary`: `Converted routed child intents now use explicit LIMIT routed order-shape policy input when supplied, or the conservative current default when omitted. Default conversion remains MARKET order, no limit price, and reduce_only=false for mandate-scoped OPEN conversion. Explicit LIMIT requires a positive finite limit_price and current modeled MARKET/LIMIT order-type support; missing, malformed, non-finite, zero, negative, unsupported order types, MARKET+limit ambiguity, and reduce_only=true for OPEN block before child-intent creation. Malformed/non-finite LIMIT policy blocks report malformed_limit_price and routed_order_shape_policy_blocked without claiming limit_price_explicit. Slippage guard semantics and market-data-derived limit-price sources remain deferred.`
- `impact`: `The policy-backed MARKET default remains backward-compatible for the controlled explicit/gated same-target routed handoff, while explicit LIMIT is now audit-visible order-shape policy only. This is not target selection, venue scoring, CBBO, or price discovery. Before broader routed execution, auto-submit, fanout, target reselection, or route-executor work can be considered, the platform still needs slippage expansion, richer limit-price source semantics, and price guard policy.`
