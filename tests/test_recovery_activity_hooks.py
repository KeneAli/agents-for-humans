from types import SimpleNamespace

from src.agent.recovery_activity_hooks import RecoveryActivityHooks
from src.simulation.operational_state import OperationalState
from src.state.in_memory_state_repository import InMemoryStateRepository


def tool_event(tool_name, shipment_id="SHP-0048", exception=None):
    return SimpleNamespace(
        tool_use={"name": tool_name, "input": {"shipment_id": shipment_id}},
        exception=exception,
    )


def test_recognized_tool_lifecycle_events_are_run_scoped():
    repository = InMemoryStateRepository()
    hooks = RecoveryActivityHooks(
        state=OperationalState(repository=repository),
        run_id="RUN-A",
        event_id="EVENT-A",
        runtime_session_id="SESSION-A",
    )

    hooks.before_tool_call(tool_event("get_shipment_context"))
    hooks.after_tool_call(tool_event("get_shipment_context"))
    hooks.before_tool_call(tool_event("get_business_consequences"))
    hooks.after_tool_call(tool_event("get_business_consequences"))
    hooks.before_tool_call(tool_event("evaluate_recovery_options"))

    events = repository.get_audit_events("SHP-0048", "RUN-A")

    assert [event["event_type"] for event in events] == [
        "SHIPMENT_CONTEXT_REVIEW_STARTED",
        "SHIPMENT_CONTEXT_REVIEWED",
        "DELAY_IMPACT_ASSESSMENT_STARTED",
        "DELAY_IMPACT_ASSESSED",
        "RECOVERY_OPTIONS_EVALUATION_STARTED",
    ]
    assert all(event["event_id"] == "EVENT-A" for event in events)
    assert all(event["runtime_session_id"] == "SESSION-A" for event in events)
    assert repository.get_audit_events("SHP-0048", "RUN-B") == []


def test_unrecognized_or_failed_tools_do_not_emit_completion_events():
    repository = InMemoryStateRepository()
    hooks = RecoveryActivityHooks(
        state=OperationalState(repository=repository),
        run_id="RUN-A",
        event_id="EVENT-A",
        runtime_session_id="SESSION-A",
    )

    hooks.before_tool_call(tool_event("unknown_tool"))
    hooks.after_tool_call(tool_event("get_shipment_context", exception=ValueError()))

    assert repository.get_audit_events("SHP-0048", "RUN-A") == []