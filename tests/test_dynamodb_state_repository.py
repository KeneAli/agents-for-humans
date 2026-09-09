from unittest.mock import MagicMock, patch

from src.state.dynamodb_state_repository import (
    DynamoDBStateRepository,
)

from decimal import Decimal
from botocore.exceptions import ClientError


@patch("src.state.dynamodb_state_repository.boto3.resource")
def test_set_and_get_pending_recovery_approval(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table

    repository = DynamoDBStateRepository()

    approval = {
        "shipment_id": "SHP-0048",
        "selected_option": "EXPEDITED_TRANSPORT",
        "current_delay_minutes": 480,
    }

    repository.set_pending_recovery_approval(approval)

    table.put_item.assert_called_once_with(
        Item={
            "pk": "SHIPMENT#SHP-0048",
            "sk": "APPROVAL",
            "entity_type": "RECOVERY_APPROVAL",
            "data": approval,
        }
    )

    table.get_item.return_value = {
        "Item": {
            "pk": "SHIPMENT#SHP-0048",
            "sk": "APPROVAL",
            "entity_type": "RECOVERY_APPROVAL",
            "data": approval,
        }
    }

    result = repository.get_pending_recovery_approval(
        "SHP-0048"
    )

    assert result == approval

    table.get_item.assert_called_once_with(
        Key={
            "pk": "SHIPMENT#SHP-0048",
            "sk": "APPROVAL",
        }
    )


@patch("src.state.dynamodb_state_repository.boto3.resource")
def test_clear_pending_recovery_approval(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table

    repository = DynamoDBStateRepository()

    repository.clear_pending_recovery_approval(
        "SHP-0048"
    )

    table.delete_item.assert_called_once_with(
        Key={
            "pk": "SHIPMENT#SHP-0048",
            "sk": "APPROVAL",
        }
    )


@patch("src.state.dynamodb_state_repository.boto3.resource")
def test_recovery_workflow(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table

    repository = DynamoDBStateRepository()

    repository.set_recovery_workflow(
        shipment_id="SHP-0048",
        status="AWAITING_APPROVAL",
        action="EXPEDITED_TRANSPORT",
    )

    table.put_item.assert_called_once_with(
        Item={
            "pk": "SHIPMENT#SHP-0048",
            "sk": "WORKFLOW",
            "entity_type": "RECOVERY_WORKFLOW",
            "data": {
                "shipment_id": "SHP-0048",
                "status": "AWAITING_APPROVAL",
                "action": "EXPEDITED_TRANSPORT",
            },
        }
    )

    table.get_item.return_value = {
        "Item": {
            "pk": "SHIPMENT#SHP-0048",
            "sk": "WORKFLOW",
            "entity_type": "RECOVERY_WORKFLOW",
            "data": {
                "shipment_id": "SHP-0048",
                "status": "AWAITING_APPROVAL",
                "action": "EXPEDITED_TRANSPORT",
            },
        }
    }

    result = repository.get_recovery_workflow(
        "SHP-0048"
    )

    assert result == {
        "shipment_id": "SHP-0048",
        "status": "AWAITING_APPROVAL",
        "action": "EXPEDITED_TRANSPORT",
    }


@patch("src.state.dynamodb_state_repository.boto3.resource")
def test_audit_events(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table

    repository = DynamoDBStateRepository()

    event = repository.record_audit_event(
        event_type="RECOVERY_SELECTED",
        shipment_id="SHP-0048",
        details={
            "option_type": "EXPEDITED_TRANSPORT"
        },
    )

    assert event["event_type"] == "RECOVERY_SELECTED"
    assert event["shipment_id"] == "SHP-0048"
    assert event["details"] == {
        "option_type": "EXPEDITED_TRANSPORT"
    }
    assert "timestamp" in event

    stored_item = table.put_item.call_args.kwargs["Item"]

    assert stored_item["pk"] == "SHIPMENT#SHP-0048"
    assert stored_item["sk"].startswith("AUDIT#")
    assert stored_item["entity_type"] == "AUDIT_EVENT"
    assert stored_item["event_type"] == "RECOVERY_SELECTED"

    table.query.return_value = {
        "Items": [
            {
                "pk": "SHIPMENT#SHP-0048",
                "sk": "AUDIT#2026-08-21T10:00:00+00:00#1",
                "entity_type": "AUDIT_EVENT",
                "event_type": "RECOVERY_SELECTED",
                "shipment_id": "SHP-0048",
                "timestamp": "2026-08-21T10:00:00+00:00",
                "details": {
                    "option_type": "EXPEDITED_TRANSPORT"
                },
            }
        ]
    }

    events = repository.get_audit_events(
        "SHP-0048"
    )

    assert events == [
        {
            "event_type": "RECOVERY_SELECTED",
            "shipment_id": "SHP-0048",
            "timestamp": "2026-08-21T10:00:00+00:00",
            "details": {
                "option_type": "EXPEDITED_TRANSPORT"
            },
        }
    ]

    table.query.assert_called_once()

@patch("src.state.dynamodb_state_repository.boto3.resource")
def test_nested_float_values_are_converted_to_decimal(
    mock_resource,
):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table

    repository = DynamoDBStateRepository()

    approval = {
        "shipment_id": "SHP-FLOAT-TEST",
        "selected_option": "EXPEDITED_TRANSPORT",
        "current_delay_minutes": 480,
        "options": [
            {
                "option_type": "EXPEDITED_TRANSPORT",
                "recovery_cost_eur": 502.50,
                "net_benefit_eur": -22.50,
            }
        ],
    }

    repository.set_pending_recovery_approval(
        approval
    )

    written_item = (
        table.put_item.call_args.kwargs["Item"]
    )

    assert isinstance(
        written_item["data"]["options"][0][
            "recovery_cost_eur"
        ],
        Decimal,
    )

    assert isinstance(
        written_item["data"]["options"][0][
            "net_benefit_eur"
        ],
        Decimal,
    )


@patch("src.state.dynamodb_state_repository.boto3.resource")
def test_claim_disruption_event(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table

    repository = DynamoDBStateRepository()
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

    table.put_item.assert_called_once_with(
        Item={
            "pk": "SHIPMENT#SHP-0048",
            "sk": "EVENT#SIM-A1B2C3D4",
            "entity_type": "DISRUPTION_EVENT",
            "event_id": "SIM-A1B2C3D4",
            "shipment_id": "SHP-0048",
            "event": event,
        },
        ConditionExpression="attribute_not_exists(pk)",
    )


@patch("src.state.dynamodb_state_repository.boto3.resource")
def test_claim_disruption_event_returns_false_for_duplicate(mock_resource):
    table = MagicMock()
    mock_resource.return_value.Table.return_value = table

    table.put_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "The conditional request failed",
            }
        },
        "PutItem",
    )

    repository = DynamoDBStateRepository()

    assert repository.claim_disruption_event(
        event_id="SIM-A1B2C3D4",
        shipment_id="SHP-0048",
        event={
            "event_id": "SIM-A1B2C3D4",
            "event_type": "VEHICLE_BREAKDOWN",
            "shipment_id": "SHP-0048",
            "delay_minutes": 480,
        },
    ) is False