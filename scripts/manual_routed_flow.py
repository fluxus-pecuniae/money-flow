"""Manual routed-flow inspection harness for the controlled Phase 6 chain.

This script is developer/operator tooling. It calls the existing routing and
execution services in an explicit sequence and emits a JSON trace. It is not a
router, route executor, auto-submit loop, or policy engine.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
import json
from typing import Any

from sqlalchemy import select

from core.config.settings import AppSettings, get_settings
from core.domain.enums import (
    RoutingTargetChoiceConversionStatus,
    RoutingTargetChoiceStatus,
    RoutingTargetRecommendationStatus,
)
from core.domain.models import (
    ExecutionReadinessAssessment,
    PreparedVenueOrder,
    RoutingAssessment,
    RouteReadinessAudit,
    RoutingTargetChoice,
    RoutingTargetChoiceConversionResult,
    RoutingTargetRecommendation,
    SubmittedOrder,
)
from core.interfaces.services import ExecutionService, RoutingAssessmentService
from db.models import MandateDesiredTradeModel
from db.session import SessionLocal
from services.execution.service import (
    DefaultExecutionService,
    SubmissionBlockedError,
    SubmissionFailedError,
)
from services.routing.service import DefaultRoutingAssessmentService, RoutingAssessmentError


SUBMISSION_CONFIRMATION_REASON = "manual_submission_confirmation_required"
SUBMISSION_SKIPPED_REASON = "manual_harness_default_no_submission"


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return enum_value
    return value


def _desired_trade_summary(model: MandateDesiredTradeModel | None) -> dict[str, Any]:
    if model is None:
        return {
            "found": False,
            "reason_codes": ["desired_trade_not_found"],
        }
    return {
        "found": True,
        "desired_trade_key": model.desired_trade_key,
        "desired_trade_ref_id": model.id,
        "status": _json_safe(model.status),
        "action": _json_safe(model.action),
        "target_scope": _json_safe(model.target_scope),
        "side": _json_safe(model.side),
        "desired_quantity": _json_safe(model.desired_quantity),
        "mandate_key": model.mandate_key,
        "strategy_mandate_ref_id": model.strategy_mandate_ref_id,
        "client_ref_id": model.client_ref_id,
        "instrument_key": model.instrument_key,
        "instrument_ref_id": model.instrument_ref_id,
        "symbol": model.symbol,
    }


def _assessment_summary(assessment: RoutingAssessment) -> dict[str, Any]:
    return {
        "routing_assessment_id": assessment.assessment_id,
        "desired_trade_key": assessment.desired_trade_key,
        "decision_status": _json_safe(assessment.decision_status),
        "candidate_count": len(assessment.candidates),
        "eligible_binding_count": assessment.eligible_binding_count,
        "ineligible_binding_count": assessment.ineligible_binding_count,
        "reason_codes": _json_safe(assessment.reason_codes),
        "missing_data": _json_safe(assessment.missing_data),
    }


def _audit_summary(audit: RouteReadinessAudit) -> dict[str, Any]:
    return {
        "route_readiness_audit_id": audit.route_readiness_audit_id,
        "routing_assessment_id": audit.routing_assessment_id,
        "desired_trade_key": audit.desired_trade_key,
        "overall_status": _json_safe(audit.overall_status),
        "candidate_count": audit.candidate_count,
        "ready_candidate_count": audit.ready_candidate_count,
        "reason_codes": _json_safe(audit.global_reason_codes),
        "blocking_reasons": _json_safe(audit.global_blocking_reasons),
        "missing_data": _json_safe(audit.global_missing_data),
        "stale_data": _json_safe(audit.global_stale_data),
        "recommendation_created": audit.recommendation_created,
        "target_choice_created": audit.target_choice_created,
        "child_intent_created": audit.child_intent_created,
        "submitted_order_created": audit.submitted_order_created,
    }


def _recommendation_summary(
    recommendation: RoutingTargetRecommendation,
) -> dict[str, Any]:
    return {
        "routing_target_recommendation_id": (
            recommendation.routing_target_recommendation_id
        ),
        "route_readiness_audit_id": recommendation.route_readiness_audit_id,
        "routing_assessment_id": recommendation.routing_assessment_id,
        "desired_trade_key": recommendation.desired_trade_key,
        "status": _json_safe(recommendation.status),
        "policy_name": recommendation.policy_name,
        "candidate_count": recommendation.candidate_count,
        "ready_candidate_count": recommendation.ready_candidate_count,
        "recommended_binding_ref_id": recommendation.recommended_binding_ref_id,
        "recommended_binding_key": recommendation.recommended_binding_key,
        "recommended_venue_account_ref_id": (
            recommendation.recommended_venue_account_ref_id
        ),
        "recommended_venue_account_key": (
            recommendation.recommended_venue_account_key
        ),
        "recommended_venue": recommendation.recommended_venue,
        "recommended_exchange_symbol": recommendation.recommended_exchange_symbol,
        "reason_codes": _json_safe(recommendation.reason_codes),
        "blocking_reasons": _json_safe(recommendation.blocking_reasons),
        "missing_data": _json_safe(recommendation.missing_data),
        "stale_data": _json_safe(recommendation.stale_data),
        "non_executing": recommendation.non_executing,
        "target_choice_created": recommendation.target_choice_created,
        "child_intent_created": recommendation.child_intent_created,
        "submitted_order_created": recommendation.submitted_order_created,
    }


def _target_choice_summary(choice: RoutingTargetChoice) -> dict[str, Any]:
    return {
        "target_choice_id": choice.target_choice_id,
        "routing_assessment_id": choice.routing_assessment_id,
        "desired_trade_key": choice.desired_trade_key,
        "status": _json_safe(choice.status),
        "selected_binding_ref_id": choice.selected_binding_ref_id,
        "selected_binding_key": choice.selected_binding_key,
        "selected_venue_account_ref_id": choice.selected_venue_account_ref_id,
        "selected_venue_account_key": choice.selected_venue_account_key,
        "selected_venue": choice.selected_venue,
        "reason_codes": _json_safe(choice.reason_codes),
        "missing_data": _json_safe(choice.missing_data),
        "non_executing": choice.non_executing,
    }


def _conversion_summary(
    conversion: RoutingTargetChoiceConversionResult,
) -> dict[str, Any]:
    return {
        "status": _json_safe(conversion.status),
        "target_choice_id": conversion.target_choice_id,
        "routing_assessment_id": conversion.routing_assessment_id,
        "desired_trade_key": conversion.desired_trade_key,
        "routing_target_recommendation_id": (
            conversion.routing_target_recommendation_id
        ),
        "route_readiness_audit_id": conversion.route_readiness_audit_id,
        "intent_id": conversion.intent_id,
        "selected_binding_ref_id": conversion.selected_binding_ref_id,
        "selected_binding_key": conversion.selected_binding_key,
        "selected_venue_account_ref_id": conversion.selected_venue_account_ref_id,
        "selected_venue_account_key": conversion.selected_venue_account_key,
        "selected_venue": conversion.selected_venue,
        "selected_exchange_symbol": conversion.selected_exchange_symbol,
        "reason_codes": _json_safe(conversion.reason_codes),
        "missing_data": _json_safe(conversion.missing_data),
        "non_submitting": conversion.non_submitting,
        "child_intent_created": conversion.child_intent_created,
        "child_intent_reused": conversion.child_intent_reused,
        "prepared_order_created": conversion.prepared_order_created,
        "readiness_assessment_created": conversion.readiness_assessment_created,
        "submitted_order_created": conversion.submitted_order_created,
    }


def _preview_summary(preview: PreparedVenueOrder) -> dict[str, Any]:
    routed_lineage = None
    if isinstance(preview.payload, dict):
        routed_lineage = preview.payload.get("routed_lineage")
    return {
        "intent_id": preview.intent_id,
        "preview_status": _json_safe(preview.preview_status),
        "venue": preview.venue,
        "venue_account_ref_id": preview.venue_account_ref_id,
        "symbol": preview.symbol,
        "exchange_symbol": preview.exchange_symbol,
        "order_type": _json_safe(preview.order_type),
        "limit_price": _json_safe(preview.limit_price),
        "reduce_only": preview.reduce_only,
        "reason_codes": _json_safe(preview.reason_codes),
        "routed_lineage": _json_safe(routed_lineage),
    }


def _readiness_summary(readiness: ExecutionReadinessAssessment) -> dict[str, Any]:
    routed_lineage = readiness.provenance.get("routed_lineage")
    return {
        "readiness_evaluation_id": readiness.readiness_evaluation_id,
        "intent_id": readiness.intent_id,
        "outcome": _json_safe(readiness.outcome),
        "preview_status": _json_safe(readiness.preview_status),
        "venue": readiness.venue,
        "eligible_for_submission_in_principle": (
            readiness.eligible_for_submission_in_principle
        ),
        "live_submission_phase_enabled": readiness.live_submission_phase_enabled,
        "reason_codes": _json_safe(readiness.reason_codes),
        "message": readiness.message,
        "routed_lineage": _json_safe(routed_lineage),
    }


def _submitted_order_summary(submitted: SubmittedOrder) -> dict[str, Any]:
    return {
        "submitted_order_id": submitted.submitted_order_id,
        "intent_id": submitted.intent_id,
        "venue": submitted.venue,
        "venue_account_ref_id": submitted.venue_account_ref_id,
        "symbol": submitted.symbol,
        "status": _json_safe(submitted.status),
        "reconciliation_status": _json_safe(submitted.reconciliation_status),
        "reason_codes": _json_safe(submitted.reason_codes),
    }


def _add_step(
    trace: dict[str, Any],
    name: str,
    *,
    status: str,
    details: dict[str, Any] | None = None,
    reason_codes: list[str] | None = None,
) -> None:
    step: dict[str, Any] = {
        "name": name,
        "status": status,
    }
    if details:
        step.update(_json_safe(details))
    if reason_codes:
        step["reason_codes"] = list(reason_codes)
    trace["steps"].append(step)


def _load_desired_trade_model(
    session_factory: Any,
    desired_trade_key: str,
) -> MandateDesiredTradeModel | None:
    with session_factory() as session:
        return session.scalar(
            select(MandateDesiredTradeModel).where(
                MandateDesiredTradeModel.desired_trade_key == desired_trade_key
            )
        )


async def _run_manual_routed_flow_async(
    *,
    desired_trade_key: str,
    create_assessment: bool = False,
    create_audit: bool = False,
    create_recommendation: bool = False,
    accept_recommendation: bool = False,
    convert_target_choice: bool = False,
    preview: bool = False,
    assess_readiness: bool = False,
    run_through_readiness: bool = False,
    submit: bool = False,
    danger_confirmed: bool = False,
    policy_name: str | None = None,
    approval_note: str | None = None,
    requested_by: str | None = "manual_routed_flow",
    settings: AppSettings | None = None,
    session_factory: Any = SessionLocal,
    routing_service: RoutingAssessmentService | None = None,
    execution_service: ExecutionService | None = None,
) -> dict[str, Any]:
    if run_through_readiness:
        create_assessment = True
        create_audit = True
        create_recommendation = True
        accept_recommendation = True
        convert_target_choice = True
        preview = True
        assess_readiness = True

    settings = settings or get_settings()
    routing_service = routing_service or DefaultRoutingAssessmentService(
        settings,
        session_factory=session_factory,
    )
    execution_service = execution_service or DefaultExecutionService(
        settings,
        session_factory=session_factory,
    )

    trace: dict[str, Any] = {
        "phase": "phase_6_5_manual_routed_flow",
        "mode": "inspection_only",
        "input": {
            "desired_trade_key": desired_trade_key,
            "policy_name": policy_name,
            "run_through_readiness": run_through_readiness,
        },
        "boundaries": {
            "smart_routing": False,
            "best_binding_selection": False,
            "ranking": False,
            "scoring": False,
            "cbbo": False,
            "fanout": False,
            "target_reselection": False,
            "route_executor": False,
            "auto_submit": False,
        },
        "steps": [],
        "artifacts": {},
        "submission": {
            "requested": submit,
            "danger_confirmed": danger_confirmed,
            "attempted": False,
            "skipped": True,
            "reason_codes": (
                [] if submit else [SUBMISSION_SKIPPED_REASON]
            ),
        },
        "ok": True,
    }

    desired_trade_model = _load_desired_trade_model(session_factory, desired_trade_key)
    desired_summary = _desired_trade_summary(desired_trade_model)
    _add_step(
        trace,
        "desired_trade",
        status="inspected" if desired_trade_model is not None else "blocked",
        details=desired_summary,
        reason_codes=None if desired_trade_model is not None else ["desired_trade_not_found"],
    )
    trace["artifacts"].update(
        {
            "desired_trade_key": desired_trade_key,
            "desired_trade_status": desired_summary.get("status"),
        }
    )
    if desired_trade_model is None:
        trace["ok"] = False
        return _json_safe(trace)

    assessment: RoutingAssessment | None = None
    audit: RouteReadinessAudit | None = None
    recommendation: RoutingTargetRecommendation | None = None
    target_choice: RoutingTargetChoice | None = None
    conversion: RoutingTargetChoiceConversionResult | None = None
    intent_id: str | None = None

    try:
        if create_assessment:
            assessment = await routing_service.create_assessment_from_desired_trade(
                desired_trade_key
            )
            assessment_details = _assessment_summary(assessment)
            _add_step(trace, "routing_assessment", status="created", details=assessment_details)
            trace["artifacts"].update(assessment_details)

        if create_audit:
            if assessment is not None:
                audit = await routing_service.create_route_readiness_audit_from_assessment(
                    assessment.assessment_id
                )
            else:
                audit = await routing_service.create_route_readiness_audit_from_desired_trade(
                    desired_trade_key
                )
                if audit.routing_assessment_id is not None:
                    assessment = await routing_service.get_routing_assessment(
                        audit.routing_assessment_id
                    )
                    assessment_details = _assessment_summary(assessment)
                    _add_step(
                        trace,
                        "routing_assessment",
                        status="created_by_audit",
                        details=assessment_details,
                    )
                    trace["artifacts"].update(assessment_details)
            audit_details = _audit_summary(audit)
            _add_step(trace, "route_readiness_audit", status="created", details=audit_details)
            trace["artifacts"].update(audit_details)

        if create_recommendation:
            if audit is None:
                _add_step(
                    trace,
                    "routing_target_recommendation",
                    status="blocked",
                    reason_codes=["manual_harness_route_readiness_audit_required"],
                )
                trace["ok"] = False
            else:
                recommendation = (
                    await routing_service.create_routing_target_recommendation_from_route_readiness_audit(
                        audit.route_readiness_audit_id,
                        policy_name=policy_name,
                    )
                )
                recommendation_details = _recommendation_summary(recommendation)
                _add_step(
                    trace,
                    "routing_target_recommendation",
                    status="created",
                    details=recommendation_details,
                )
                trace["artifacts"].update(recommendation_details)

        if accept_recommendation:
            if recommendation is None:
                _add_step(
                    trace,
                    "routing_target_choice",
                    status="blocked",
                    reason_codes=["manual_harness_recommendation_required"],
                )
                trace["ok"] = False
            elif (
                recommendation.status
                != RoutingTargetRecommendationStatus.RECOMMENDED_SINGLE_READY_CANDIDATE
            ):
                _add_step(
                    trace,
                    "routing_target_choice",
                    status="blocked",
                    reason_codes=[
                        "manual_harness_recommendation_not_successful",
                        _json_safe(recommendation.status),
                    ],
                )
                trace["ok"] = False
            else:
                target_choice = (
                    await routing_service.accept_routing_target_recommendation_to_target_choice(
                        recommendation.routing_target_recommendation_id,
                        approval_note=approval_note,
                        requested_by=requested_by,
                    )
                )
                choice_details = _target_choice_summary(target_choice)
                _add_step(trace, "routing_target_choice", status="created", details=choice_details)
                trace["artifacts"].update(choice_details)

        if convert_target_choice:
            if target_choice is None:
                _add_step(
                    trace,
                    "child_intent_conversion",
                    status="blocked",
                    reason_codes=["manual_harness_target_choice_required"],
                )
                trace["ok"] = False
            elif target_choice.status != RoutingTargetChoiceStatus.TARGET_CHOICE_RECORDED:
                _add_step(
                    trace,
                    "child_intent_conversion",
                    status="blocked",
                    reason_codes=[
                        "manual_harness_target_choice_not_recorded",
                        _json_safe(target_choice.status),
                    ],
                )
                trace["ok"] = False
            else:
                conversion = await routing_service.convert_target_choice_to_child_intent(
                    target_choice.target_choice_id
                )
                conversion_details = _conversion_summary(conversion)
                _add_step(
                    trace,
                    "child_intent_conversion",
                    status="created_or_reused",
                    details=conversion_details,
                )
                trace["artifacts"].update(conversion_details)
                if conversion.status in {
                    RoutingTargetChoiceConversionStatus.CHILD_INTENT_CREATED,
                    RoutingTargetChoiceConversionStatus.CHILD_INTENT_ALREADY_EXISTS,
                }:
                    intent_id = conversion.intent_id
                else:
                    trace["ok"] = False

        if preview:
            if intent_id is None:
                _add_step(
                    trace,
                    "prepared_order_preview",
                    status="blocked",
                    reason_codes=["manual_harness_child_intent_required"],
                )
                trace["ok"] = False
            else:
                preview_result = await execution_service.preview_child_intent(intent_id)
                preview_details = _preview_summary(preview_result)
                _add_step(
                    trace,
                    "prepared_order_preview",
                    status="inspected",
                    details=preview_details,
                )
                trace["artifacts"].update(
                    {
                        "prepared_order_preview_status": preview_details[
                            "preview_status"
                        ],
                        "prepared_order_preview_reason_codes": preview_details[
                            "reason_codes"
                        ],
                        "routed_lineage": preview_details.get("routed_lineage"),
                    }
                )

        if assess_readiness:
            if intent_id is None:
                _add_step(
                    trace,
                    "execution_readiness",
                    status="blocked",
                    reason_codes=["manual_harness_child_intent_required"],
                )
                trace["ok"] = False
            else:
                readiness = await execution_service.assess_child_intent_readiness(intent_id)
                readiness_details = _readiness_summary(readiness)
                _add_step(
                    trace,
                    "execution_readiness",
                    status="inspected",
                    details=readiness_details,
                )
                trace["artifacts"].update(
                    {
                        "readiness_evaluation_id": readiness_details[
                            "readiness_evaluation_id"
                        ],
                        "readiness_outcome": readiness_details["outcome"],
                        "readiness_reason_codes": readiness_details["reason_codes"],
                        "routed_lineage": readiness_details.get("routed_lineage"),
                    }
                )

        if submit:
            trace["submission"]["skipped"] = False
            if not danger_confirmed:
                trace["submission"].update(
                    {
                        "attempted": False,
                        "blocked": True,
                        "skipped": True,
                        "reason_codes": [SUBMISSION_CONFIRMATION_REASON],
                    }
                )
                _add_step(
                    trace,
                    "submission",
                    status="blocked_before_service_submission",
                    reason_codes=[SUBMISSION_CONFIRMATION_REASON],
                )
                trace["ok"] = False
            elif intent_id is None:
                trace["submission"].update(
                    {
                        "attempted": False,
                        "blocked": True,
                        "skipped": True,
                        "reason_codes": ["manual_harness_child_intent_required"],
                    }
                )
                _add_step(
                    trace,
                    "submission",
                    status="blocked",
                    reason_codes=["manual_harness_child_intent_required"],
                )
                trace["ok"] = False
            else:
                intent = await execution_service.get_child_intent(intent_id)
                trace["submission"]["attempted"] = True
                submitted = await execution_service.submit_prepared_intent(intent)
                submitted_details = _submitted_order_summary(submitted)
                trace["submission"].update(
                    {
                        "blocked": False,
                        "skipped": False,
                        "submitted_order_id": submitted.submitted_order_id,
                        "reason_codes": submitted_details["reason_codes"],
                    }
                )
                _add_step(trace, "submission", status="submitted", details=submitted_details)
                trace["artifacts"].update(submitted_details)

    except RoutingAssessmentError as exc:
        trace["ok"] = False
        _add_step(
            trace,
            "error",
            status="blocked",
            details={"message": str(exc)},
            reason_codes=[exc.reason_code],
        )
    except SubmissionBlockedError as exc:
        trace["ok"] = False
        reason_codes = list(exc.readiness.reason_codes or [exc.readiness.outcome.value])
        trace["submission"].update(
            {
                "blocked": True,
                "attempted": True,
                "skipped": False,
                "reason_codes": _json_safe(reason_codes),
            }
        )
        _add_step(
            trace,
            "submission",
            status="blocked_by_existing_readiness_gates",
            details=_readiness_summary(exc.readiness),
            reason_codes=reason_codes,
        )
    except SubmissionFailedError as exc:
        trace["ok"] = False
        trace["submission"].update(
            {
                "blocked": False,
                "attempted": True,
                "skipped": False,
                "reason_codes": list(exc.reason_codes),
            }
        )
        _add_step(
            trace,
            "submission",
            status="failed",
            details={"message": str(exc), "venue": exc.venue},
            reason_codes=list(exc.reason_codes),
        )
    except ValueError as exc:
        trace["ok"] = False
        _add_step(
            trace,
            "error",
            status="blocked",
            details={"message": str(exc)},
            reason_codes=["manual_harness_value_error"],
        )

    return _json_safe(trace)


def run_manual_routed_flow(
    *,
    desired_trade_key: str,
    create_assessment: bool = False,
    create_audit: bool = False,
    create_recommendation: bool = False,
    accept_recommendation: bool = False,
    convert_target_choice: bool = False,
    preview: bool = False,
    assess_readiness: bool = False,
    run_through_readiness: bool = False,
    submit: bool = False,
    danger_confirmed: bool = False,
    policy_name: str | None = None,
    approval_note: str | None = None,
    requested_by: str | None = "manual_routed_flow",
    settings: AppSettings | None = None,
    session_factory: Any = SessionLocal,
    routing_service: RoutingAssessmentService | None = None,
    execution_service: ExecutionService | None = None,
) -> dict[str, Any]:
    return asyncio.run(
        _run_manual_routed_flow_async(
            desired_trade_key=desired_trade_key,
            create_assessment=create_assessment,
            create_audit=create_audit,
            create_recommendation=create_recommendation,
            accept_recommendation=accept_recommendation,
            convert_target_choice=convert_target_choice,
            preview=preview,
            assess_readiness=assess_readiness,
            run_through_readiness=run_through_readiness,
            submit=submit,
            danger_confirmed=danger_confirmed,
            policy_name=policy_name,
            approval_note=approval_note,
            requested_by=requested_by,
            settings=settings,
            session_factory=session_factory,
            routing_service=routing_service,
            execution_service=execution_service,
        )
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manual routed-flow inspection trace from an existing "
            "routing-required desired trade."
        )
    )
    parser.add_argument("--desired-trade-key", required=True)
    parser.add_argument(
        "--policy-name",
        choices=("single_ready_candidate_only", "explicit_binding_priority"),
        default=None,
        help="Recommendation policy. Omit for the default single-ready-candidate policy.",
    )
    parser.add_argument("--create-assessment", action="store_true")
    parser.add_argument("--create-audit", action="store_true")
    parser.add_argument("--create-recommendation", action="store_true")
    parser.add_argument("--accept-recommendation", action="store_true")
    parser.add_argument("--convert-target-choice", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--assess-readiness", action="store_true")
    parser.add_argument(
        "--run-through-readiness",
        action="store_true",
        help=(
            "Convenience mode: explicitly creates assessment, audit, recommendation, "
            "target choice, child intent, prepared-order preview, and readiness. "
            "It still skips submission unless --submit and the danger confirmation "
            "flag are also supplied."
        ),
    )
    parser.add_argument("--submit", action="store_true")
    parser.add_argument(
        "--i-understand-this-can-place-a-live-order",
        action="store_true",
        dest="danger_confirmed",
    )
    parser.add_argument("--approval-note", default=None)
    parser.add_argument("--requested-by", default="manual_routed_flow")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = run_manual_routed_flow(
        desired_trade_key=args.desired_trade_key,
        create_assessment=args.create_assessment,
        create_audit=args.create_audit,
        create_recommendation=args.create_recommendation,
        accept_recommendation=args.accept_recommendation,
        convert_target_choice=args.convert_target_choice,
        preview=args.preview,
        assess_readiness=args.assess_readiness,
        run_through_readiness=args.run_through_readiness,
        submit=args.submit,
        danger_confirmed=args.danger_confirmed,
        policy_name=args.policy_name,
        approval_note=args.approval_note,
        requested_by=args.requested_by,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
