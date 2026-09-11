from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

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

    def _run_key(
        self,
        shipment_id: str,
        run_id: str,
        item_type: str,
    ) -> dict:
        return self._shipment_key(shipment_id, f"RUN#{run_id}#{item_type}")

    # RECOVERY APPROVAL

    def set_pending_recovery_approval(
        self,
        approval: dict | None,
    ) -> None:

        if approval is None:
            return

        shipment_id = approval["shipment_id"]
        run_id = approval["run_id"]

        self.table.put_item(
            Item=self._to_dynamodb_compatible(
                {
                **self._run_key(
                    shipment_id,
                    run_id,
                    "APPROVAL",
                ),
                "entity_type": "RECOVERY_APPROVAL",
                "run_id": run_id,
                "shipment_id": shipment_id,
                "event_id": approval.get("event_id"),
                "runtime_session_id": approval.get("runtime_session_id"),
                "data": approval,
            }
        )
    )

    def get_pending_recovery_approval(
        self,
        shipment_id: str,
        run_id: str,
    ) -> dict | None:

        response = self.table.get_item(
            Key=self._run_key(
                shipment_id,
                run_id,
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
        run_id: str,
    ) -> None:

        self.table.delete_item(
            Key=self._run_key(
                shipment_id,
                run_id,
                "APPROVAL",
            )
        )

    # RECOVERY WORKFLOW

    def set_recovery_workflow(
        self,
        shipment_id: str,
        run_id: str,
        status: str,
        action: str | None = None,
        event_id: str | None = None,
        runtime_session_id: str | None = None,
    ) -> None:

        self.table.put_item(
            Item= self._to_dynamodb_compatible({
                **self._run_key(
                    shipment_id,
                    run_id,
                    "WORKFLOW",
                ),
                "entity_type": "RECOVERY_WORKFLOW",
                "run_id": run_id,
                "shipment_id": shipment_id,
                "event_id": event_id,
                "runtime_session_id": runtime_session_id,
                "data": {
                    "shipment_id": shipment_id,
                    "run_id": run_id,
                    "event_id": event_id,
                    "runtime_session_id": runtime_session_id,
                    "status": status,
                    "action": action,
                },
            })
        )

    def get_recovery_workflow(
        self,
        shipment_id: str,
        run_id: str,
    ) -> dict | None:

        response = self.table.get_item(
            Key=self._run_key(
                shipment_id,
                run_id,
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
        run_id: str,
    ) -> None:

        self.table.delete_item(
            Key=self._run_key(
                shipment_id,
                run_id,
                "WORKFLOW",
            )
        )

    # AUDIT TRAIL

    def record_audit_event(
        self,
        event_type: str,
        shipment_id: str,
        run_id: str,
        details: dict[str, Any] | None = None,
        event_id: str | None = None,
        runtime_session_id: str | None = None,
    ) -> dict:

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        event = {
            "event_type": event_type,
            "shipment_id": shipment_id,
            "run_id": run_id,
            "event_id": event_id,
            "runtime_session_id": runtime_session_id,
            "timestamp": timestamp,
            "details": details or {},
        }

        self.table.put_item(
            Item= self._to_dynamodb_compatible({
                **self._run_key(
                    shipment_id,
                    run_id,
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
        run_id: str | None = None,
    ) -> list[dict]:

        if shipment_id is None:
            raise ValueError(
                "DynamoDB audit lookup requires a shipment_id."
            )
        if run_id is None:
            raise ValueError("DynamoDB audit lookup requires a run_id.")

        response = self.table.query(
            KeyConditionExpression=(
                Key("pk").eq(
                    f"SHIPMENT#{shipment_id}"
                )
                & Key("sk").begins_with(f"RUN#{run_id}#AUDIT#")
            ),
            ScanIndexForward=True,
        )

        return [
            {
                "event_type": item["event_type"],
                "shipment_id": item["shipment_id"],
                "run_id": item["run_id"],
                "event_id": item.get("event_id"),
                "runtime_session_id": item.get("runtime_session_id"),
                "timestamp": item["timestamp"],
                "details": item.get("details", {}),
            }
            for item in response.get("Items", [])
        ]

    def claim_disruption_event(
        self,
        event_id: str,
        shipment_id: str,
        event: dict,
    ) -> bool:
        try:
            self.table.put_item(
                Item=self._to_dynamodb_compatible(
                    {
                        **self._shipment_key(
                            shipment_id,
                            f"EVENT#{event_id}",
                        ),
                        "entity_type": "DISRUPTION_EVENT",
                        "event_id": event_id,
                        "shipment_id": shipment_id,
                        "event": event,
                    }
                ),
                ConditionExpression="attribute_not_exists(pk)",
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise

        return True