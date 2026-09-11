import os

import pytest

from src.state.dynamodb_state_repository import (
    DynamoDBStateRepository,
)


if os.getenv("RUN_AWS_INTEGRATION_TESTS") != "1":
    pytestmark = pytest.mark.skip(
        reason="AWS integration tests disabled"
    )


def test_dynamodb_persistence():
    repository = DynamoDBStateRepository()

    shipment_id = "SHP-DDB-TEST-001"
    run_id = "RUN-DDB-TEST-001"

    approval = {
        "shipment_id": shipment_id,
        "run_id": run_id,
        "selected_option": "EXPEDITED_TRANSPORT",
        "current_delay_minutes": 480,
    }

    repository.set_pending_recovery_approval(
        approval
    )

    assert (
        repository.get_pending_recovery_approval(
            shipment_id, run_id
        )
        == approval
    )

    repository.set_recovery_workflow(
        shipment_id=shipment_id,
        run_id=run_id,
        status="AWAITING_APPROVAL",
        action="EXPEDITED_TRANSPORT",
    )

    assert (
        repository.get_recovery_workflow(
            shipment_id, run_id
        )
        == {
            "shipment_id": shipment_id,
            "run_id": run_id,
            "event_id": None,
            "runtime_session_id": None,
            "status": "AWAITING_APPROVAL",
            "action": "EXPEDITED_TRANSPORT",
        }
    )

    repository.record_audit_event(
        event_type="TEST_EVENT",
        shipment_id=shipment_id,
        run_id=run_id,
        details={
            "source": "dynamodb_integration_test",
        },
    )

    events = repository.get_audit_events(
        shipment_id
        , run_id
    )

    assert len(events) == 1
    assert events[0]["event_type"] == "TEST_EVENT"
    assert events[0]["shipment_id"] == shipment_id
    assert events[0]["run_id"] == run_id
    assert events[0]["details"] == {
        "source": "dynamodb_integration_test",
    }

    repository.clear_pending_recovery_approval(
        shipment_id, run_id
    )

    repository.clear_recovery_workflow(
        shipment_id, run_id
    )

    assert (
        repository.get_pending_recovery_approval(
            shipment_id, run_id
        )
        is None
    )

    assert (
        repository.get_recovery_workflow(
            shipment_id, run_id
        )
        is None
    )