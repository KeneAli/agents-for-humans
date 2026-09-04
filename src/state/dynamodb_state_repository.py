from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key

from .state_repository import StateRepository
from decimal import Decimal



class DynamoDBStateRepository(StateRepository):

    def __init__(
        self,
        table_name: str = "agents-for-humans-state",
        region_name: str = "us-east-1",
    ):
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=region_name,
        )

        self.table = dynamodb.Table(table_name)

    def _to_dynamodb_compatible(
        self,
        value: Any,
    ):
        if isinstance(value, float):
            return Decimal(str(value))

        if isinstance(value, dict):
            return {
                key: self._to_dynamodb_compatible(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                self._to_dynamodb_compatible(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                self._to_dynamodb_compatible(item)
                for item in value
            ]

        return value

    def _shipment_key(
        self,
        shipment_id: str,
        item_type: str,
    ) -> dict:
        return {
            "pk": f"SHIPMENT#{shipment_id}",
            "sk": item_type,
        }

    # RECOVERY APPROVAL

    def set_pending_recovery_approval(
        self,
        approval: dict | None,
    ) -> None:

        if approval is None:
            return

        shipment_id = approval["shipment_id"]

        self.table.put_item(
            Item=self._to_dynamodb_compatible(
                {
                **self._shipment_key(
                    shipment_id,
                    "APPROVAL",
                ),
                "entity_type": "RECOVERY_APPROVAL",
                "data": approval,
            }
        )
    )

    def get_pending_recovery_approval(
        self,
        shipment_id: str,
    ) -> dict | None:

        response = self.table.get_item(
            Key=self._shipment_key(
                shipment_id,
                "APPROVAL",
            )
        )

        item = response.get("Item")

        if item is None:
            return None

        return item["data"]

    def clear_pending_recovery_approval(
        self,
        shipment_id: str,
    ) -> None:

        self.table.delete_item(
            Key=self._shipment_key(
                shipment_id,
                "APPROVAL",
            )
        )

    # RECOVERY WORKFLOW

    def set_recovery_workflow(
        self,
        shipment_id: str,
        status: str,
        action: str | None = None,
    ) -> None:

        self.table.put_item(
            Item= self._to_dynamodb_compatible({
                **self._shipment_key(
                    shipment_id,
                    "WORKFLOW",
                ),
                "entity_type": "RECOVERY_WORKFLOW",
                "data": {
                    "shipment_id": shipment_id,
                    "status": status,
                    "action": action,
                },
            })
        )

    def get_recovery_workflow(
        self,
        shipment_id: str,
    ) -> dict | None:

        response = self.table.get_item(
            Key=self._shipment_key(
                shipment_id,
                "WORKFLOW",
            )
        )

        item = response.get("Item")

        if item is None:
            return None

        return item["data"]

    def clear_recovery_workflow(
        self,
        shipment_id: str,
    ) -> None:

        self.table.delete_item(
            Key=self._shipment_key(
                shipment_id,
                "WORKFLOW",
            )
        )

    # AUDIT TRAIL

    def record_audit_event(
        self,
        event_type: str,
        shipment_id: str,
        details: dict[str, Any] | None = None,
    ) -> dict:

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        event = {
            "event_type": event_type,
            "shipment_id": shipment_id,
            "timestamp": timestamp,
            "details": details or {},
        }

        self.table.put_item(
            Item= self._to_dynamodb_compatible({
                **self._shipment_key(
                    shipment_id,
                    f"AUDIT#{timestamp}#{uuid4()}",
                ),
                "entity_type": "AUDIT_EVENT",
                **event,
            })
        )

        return event

    def get_audit_events(
        self,
        shipment_id: str | None = None,
    ) -> list[dict]:

        if shipment_id is None:
            raise ValueError(
                "DynamoDB audit lookup requires a shipment_id."
            )

        response = self.table.query(
            KeyConditionExpression=(
                Key("pk").eq(
                    f"SHIPMENT#{shipment_id}"
                )
                & Key("sk").begins_with("AUDIT#")
            ),
            ScanIndexForward=True,
        )

        return [
            {
                "event_type": item["event_type"],
                "shipment_id": item["shipment_id"],
                "timestamp": item["timestamp"],
                "details": item.get("details", {}),
            }
            for item in response.get("Items", [])
        ]