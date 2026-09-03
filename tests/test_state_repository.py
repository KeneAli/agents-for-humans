from src.state.in_memory_state_repository import (
    InMemoryStateRepository,
)
from src.simulation.operational_state import OperationalState


def test_pending_recovery_approval():
    repository = InMemoryStateRepository()

    approval = {
        "shipment_id": "SHP-0048",
        "selected_option": "EXPEDITED_TRANSPORT",
    }

    repository.set_pending_recovery_approval(
        approval
    )

    assert (
        repository.get_pending_recovery_approval()
        == approval
    )

    repository.clear_pending_recovery_approval()

    assert (
        repository.get_pending_recovery_approval()
        is None
    )


def test_recovery_workflow():
    repository = InMemoryStateRepository()

    repository.set_recovery_workflow(
        shipment_id="SHP-0048",
        status="AWAITING_APPROVAL",
        action="EXPEDITED_TRANSPORT",
    )

    workflow = repository.get_recovery_workflow(
        "SHP-0048"
    )

    assert workflow == {
        "shipment_id": "SHP-0048",
        "status": "AWAITING_APPROVAL",
        "action": "EXPEDITED_TRANSPORT",
    }


def test_audit_events():
    repository = InMemoryStateRepository()

    repository.record_audit_event(
        event_type="RECOVERY_SELECTED",
        shipment_id="SHP-0048",
        details={
            "option_type": "EXPEDITED_TRANSPORT",
        },
    )

    events = repository.get_audit_events(
        "SHP-0048"
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

def test_operational_state_uses_injected_repository():
    repository = InMemoryStateRepository()
    state = OperationalState(repository=repository)

    approval = {
        "shipment_id": "SHP-0048",
        "selected_option": "EXPEDITED_TRANSPORT",
    }

    state.set_pending_recovery_approval(approval)

    assert (
        repository.get_pending_recovery_approval()
        == approval
    )

    state.set_recovery_workflow(
        shipment_id="SHP-0048",
        status="AWAITING_APPROVAL",
        action="EXPEDITED_TRANSPORT",
    )

    assert (
        repository.get_recovery_workflow("SHP-0048")
        == {
            "shipment_id": "SHP-0048",
            "status": "AWAITING_APPROVAL",
            "action": "EXPEDITED_TRANSPORT",
        }
    )

    state.record_audit_event(
        event_type="RECOVERY_SELECTED",
        shipment_id="SHP-0048",
        details={
            "option_type": "EXPEDITED_TRANSPORT",
        },
    )

    events = repository.get_audit_events("SHP-0048")

    assert len(events) == 1
    assert events[0]["event_type"] == "RECOVERY_SELECTED"