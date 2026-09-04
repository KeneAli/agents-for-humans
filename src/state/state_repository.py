from abc import ABC, abstractmethod
from typing import Any


class StateRepository(ABC):

    @abstractmethod
    def set_pending_recovery_approval(
        self,
        approval: dict | None,
    ) -> None:
        pass

    @abstractmethod
    def get_pending_recovery_approval(
        self,
        shipment_id: str,
    ) -> dict | None:
        pass

    @abstractmethod
    def clear_pending_recovery_approval(
        self,
        shipment_id: str,
    ) -> None:
        pass

    @abstractmethod
    def set_recovery_workflow(
        self,
        shipment_id: str,
        status: str,
        action: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    def get_recovery_workflow(
        self,
        shipment_id: str,
    ) -> dict | None:
        pass

    @abstractmethod
    def clear_recovery_workflow(
        self,
        shipment_id: str,
    ) -> None:
        pass

    @abstractmethod
    def record_audit_event(
        self,
        event_type: str,
        shipment_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        pass

    @abstractmethod
    def get_audit_events(
        self,
        shipment_id: str | None = None,
    ) -> list[dict]:
        pass