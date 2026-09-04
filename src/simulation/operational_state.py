from pathlib import Path
# from datetime import datetime, timezone
import pandas as pd
from src.state.state_repository_factory import (
    create_state_repository,
)
from src.state.state_repository import StateRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PARQUET_DIR = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "parquet"
)


class OperationalState:
    """
    Current operational state of the simulated
    supply-chain network.

    Parquet files provide the baseline state.
    Runtime events mutate the in-memory state.
    """

    def __init__(self, repository: StateRepository | None = None,):

        # ----------------------------------------------------
        # Load baseline data
        # ----------------------------------------------------

        self.shipments = pd.read_parquet(PARQUET_DIR / "shipments.parquet")
        self.inventory = pd.read_parquet(PARQUET_DIR / "inventory.parquet")
        self.events = pd.read_parquet(PARQUET_DIR / "events.parquet")

        # Runtime events are kept separate from historical events.
        self.runtime_events = []

                # State persistence is provided through a repository.
        self.repository = (
            repository
            if repository is not None
            else create_state_repository()
        )

        # # Pending human approval for recovery decisions
        # self.pending_recovery_approval = None

        # # Recovery workflow state is separate from shipment status.
        # self.recovery_workflows = {}

        # # Audit trail for agent/system actions.
        # self.audit_events = []

    # ========================================================
    # SHIPMENT
    # ========================================================

    def get_shipment(
        self,
        shipment_id: str,
    ):
        """
        Return the current live state of a shipment.
        """

        matches = self.shipments[
            self.shipments["shipment_id"]
            == shipment_id
        ]

        if matches.empty:
            return None

        return matches.iloc[0].to_dict()

    # ========================================================
    # RECOVERY APPROVAL
    # ========================================================

    def set_pending_recovery_approval(
        self,
        approval: dict,
    ):
        """
        Store the recovery decision awaiting human approval.

        This contains information already produced by the
        recovery workflow. It does not recalculate anything.
        """
        self.repository.set_pending_recovery_approval(approval)

    def get_pending_recovery_approval(self, shipment_id: str):
        """
        Return the recovery decision currently awaiting
        human approval.
        """
        return self.repository.get_pending_recovery_approval(shipment_id)

    def clear_pending_recovery_approval(self, shipment_id: str):
        """
        Clear the pending approval after the decision has
        been handled.
        """
        self.repository.clear_pending_recovery_approval(shipment_id)

    # ========================================================
    # RECOVERY WORKFLOW
    # ========================================================

    def set_recovery_workflow(
        self,
        shipment_id: str,
        status: str,
        action: str | None = None,
    ):
        """
        Store the current recovery workflow state for a shipment.

        This is separate from the shipment's operational status.
        """
        self.repository.set_recovery_workflow(
            shipment_id=shipment_id,
            status=status,
            action=action,
        )

    def get_recovery_workflow(
        self,
        shipment_id: str,
    ):
        """
        Return the current recovery workflow state.
        """
        return self.repository.get_recovery_workflow(shipment_id)

    def clear_recovery_workflow(
        self,
        shipment_id: str,
    ):
        """
        Remove the recovery workflow state for a shipment.
        """
        self.repository.clear_recovery_workflow(shipment_id)

    # ========================================================
    # AUDIT TRAIL
    # ========================================================

    def record_audit_event(
        self,
        event_type: str,
        shipment_id: str,
        details: dict | None = None,
    ):
        """
        Record an agent/system event in the audit trail.

        Audit events describe what happened during the recovery
        workflow. They do not replace operational runtime events.
        """

        # event = {
        #     "event_type": event_type,
        #     "shipment_id": shipment_id,
        #     "timestamp": datetime.now(
        #         timezone.utc
        #     ).isoformat(),
        #     "details": details or {},
        # }

        # self.audit_events.append(event)

        return self.repository.record_audit_event(
            event_type=event_type,
            shipment_id=shipment_id,
            details=details,
        )

    def get_audit_events(
        self,
        shipment_id: str | None = None,
    ):
        """
        Return audit events, optionally filtered by shipment.
        """

        # if shipment_id is None:
        #     return self.audit_events

        return self.repository.get_audit_events(
            shipment_id=shipment_id
        )

    # ========================================================
    # SHIPMENT DELAY
    # ========================================================

    def apply_shipment_delay(
        self,
        shipment_id: str,
        delay_minutes: int,
    ):
        """
        Apply an additional delay to a shipment.

        The baseline Parquet data is not modified.
        Only the in-memory operational state changes.
        """

        if delay_minutes <= 0:
            raise ValueError(
                "delay_minutes must be greater than zero."
            )

        shipment_index = self.shipments.index[
            self.shipments["shipment_id"]
            == shipment_id
        ]

        if len(shipment_index) == 0:
            raise ValueError(
                f"Shipment {shipment_id} not found."
            )

        index = shipment_index[0]

        # ----------------------------------------------------
        # Current ETA
        # ----------------------------------------------------

        current_eta = pd.to_datetime(
            self.shipments.at[
                index,
                "current_eta",
            ]
        )

        # ----------------------------------------------------
        # Apply additional delay
        # ----------------------------------------------------

        new_eta = (
            current_eta
            + pd.Timedelta(
                minutes=delay_minutes
            )
        )

        self.shipments.at[
            index,
            "current_eta",
        ] = new_eta

        # ----------------------------------------------------
        # Update shipment status
        # ----------------------------------------------------

        self.shipments.at[
            index,
            "shipment_status",
        ] = "DELAYED"

        return self.get_shipment(
            shipment_id
        )

    # ========================================================
    # RECOVERY ACTION
    # ========================================================

    def apply_recovery_action(
        self,
        shipment_id: str,
        option_type: str,
        recovery_hours: float,
        recovery_cost_eur: float,
    ):
        """
        Apply an approved recovery action to a shipment.

        The baseline Parquet data is not modified.
        Only the in-memory operational state changes.

        Args:
            shipment_id:
                Shipment being recovered.

            option_type:
                Recovery action being executed.

            recovery_hours:
                Expected recovery time in hours.

            recovery_cost_eur:
                Cost of the recovery action.

        Returns:
            Updated shipment state.
        """

        if recovery_hours <= 0:
            raise ValueError(
                "recovery_hours must be greater than zero."
            )

        shipment_index = self.shipments.index[
            self.shipments["shipment_id"]
            == shipment_id
        ]

        if len(shipment_index) == 0:
            raise ValueError(
                f"Shipment {shipment_id} not found."
            )

        index = shipment_index[0]

        current_eta = pd.to_datetime(
            self.shipments.at[
                index,
                "current_eta",
            ]
        )

        # ----------------------------------------------------
        # Reduce the current ETA by the expected recovery time
        # ----------------------------------------------------

        recovery_delta = pd.Timedelta(
            hours=recovery_hours
        )

        new_eta = current_eta - recovery_delta

        # Never allow recovery to move ETA before original ETA.
        original_eta = pd.to_datetime(
            self.shipments.at[
                index,
                "original_eta",
            ]
        )

        new_eta = max(
            new_eta,
            original_eta,
        )

        self.shipments.at[
            index,
            "current_eta",
        ] = new_eta

        # ----------------------------------------------------
        # Update shipment status
        # ----------------------------------------------------

        self.shipments.at[
            index,
            "shipment_status",
        ] = "RECOVERY_IN_PROGRESS"

        # ----------------------------------------------------
        # Record recovery action
        # ----------------------------------------------------

        recovery_event = {
            "event_type": "RECOVERY_ACTION",
            "shipment_id": shipment_id,
            "option_type": option_type,
            "recovery_hours": float(
                recovery_hours
            ),
            "recovery_cost_eur": float(
                recovery_cost_eur
            ),
        }

        self.runtime_events.append(
            recovery_event
        )

        return self.get_shipment(
            shipment_id
        )
    
    # ========================================================
    # DERIVED DELAY
    # ========================================================

    def get_shipment_delay(
        self,
        shipment_id: str,
    ):
        """
        Calculate the current shipment delay
        relative to the original ETA.
        """

        shipment = self.get_shipment(
            shipment_id
        )

        if shipment is None:
            return None

        original_eta = pd.to_datetime(
            shipment["original_eta"]
        )

        current_eta = pd.to_datetime(
            shipment["current_eta"]
        )

        delay = (
            current_eta
            - original_eta
        )

        return int(
            delay.total_seconds() / 60
        )

    # ========================================================
    # INVENTORY
    # ========================================================

    def get_inventory(
        self,
        warehouse_id: str,
        product_id: str,
    ):
        """
        Return the current live inventory state.
        """

        matches = self.inventory[
            (self.inventory["warehouse_id"] == warehouse_id)
            & (self.inventory["product_id"] == product_id)
        ]

        if matches.empty:
            return None

        return matches.iloc[0].to_dict()

    # ========================================================
    # RUNTIME EVENTS
    # ========================================================

    def add_runtime_event(
        self,
        event: dict,
    ):
        """
        Store a runtime event and apply its
        operational consequences.
        """

        self.runtime_events.append(
            event
        )

        event_type = event["event_type"]

        if event_type in {
            "TRAFFIC_DELAY",
            "WEATHER_DISRUPTION",
            "VEHICLE_BREAKDOWN",
            "CUSTOMS_DELAY",
        }:

            self.apply_shipment_delay(
                shipment_id=event["shipment_id"],
                delay_minutes=event["delay_minutes"],
            )

    # ========================================================
    # ACTIVE EVENTS
    # ========================================================

    def get_active_events(
        self,
        shipment_id: str | None = None,
    ):
        """
        Return currently active simulated events.
        """

        events = self.runtime_events

        if shipment_id is not None:

            events = [
                event
                for event in events
                if event["shipment_id"]
                == shipment_id
            ]

        return events