"""Shared parsing for routed submitted-order lifecycle audit metadata."""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

from core.domain.models import SubmittedOrderRoutedLifecycleContext


ROUTED_SUBMITTED_ORDER_STRING_FIELDS = (
    "intent_id",
    "desired_trade_key",
    "routing_assessment_id",
    "routing_target_choice_id",
    "selected_binding_ref_id",
    "selected_binding_key",
    "selected_venue_account_ref_id",
    "selected_venue_account_key",
    "selected_venue",
    "selected_exchange_symbol",
    "readiness_evaluation_id",
)

ROUTED_SUBMITTED_ORDER_OPTIONAL_STRING_FIELDS = (
    "route_readiness_audit_id",
    "routing_target_recommendation_id",
    "recommendation_policy_name",
)

ROUTED_SUBMITTED_ORDER_BOOL_FIELDS = (
    "explicit_action_required",
    "auto_submit",
    "fanout_created",
    "allocation_created",
    "scoring_created",
    "route_executor_created",
    "target_reselection",
    "submitted_order_created",
)

ROUTED_SUBMITTED_ORDER_LINEAGE_FIELDS = (
    *ROUTED_SUBMITTED_ORDER_STRING_FIELDS,
    *ROUTED_SUBMITTED_ORDER_BOOL_FIELDS,
)


def _jsonable_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(payload), default=str))


def submitted_order_routed_lifecycle_context_from_raw_payload(
    raw_payload: Mapping[str, Any] | None,
) -> SubmittedOrderRoutedLifecycleContext | None:
    """Return bounded read-only routed lifecycle context from SubmittedOrder raw payload."""

    if not isinstance(raw_payload, Mapping) or "routed_submission" not in raw_payload:
        return None

    routed_payload = raw_payload.get("routed_submission")
    if not isinstance(routed_payload, Mapping):
        return SubmittedOrderRoutedLifecycleContext(
            routed_origin=True,
            intent_id=None,
            desired_trade_key=None,
            routing_assessment_id=None,
            route_readiness_audit_id=None,
            routing_target_recommendation_id=None,
            routing_target_choice_id=None,
            recommendation_policy_name=None,
            selected_binding_ref_id=None,
            selected_binding_key=None,
            selected_venue_account_ref_id=None,
            selected_venue_account_key=None,
            selected_venue=None,
            selected_exchange_symbol=None,
            readiness_evaluation_id=None,
            explicit_action_required=None,
            auto_submit=None,
            fanout_created=None,
            allocation_created=None,
            scoring_created=None,
            route_executor_created=None,
            target_reselection=None,
            submitted_order_created=None,
            boundary_reason_codes=[
                "routed_origin",
                "routed_recovery_same_target_only",
                "routed_lineage_malformed",
                "no_fanout",
                "no_target_reselection",
            ],
            route_lineage_malformed=True,
            missing_lineage_fields=list(ROUTED_SUBMITTED_ORDER_LINEAGE_FIELDS),
            malformed_lineage_fields=["routed_submission"],
        )

    missing_fields: list[str] = []
    malformed_fields: list[str] = []

    def _lineage_str(field: str) -> str | None:
        if field not in routed_payload or routed_payload.get(field) is None:
            missing_fields.append(field)
            return None
        value = routed_payload.get(field)
        if isinstance(value, str):
            return value
        malformed_fields.append(field)
        return None

    def _optional_lineage_str(field: str) -> str | None:
        if field not in routed_payload or routed_payload.get(field) is None:
            return None
        value = routed_payload.get(field)
        if isinstance(value, str):
            return value
        malformed_fields.append(field)
        return None

    def _lineage_bool(field: str) -> bool | None:
        if field not in routed_payload or routed_payload.get(field) is None:
            missing_fields.append(field)
            return None
        value = routed_payload.get(field)
        if isinstance(value, bool):
            return value
        malformed_fields.append(field)
        return None

    routed_order_shape_policy = routed_payload.get("routed_order_shape_policy")
    if routed_order_shape_policy is not None and not isinstance(
        routed_order_shape_policy, Mapping
    ):
        malformed_fields.append("routed_order_shape_policy")
        routed_order_shape_policy = None

    intent_id = _lineage_str("intent_id")
    desired_trade_key = _lineage_str("desired_trade_key")
    routing_assessment_id = _lineage_str("routing_assessment_id")
    route_readiness_audit_id = _optional_lineage_str("route_readiness_audit_id")
    routing_target_recommendation_id = _optional_lineage_str(
        "routing_target_recommendation_id"
    )
    routing_target_choice_id = _lineage_str("routing_target_choice_id")
    recommendation_policy_name = _optional_lineage_str("recommendation_policy_name")
    selected_binding_ref_id = _lineage_str("selected_binding_ref_id")
    selected_binding_key = _lineage_str("selected_binding_key")
    selected_venue_account_ref_id = _lineage_str("selected_venue_account_ref_id")
    selected_venue_account_key = _lineage_str("selected_venue_account_key")
    selected_venue = _lineage_str("selected_venue")
    selected_exchange_symbol = _lineage_str("selected_exchange_symbol")
    readiness_evaluation_id = _lineage_str("readiness_evaluation_id")
    explicit_action_required = _lineage_bool("explicit_action_required")
    auto_submit = _lineage_bool("auto_submit")
    fanout_created = _lineage_bool("fanout_created")
    allocation_created = _lineage_bool("allocation_created")
    scoring_created = _lineage_bool("scoring_created")
    route_executor_created = _lineage_bool("route_executor_created")
    target_reselection = _lineage_bool("target_reselection")
    submitted_order_created = _lineage_bool("submitted_order_created")

    boundary_reason_codes = [
        "routed_origin",
        "routed_recovery_same_target_only",
        "no_fanout",
        "no_target_reselection",
    ]
    if missing_fields or malformed_fields:
        boundary_reason_codes.append("routed_lineage_malformed")

    return SubmittedOrderRoutedLifecycleContext(
        routed_origin=True,
        intent_id=intent_id,
        desired_trade_key=desired_trade_key,
        routing_assessment_id=routing_assessment_id,
        route_readiness_audit_id=route_readiness_audit_id,
        routing_target_recommendation_id=routing_target_recommendation_id,
        routing_target_choice_id=routing_target_choice_id,
        recommendation_policy_name=recommendation_policy_name,
        selected_binding_ref_id=selected_binding_ref_id,
        selected_binding_key=selected_binding_key,
        selected_venue_account_ref_id=selected_venue_account_ref_id,
        selected_venue_account_key=selected_venue_account_key,
        selected_venue=selected_venue,
        selected_exchange_symbol=selected_exchange_symbol,
        readiness_evaluation_id=readiness_evaluation_id,
        explicit_action_required=explicit_action_required,
        auto_submit=auto_submit,
        fanout_created=fanout_created,
        allocation_created=allocation_created,
        scoring_created=scoring_created,
        route_executor_created=route_executor_created,
        target_reselection=target_reselection,
        submitted_order_created=submitted_order_created,
        boundary_reason_codes=boundary_reason_codes,
        route_lineage_malformed=bool(missing_fields or malformed_fields),
        missing_lineage_fields=missing_fields,
        malformed_lineage_fields=malformed_fields,
        routed_order_shape_policy=(
            _jsonable_mapping(routed_order_shape_policy)
            if isinstance(routed_order_shape_policy, Mapping)
            else None
        ),
    )
