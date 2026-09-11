from datetime import datetime, timezone
from typing import Any

from .state_repository import StateRepository


class InMemoryStateRepository(StateRepository):

    def __init__(self):
        self.pending_recovery_approvals = {}
        self.recovery_workflows = {}
        self.audit_events = []
        self.claimed_disruption_event_ids = set()

    def set_pending_recovery_approval(
        self,
        approval: dict | None,
    ) -> None:
        if approval is None:
            return
        shipment_id = approval["shipment_id"]
        run_id = approval["run_id"]
        self.pending_recovery_approvals[(shipment_id, run_id)] = approval

    def get_pending_recovery_approval(
        self,
        shipment_id: str,
        run_id: str,
    ) -> dict | None:
        return self.pending_recovery_approvals.get((shipment_id, run_id))

    def clear_pending_recovery_approval(
        self,
        shipment_id: str,
        run_id: str,
    ) -> None:
        self.pending_recovery_approvals.pop((shipment_id, run_id), None)

    def set_recovery_workflow(
        self,
        shipment_id: str,
        run_id: str,
        status: str,
        action: str | None = None,
        event_id: str | None = None,
        runtime_session_id: str | None = None,
    ) -> None:
        self.recovery_workflows[(shipment_id, run_id)] = {
            "shipment_id": shipment_id,
            "run_id": run_id,
            "event_id": event_id,
            "runtime_session_id": runtime_session_id,
            "status": status,
            "action": action,
        }

    def get_recovery_workflow(
        self,
        shipment_id: str,
        run_id: str,
    ) -> dict | None:
        return self.recovery_workflows.get((shipment_id, run_id))

    def clear_recovery_workflow(
        self,
        shipment_id: str,
        run_id: str,
    ) -> None:
        self.recovery_workflows.pop((shipment_id, run_id), None)

    def record_audit_event(
        self,
        event_type: str,
        shipment_id: str,
        run_id: str,
        details: dict[str, Any] | None = None,
        event_id: str | None = None,
        runtime_session_id: str | None = None,
    ) -> None:
        self.audit_events.append(
            {
                "event_type": event_type,
                "shipment_id": shipment_id,
                "run_id": run_id,
                "event_id": event_id,
                "runtime_session_id": runtime_session_id,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "details": details or {},
            }
        )

    def get_audit_events(
        self,
        shipment_id: str | None = None,
        run_id: str | None = None,
    ) -> list[dict]:

        if shipment_id is None:
            if run_id is not None:
                raise ValueError("run_id requires shipment_id.")
            return list(self.audit_events)

        return [
            event
            for event in self.audit_events
            if event["shipment_id"]
            == shipment_id
            and (run_id is None or event["run_id"] == run_id)
        ]

    def claim_disruption_event(
        self,
        event_id: str,
        shipment_id: str,
        event: dict,
    ) -> bool:
        if event_id in self.claimed_disruption_event_ids:
            return False

        self.claimed_disruption_event_ids.add(event_id)
        return True