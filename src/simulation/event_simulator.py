from datetime import datetime, timezone
from uuid import uuid4

from src.simulation.operational_state import OperationalState
from src.business.consequence_engine import (
    ConsequenceEngine,
)


SUPPORTED_DISRUPTIONS = {
    "TRAFFIC_DELAY",
    "WEATHER_DISRUPTION",
    "VEHICLE_BREAKDOWN",
    "CUSTOMS_DELAY",
}


SEVERITY_THRESHOLDS = {
    "LOW": 120,
    "MEDIUM": 360,
    "HIGH": 720,
}


def determine_severity(delay_minutes: int) -> str:
    """
    Determine operational severity based on
    the simulated disruption duration.
    """

    if delay_minutes < SEVERITY_THRESHOLDS["LOW"]:
        return "LOW"

    if delay_minutes < SEVERITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"

    if delay_minutes < SEVERITY_THRESHOLDS["HIGH"]:
        return "HIGH"

    return "CRITICAL"

def validate_scenario(
    state: OperationalState,
    shipment_id: str,
    event_type: str,
    delay_minutes: int,
) -> None:
    """
    Validate a disruption scenario before it is injected
    into the operational state.
    """

    if not shipment_id:
        raise ValueError(
            "shipment_id is required."
        )

    if event_type not in SUPPORTED_DISRUPTIONS:
        raise ValueError(
            f"Unsupported disruption type: {event_type}. "
            f"Supported types: "
            f"{sorted(SUPPORTED_DISRUPTIONS)}"
        )

    if not isinstance(
        delay_minutes,
        int,
    ):
        raise ValueError(
            "delay_minutes must be an integer."
        )

    if delay_minutes <= 0:
        raise ValueError(
            "delay_minutes must be greater than zero."
        )

    shipment = state.get_shipment(
        shipment_id
    )

    if shipment is None:
        raise ValueError(
            f"Shipment {shipment_id} not found."
        )

def simulate_disruption(
    state: OperationalState,
    shipment_id: str,
    event_type: str,
    delay_minutes: int,
):
    """
    Inject a generic runtime operational disruption.
    """

    validate_scenario(
        state=state,
        shipment_id=shipment_id,
        event_type=event_type,
        delay_minutes=delay_minutes,
    )

    severity = determine_severity(
        delay_minutes
    )

    event = {
        "event_id": (
            f"SIM-{uuid4().hex[:8].upper()}"
        ),
        "event_type": event_type,
        "shipment_id": shipment_id,
        "delay_minutes": delay_minutes,
        "severity": severity,
        "source": "simulation_ui",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "description": (
            f"{event_type.replace('_', ' ').title()} "
            f"causing an estimated "
            f"{delay_minutes}-minute disruption."
        ),
    }

    state.add_runtime_event(
        event
    )

    return event


if __name__ == "__main__":

    state = OperationalState()

    # Use real shipment IDs from the generated dataset.
    available_shipments = (
        state.shipments["shipment_id"]
        .tolist()
    )

    # Use the first few real shipments for testing.
    test_shipments = available_shipments[:4]

    scenarios = [
        {
            "shipment_id": test_shipments[0],
            "event_type": "TRAFFIC_DELAY",
            "delay_minutes": 480,
        },
        {
            "shipment_id": test_shipments[1],
            "event_type": "VEHICLE_BREAKDOWN",
            "delay_minutes": 300,
        },
        {
            "shipment_id": test_shipments[2],
            "event_type": "WEATHER_DISRUPTION",
            "delay_minutes": 180,
        },
        {
            "shipment_id": test_shipments[3],
            "event_type": "CUSTOMS_DELAY",
            "delay_minutes": 720,
        },
    ]

    print("\n=== SCENARIO VALIDATION TEST ===")

    valid_scenarios = []

    for scenario in scenarios:

        try:

            validate_scenario(
                state=state,
                **scenario,
            )

            print(
                f"✓ VALID | "
                f"{scenario['shipment_id']} | "
                f"{scenario['event_type']} | "
                f"{scenario['delay_minutes']} min"
            )

            valid_scenarios.append(
                scenario
            )

        except ValueError as error:

            print(
                f"✗ INVALID | "
                f"{scenario} | "
                f"{error}"
            )

    print("\n=== SCENARIO EXECUTION TEST ===")

    for scenario in valid_scenarios:

        event = simulate_disruption(
            state=state,
            **scenario,
        )

        shipment = state.get_shipment(
            scenario["shipment_id"]
        )

        print(
            f"\n✓ {event['event_type']}"
        )

        print(
            f"  Shipment: "
            f"{shipment['shipment_id']}"
        )

        print(
            f"  Status: "
            f"{shipment['shipment_status']}"
        )

        print(
            f"  Delay: "
            f"{state.get_shipment_delay(
                scenario['shipment_id']
            )} minutes"
        )

        print(
            f"  Severity: "
            f"{event['severity']}"
        )

        consequence_engine = (
            ConsequenceEngine()
        )

        consequences = (
            consequence_engine
            .calculate_shipment_consequences(
                shipment
            )
        )

        print("\n=== BUSINESS CONSEQUENCES ===")

        print(
            f"SLA deadline: "
            f"{consequences['sla_deadline']}"
        )

        print(
            f"SLA breached: "
            f"{consequences['sla_breached']}"
        )

        print(
            f"SLA breach: "
            f"{consequences['sla_breach_hours']:.1f} hours"
        )

        print(
            f"Penalty rate: €"
            f"{consequences['sla_penalty_per_hour_eur']:.2f}/hour"
        )

        print(
            f"Projected SLA penalty: €"
            f"{consequences['projected_sla_penalty_eur']:.2f}"
        )