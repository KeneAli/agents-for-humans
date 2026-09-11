from src.state.in_memory_state_repository import (
    InMemoryStateRepository,
)
from src.state.dynamodb_state_repository import DynamoDBStateRepository
from src.state.state_repository_factory import create_state_repository
from src.agent.tools.recovery_tools import create_recovery_tools
from src.simulation.operational_state import OperationalState


def test_pending_recovery_approval():
    repository = InMemoryStateRepository()
    run_id = "RUN-A"

    approval = {
        "shipment_id": "SHP-0048",
        "run_id": run_id,
        "selected_option": "EXPEDITED_TRANSPORT",
    }

    repository.set_pending_recovery_approval(
        approval
    )

    assert (
        repository.get_pending_recovery_approval("SHP-0048", run_id)
        == approval
    )

    repository.clear_pending_recovery_approval("SHP-0048", run_id)

    assert (
        repository.get_pending_recovery_approval("SHP-0048", run_id)
        is None
    )


def test_state_repository_factory_uses_dynamodb_runtime_configuration(monkeypatch):
    monkeypatch.setenv("STATE_REPOSITORY", "dynamodb")
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "runtime-state-table")
    monkeypatch.setenv("AWS_REGION", "us-west-2")

    repository = create_state_repository()

    assert isinstance(repository, DynamoDBStateRepository)
    assert repository.table.name == "runtime-state-table"


def test_recovery_workflow():
    repository = InMemoryStateRepository()
    run_id = "RUN-A"

    repository.set_recovery_workflow(
        shipment_id="SHP-0048",
        run_id=run_id,
        status="AWAITING_APPROVAL",
        action="EXPEDITED_TRANSPORT",
    )

    workflow = repository.get_recovery_workflow(
        "SHP-0048", run_id
    )

    assert workflow == {
        "shipment_id": "SHP-0048",
        "run_id": run_id,
        "event_id": None,
        "runtime_session_id": None,
        "status": "AWAITING_APPROVAL",
        "action": "EXPEDITED_TRANSPORT",
    }


def test_audit_events():
    repository = InMemoryStateRepository()
    run_id = "RUN-A"

    repository.record_audit_event(
        event_type="RECOVERY_SELECTED",
        shipment_id="SHP-0048",
        run_id=run_id,
        details={
            "option_type": "EXPEDITED_TRANSPORT",
        },
    )

    events = repository.get_audit_events(
        "SHP-0048", run_id
    )

    assert len(events) == 1
    assert (
        events[0]["event_type"]
        == "RECOVERY_SELECTED"
    )
    assert (
        events[0]["details"]["option_type"]
        == "EXPEDITED_TRANSPORT"
    )


def test_disruption_event_claim_is_idempotent():
    repository = InMemoryStateRepository()

    event = {
        "event_id": "SIM-A1B2C3D4",
        "event_type": "VEHICLE_BREAKDOWN",
        "shipment_id": "SHP-0048",
        "delay_minutes": 480,
    }

    assert repository.claim_disruption_event(
        event_id=event["event_id"],
        shipment_id=event["shipment_id"],
        event=event,
    ) is True

    assert repository.claim_disruption_event(
        event_id=event["event_id"],
        shipment_id=event["shipment_id"],
        event=event,
    ) is False

def test_operational_state_uses_injected_repository():
    repository = InMemoryStateRepository()
    state = OperationalState(repository=repository)
    run_id = "RUN-A"

    approval = {
        "shipment_id": "SHP-0048",
        "run_id": run_id,
        "selected_option": "EXPEDITED_TRANSPORT",
    }

    state.set_pending_recovery_approval(approval)

    assert (
        repository.get_pending_recovery_approval("SHP-0048", run_id)
        == approval
    )

    state.set_recovery_workflow(
        shipment_id="SHP-0048",
        run_id=run_id,
        status="AWAITING_APPROVAL",
        action="EXPEDITED_TRANSPORT",
    )

    assert (
        repository.get_recovery_workflow("SHP-0048", run_id)
        == {
            "shipment_id": "SHP-0048",
            "run_id": run_id,
            "event_id": None,
            "runtime_session_id": None,
            "status": "AWAITING_APPROVAL",
            "action": "EXPEDITED_TRANSPORT",
        }
    )

    state.record_audit_event(
        event_type="RECOVERY_SELECTED",
        shipment_id="SHP-0048",
        run_id=run_id,
        details={
            "option_type": "EXPEDITED_TRANSPORT",
        },
    )

    events = repository.get_audit_events("SHP-0048", run_id)

    assert len(events) == 1
    assert events[0]["event_type"] == "RECOVERY_SELECTED"


def test_runs_for_one_shipment_are_isolated():
    repository = InMemoryStateRepository()
    shipment_id = "SHP-0048"
    run_a = "RUN-A"
    run_b = "RUN-B"

    repository.set_pending_recovery_approval(
        {"shipment_id": shipment_id, "run_id": run_a, "status": "PENDING_APPROVAL"}
    )
    repository.set_pending_recovery_approval(
        {"shipment_id": shipment_id, "run_id": run_b, "status": "PENDING_APPROVAL"}
    )
    repository.set_recovery_workflow(shipment_id, run_a, "COMPLETED")
    repository.set_recovery_workflow(shipment_id, run_b, "PENDING_APPROVAL")
    repository.record_audit_event("RECOVERY_EXECUTED", shipment_id, run_a)
    repository.record_audit_event("STATE_VERIFIED", shipment_id, run_a)

    assert repository.get_pending_recovery_approval(shipment_id, run_a)["status"] == "PENDING_APPROVAL"
    assert repository.get_pending_recovery_approval(shipment_id, run_b)["status"] == "PENDING_APPROVAL"
    assert repository.get_recovery_workflow(shipment_id, run_a)["status"] == "COMPLETED"
    assert repository.get_recovery_workflow(shipment_id, run_b)["status"] == "PENDING_APPROVAL"
    assert {event["event_type"] for event in repository.get_audit_events(shipment_id, run_a)} == {
        "RECOVERY_EXECUTED",
        "STATE_VERIFIED",
    }
    assert repository.get_audit_events(shipment_id, run_b) == []


def test_recovery_execution_writes_audits_only_for_its_run():
    repository = InMemoryStateRepository()
    state = OperationalState(repository=repository)
    run_a = "RUN-A"
    run_b = "RUN-B"
    execute_recovery = next(
        tool
        for tool in create_recovery_tools(
            state,
            run_id=run_a,
            event_id="EVENT-A",
            runtime_session_id="SESSION-A",
        )
        if tool.tool_name == "execute_recovery_action"
    )

    result = execute_recovery.__wrapped__("SHP-0048", "EXPEDITED_TRANSPORT")
    run_a_events = repository.get_audit_events("SHP-0048", run_a)

    assert result["executed"] is True
    assert {event["event_type"] for event in run_a_events} >= {
        "RECOVERY_EXECUTED",
        "STATE_VERIFIED",
    }
    assert all(event["run_id"] == run_a for event in run_a_events)
    assert repository.get_audit_events("SHP-0048", run_b) == []