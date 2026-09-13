from typing import Any

from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent, HookProvider, HookRegistry

from src.simulation.operational_state import OperationalState


import json
from typing import Any

from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent, HookProvider, HookRegistry

from src.simulation.operational_state import OperationalState


def _extract_tool_result_data(result: Any) -> dict | None:
    if not isinstance(result, dict):
        return None
    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if "json" in item and isinstance(item["json"], dict):
                    return item["json"]
                if "text" in item and isinstance(item["text"], str):
                    try:
                        parsed = json.loads(item["text"])
                        if isinstance(parsed, dict):
                            return parsed
                    except Exception:
                        pass
    return None


class RecoveryActivityHooks(HookProvider):
    """Persist controlled operational facts and evidence for recognized recovery tools."""

    def __init__(
        self,
        state: OperationalState,
        run_id: str | None,
        event_id: str | None,
        runtime_session_id: str | None,
    ):
        self.state = state
        self.run_id = run_id
        self.event_id = event_id
        self.runtime_session_id = runtime_session_id

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self.before_tool_call)
        registry.add_callback(AfterToolCallEvent, self.after_tool_call)

    def before_tool_call(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use.get("name")
        if name == "get_shipment_context":
            self._record(
                "SHIPMENT_CONTEXT_REVIEW_STARTED",
                event.tool_use,
                details={
                    "tool_name": name,
                    "summary": "Reviewing shipment context and delivery commitments.",
                    "live": [
                        "Retrieving shipment record and operational status...",
                        "Checking route origin, destination, and distance...",
                        "Verifying carrier profile and transit requirements...",
                    ],
                },
            )
        elif name == "get_business_consequences":
            self._record(
                "DELAY_IMPACT_ASSESSMENT_STARTED",
                event.tool_use,
                details={
                    "tool_name": name,
                    "summary": "Calculating delay consequences and contract SLA exposure.",
                    "live": [
                        "Checking contract SLA rules and customer priority...",
                        "Calculating delay breach duration...",
                        "Quantifying projected penalty exposure...",
                    ],
                },
            )
        elif name == "evaluate_recovery_options":
            self._record(
                "RECOVERY_OPTIONS_EVALUATION_STARTED",
                event.tool_use,
                details={
                    "tool_name": name,
                    "summary": "Evaluating deterministic recovery strategies and operational constraints.",
                    "live": [
                        "Evaluating recovery strategies...",
                        "Checking inventory availability and safety stock...",
                        "Checking expedited transportation lanes...",
                        "Calculating net economic benefits...",
                    ],
                },
            )

    def after_tool_call(self, event: AfterToolCallEvent) -> None:
        if event.exception is not None:
            return
        name = event.tool_use.get("name")
        result_obj = getattr(event, "result", None)
        data = _extract_tool_result_data(result_obj) or {}

        if name == "get_shipment_context":
            shipment = data.get("shipment", {}) if isinstance(data, dict) else {}
            order = data.get("order", {}) if isinstance(data, dict) else {}
            route = data.get("route", {}) if isinstance(data, dict) else {}
            carrier = data.get("carrier", {}) if isinstance(data, dict) else {}

            shipment_id = shipment.get("shipment_id", "Shipment")
            origin = route.get("origin_warehouse", shipment.get("origin_warehouse_id", "Origin"))
            destination = route.get("destination_warehouse", shipment.get("destination_warehouse_id", "Destination"))
            status = shipment.get("shipment_status", "DELAYED")
            priority = order.get("priority", "STANDARD")
            current_eta = str(shipment.get("current_eta", "unknown"))

            evidence_items = [
                f"Route: {origin} → {destination} ({route.get('distance_km', 0)} km)",
                f"Status: {status} · Current ETA: {current_eta}",
                f"Order Priority: {priority} · Promised: {order.get('promised_delivery', 'unknown')}",
                f"Carrier: {carrier.get('carrier_name', 'Assigned Carrier')} (€{carrier.get('base_cost_per_km', 0):.2f}/km)",
            ]
            observation = f"{shipment_id} ({priority} priority) is currently {status.lower()} on route {origin} → {destination}, requiring consequence assessment."

            self._record(
                "SHIPMENT_CONTEXT_REVIEWED",
                event.tool_use,
                details={
                    "tool_name": name,
                    "summary": "Shipment context and delivery schedule verified.",
                    "details": evidence_items,
                    "agent_observation": observation,
                    "shipment": shipment,
                    "order": order,
                    "route": route,
                },
            )

        elif name == "get_business_consequences":
            shipment_id = data.get("shipment_id", "Shipment")
            delay_minutes = data.get("delay_minutes", 0)
            sla_breached = bool(data.get("sla_breached", False))
            sla_breach_hours = float(data.get("sla_breach_hours", 0.0))
            penalty = float(data.get("projected_sla_penalty_eur", 0.0))
            tolerance = float(data.get("sla_tolerance_hours", 0.0))
            deadline = str(data.get("sla_deadline", "unknown"))

            evidence_items = [
                f"Delay: {delay_minutes} min (SLA tolerance: {tolerance:.1f}h)",
                f"SLA Deadline: {deadline}",
                f"Breach Duration: {sla_breach_hours:.1f}h",
                f"Projected SLA Penalty: €{penalty:.2f}",
                f"SLA Breached: {'Yes' if sla_breached else 'No'}",
            ]

            if sla_breached:
                observation = f"Delay of {delay_minutes}m creates a {sla_breach_hours:.1f}h SLA breach and €{penalty:.2f} penalty exposure, warranting active recovery."
            else:
                observation = f"Delay of {delay_minutes}m is within the {tolerance:.1f}h SLA tolerance with zero penalty exposure."

            self._record(
                "DELAY_IMPACT_ASSESSED",
                event.tool_use,
                details={
                    "tool_name": name,
                    "summary": "Delay consequences and financial SLA exposure calculated.",
                    "details": evidence_items,
                    "agent_observation": observation,
                    "delay_minutes": delay_minutes,
                    "projected_sla_penalty_eur": penalty,
                    "sla_breached": sla_breached,
                },
            )

    def _record(self, event_type: str, tool_use: dict[str, Any], details: dict[str, Any] | None = None) -> None:
        if not self.run_id:
            return
        tool_input = tool_use.get("input", {})
        shipment_id = tool_input.get("shipment_id") if isinstance(tool_input, dict) else None
        if not isinstance(shipment_id, str) or not shipment_id:
            return

        payload_details = {"tool_name": tool_use.get("name")}
        if details:
            payload_details.update(details)

        self.state.record_audit_event(
            event_type=event_type,
            shipment_id=shipment_id,
            run_id=self.run_id,
            details=payload_details,
            event_id=self.event_id,
            runtime_session_id=self.runtime_session_id,
        )
