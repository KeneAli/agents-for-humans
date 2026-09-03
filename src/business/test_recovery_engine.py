from pathlib import Path

import pandas as pd

from src.business.consequence_engine import ConsequenceEngine
from src.business.recovery_engine import RecoveryEngine
from src.simulation.operational_state import OperationalState
from src.simulation.event_simulator import simulate_disruption


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PARQUET_DIR = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "parquet"
)


def main():

    shipments = pd.read_parquet(
        PARQUET_DIR / "shipments.parquet"
    )

    # Use an actual shipment from the generated dataset.
    shipment_id = "SHP-0048"

    shipment = shipments[
        shipments["shipment_id"]
        == shipment_id
    ]

    if shipment.empty:
        raise ValueError(
            f"Shipment {shipment_id} not found."
        )

    shipment = shipment.iloc[0].to_dict()

    print("\n=== RECOVERY ENGINE TEST ===")

    print(
        f"Shipment: "
        f"{shipment['shipment_id']}"
    )

    print(
        f"Order: "
        f"{shipment['order_id']}"
    )

    print(
        f"Route: "
        f"{shipment['origin_warehouse_id']}"
        f" → "
        f"{shipment['destination_warehouse_id']}"
    )

    print(
        f"Quantity: "
        f"{shipment['quantity_units']} units"
    )

    # -----------------------------------------------------
    # CREATE OPERATIONAL STATE
    # -----------------------------------------------------

    state = OperationalState()

    # -----------------------------------------------------
    # INJECT TEST DISRUPTION
    # -----------------------------------------------------

    simulate_disruption(
        state=state,
        shipment_id=shipment_id,
        event_type="VEHICLE_BREAKDOWN",
        delay_minutes=480,
    )

    # Retrieve the updated shipment.
    after = state.get_shipment(
        shipment_id
    )

    print("\n=== AFTER DISRUPTION ===")

    print(
        f"Status: "
        f"{after['shipment_status']}"
    )

    print(
        f"Delay: "
        f"{state.get_shipment_delay(shipment_id)} "
        f"minutes"
    )

    # -----------------------------------------------------
    # BUSINESS CONSEQUENCES
    # -----------------------------------------------------

    consequence_engine = (
        ConsequenceEngine()
    )

    consequences = (
        consequence_engine
        .calculate_shipment_consequences(
            after
        )
    )

    print("\n=== BUSINESS CONSEQUENCES ===")

    print(
        f"SLA penalty: "
        f"€{consequences['projected_sla_penalty_eur']:.2f}"
    )

    # -----------------------------------------------------
    # RECOVERY ENGINE
    # -----------------------------------------------------

    recovery_engine = (
        RecoveryEngine()
    )

    options = (
        recovery_engine
        .evaluate_recovery_options(
            after,
            consequences,
        )
    )

    print("\n=== RECOVERY OPTIONS ===")

    for index, option in enumerate(
        options,
        start=1,
    ):

        print(
            f"\n[{index}] "
            f"{option.option_type}"
        )

        print(
            f"Feasible: "
            f"{option.feasible}"
        )

        print(
            f"Description: "
            f"{option.description}"
        )

        print(
            f"Recovery cost: "
            f"€{option.recovery_cost_eur:.2f}"
        )

        print(
            f"Avoided SLA penalty: "
            f"€{option.avoided_sla_penalty_eur:.2f}"
        )

        print(
            f"Net benefit: "
            f"€{option.net_benefit_eur:.2f}"
        )

        print(
            f"Reason: "
            f"{option.reason}"
        )

        if option.source_warehouse_id:
            print(
                f"Source warehouse: "
                f"{option.source_warehouse_id}"
            )

        if option.destination_warehouse_id:
            print(
                f"Destination warehouse: "
                f"{option.destination_warehouse_id}"
            )

        if option.quantity_units:
            print(
                f"Quantity: "
                f"{option.quantity_units} units"
            )

        if option.estimated_recovery_hours:
            print(
                f"Estimated recovery time: "
                f"{option.estimated_recovery_hours:.1f} hours"
            )

        print(
            f"Safety stock protected: "
            f"{option.safety_stock_protected}"
        )


if __name__ == "__main__":
    main()