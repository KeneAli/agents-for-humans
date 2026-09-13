from typing import Any

from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent, HookProvider, HookRegistry

from src.simulation.operational_state import OperationalState


class RecoveryActivityHooks(HookProvider):
    """Persist controlled operational facts for recognized recovery tools."""

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
        event_type = {
            "get_shipment_context": "SHIPMENT_CONTEXT_REVIEW_STARTED",
            "get_business_consequences": "DELAY_IMPACT_ASSESSMENT_STARTED",
            "evaluate_recovery_options": "RECOVERY_OPTIONS_EVALUATION_STARTED",
        }.get(event.tool_use.get("name"))
        if event_type:
            self._record(event_type, event.tool_use)

    def after_tool_call(self, event: AfterToolCallEvent) -> None:
        if event.exception is not None:
            return
        event_type = {
            "get_shipment_context": "SHIPMENT_CONTEXT_REVIEWED",
            "get_business_consequences": "DELAY_IMPACT_ASSESSED",
        }.get(event.tool_use.get("name"))
        if event_type:
            self._record(event_type, event.tool_use)

    def _record(self, event_type: str, tool_use: dict[str, Any]) -> None:
        if not self.run_id:
            return
        tool_input = tool_use.get("input", {})
        shipment_id = tool_input.get("shipment_id") if isinstance(tool_input, dict) else None
        if not isinstance(shipment_id, str) or not shipment_id:
            return
        self.state.record_audit_event(
            event_type=event_type,
            shipment_id=shipment_id,
            run_id=self.run_id,
            details={"tool_name": tool_use.get("name")},
            event_id=self.event_id,
            runtime_session_id=self.runtime_session_id,
        )
