from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_DIR = PROJECT_ROOT / "data" / "generated" / "csv"
PARQUET_DIR = PROJECT_ROOT / "data" / "generated" / "parquet"


# ============================================================
# HISTORICAL EVENT CONFIGURATION
# ============================================================

DISRUPTION_TYPES = [
    "TRAFFIC_DELAY",
    "WEATHER_DISRUPTION",
    "CUSTOMS_DELAY",
    "VEHICLE_BREAKDOWN",
]

# Probability that a shipment experiences each type
# of historical disruption.
DISRUPTION_PROBABILITIES = np.array([
    0.08,  # Traffic
    0.05,  # Weather
    0.03,  # Customs
    0.03,  # Vehicle breakdown
])

# Overall historical disruption probability.
DISRUPTION_PROBABILITY = DISRUPTION_PROBABILITIES.sum()

# Normalized probabilities used after a disruption
# has been selected.
DISRUPTION_TYPE_PROBABILITIES = (
    DISRUPTION_PROBABILITIES
    / DISRUPTION_PROBABILITIES.sum()
)


DELAY_RANGES = {
    "TRAFFIC_DELAY": (30, 360),
    "WEATHER_DISRUPTION": (60, 480),
    "CUSTOMS_DELAY": (60, 720),
    "VEHICLE_BREAKDOWN": (90, 360),
}


# ============================================================
# HELPERS
# ============================================================

def determine_severity(delay_minutes: int) -> str:

    if delay_minutes < 120:
        return "LOW"

    if delay_minutes < 360:
        return "MEDIUM"

    if delay_minutes < 720:
        return "HIGH"

    return "CRITICAL"


def generate_disruption_description(
    disruption_type: str,
) -> str:

    descriptions = {
        "TRAFFIC_DELAY": (
            "Traffic congestion reported "
            "along shipment route."
        ),
        "WEATHER_DISRUPTION": (
            "Severe weather conditions "
            "affecting transport operations."
        ),
        "CUSTOMS_DELAY": (
            "Shipment held temporarily "
            "for customs processing."
        ),
        "VEHICLE_BREAKDOWN": (
            "Vehicle breakdown reported "
            "during transit."
        ),
    }

    return descriptions[disruption_type]


# ============================================================
# EVENT GENERATION
# ============================================================

def generate_events(
    shipments: pd.DataFrame,
) -> pd.DataFrame:

    events = []

    event_counter = 1

    for _, shipment in shipments.iterrows():

        shipment_id = shipment["shipment_id"]

        departure = pd.Timestamp(
            shipment["departure_time"]
        )

        original_eta = pd.Timestamp(
            shipment["original_eta"]
        )

        # ====================================================
        # 1. DEPARTURE
        # ====================================================

        events.append(
            {
                "event_id": f"EVT-{event_counter:06d}",
                "shipment_id": shipment_id,
                "event_timestamp": departure,
                "event_type": "DEPARTURE",
                "severity": "INFO",
                "delay_minutes": 0,
                "location": shipment[
                    "origin_warehouse_id"
                ],
                "description": (
                    "Shipment departed origin "
                    "distribution centre."
                ),
            }
        )

        event_counter += 1

        # ====================================================
        # 2. IN TRANSIT
        # ====================================================

        transit_time = departure + (
            original_eta - departure
        ) / 2

        events.append(
            {
                "event_id": f"EVT-{event_counter:06d}",
                "shipment_id": shipment_id,
                "event_timestamp": transit_time,
                "event_type": "IN_TRANSIT",
                "severity": "INFO",
                "delay_minutes": 0,
                "location": "EN_ROUTE",
                "description": (
                    "Shipment confirmed in transit."
                ),
            }
        )

        event_counter += 1

        # ====================================================
        # 3. HISTORICAL DISRUPTION
        # ====================================================

        has_disruption = (
            rng.random() < DISRUPTION_PROBABILITY
        )

        if has_disruption:

            disruption_type = rng.choice(
                DISRUPTION_TYPES,
                p=DISRUPTION_TYPE_PROBABILITIES,
            )

            minimum_delay, maximum_delay = (
                DELAY_RANGES[disruption_type]
            )

            delay_minutes = int(
                rng.integers(
                    minimum_delay,
                    maximum_delay + 1,
                )
            )

            severity = determine_severity(
                delay_minutes
            )

            # Historical disruption occurs during
            # the middle portion of the journey.
            event_time = departure + (
                original_eta - departure
            ) * rng.uniform(0.55, 0.80)

            location = shipment["route_id"]

            # ------------------------------------------------
            # DISRUPTION EVENT
            # ------------------------------------------------

            events.append(
                {
                    "event_id": f"EVT-{event_counter:06d}",
                    "shipment_id": shipment_id,
                    "event_timestamp": event_time,
                    "event_type": disruption_type,
                    "severity": severity,
                    "delay_minutes": delay_minutes,
                    "location": location,
                    "description": (
                        generate_disruption_description(
                            disruption_type
                        )
                    ),
                }
            )

            event_counter += 1

            # ------------------------------------------------
            # ETA UPDATE
            # ------------------------------------------------

            events.append(
                {
                    "event_id": f"EVT-{event_counter:06d}",
                    "shipment_id": shipment_id,
                    "event_timestamp": (
                        event_time
                        + pd.Timedelta(minutes=15)
                    ),
                    "event_type": "ETA_UPDATE",
                    "severity": severity,
                    "delay_minutes": delay_minutes,
                    "location": location,
                    "description": (
                        "Estimated arrival time updated "
                        "following operational disruption."
                    ),
                }
            )

            event_counter += 1

            # ------------------------------------------------
            # HISTORICAL RESOLUTION
            # ------------------------------------------------

            resolution_time = (
                event_time
                + pd.Timedelta(
                    minutes=delay_minutes
                )
            )

            events.append(
                {
                    "event_id": f"EVT-{event_counter:06d}",
                    "shipment_id": shipment_id,
                    "event_timestamp": resolution_time,
                    "event_type": "DISRUPTION_RESOLVED",
                    "severity": "INFO",
                    "delay_minutes": delay_minutes,
                    "location": location,
                    "description": (
                        "Historical operational disruption "
                        "resolved."
                    ),
                }
            )

            event_counter += 1

            # ------------------------------------------------
            # HISTORICAL ARRIVAL
            # ------------------------------------------------

            actual_arrival = (
                original_eta
                + pd.Timedelta(
                    minutes=delay_minutes
                )
            )

            events.append(
                {
                    "event_id": f"EVT-{event_counter:06d}",
                    "shipment_id": shipment_id,
                    "event_timestamp": actual_arrival,
                    "event_type": "ARRIVAL",
                    "severity": "INFO",
                    "delay_minutes": delay_minutes,
                    "location": shipment[
                        "destination_warehouse_id"
                    ],
                    "description": (
                        "Shipment arrived at destination "
                        "distribution centre after "
                        "historical disruption."
                    ),
                }
            )

            event_counter += 1

        else:

            # =================================================
            # NORMAL ARRIVAL
            # =================================================

            events.append(
                {
                    "event_id": f"EVT-{event_counter:06d}",
                    "shipment_id": shipment_id,
                    "event_timestamp": original_eta,
                    "event_type": "ARRIVAL",
                    "severity": "INFO",
                    "delay_minutes": 0,
                    "location": shipment[
                        "destination_warehouse_id"
                    ],
                    "description": (
                        "Shipment arrived at destination "
                        "distribution centre."
                    ),
                }
            )

            event_counter += 1

    events_df = pd.DataFrame(events)

    return events_df


# ============================================================
# SAVE
# ============================================================

def save_events(
    df: pd.DataFrame,
):

    CSV_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PARQUET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = CSV_DIR / "events.csv"

    parquet_path = (
        PARQUET_DIR / "events.parquet"
    )

    df.to_csv(
        csv_path,
        index=False,
    )

    df.to_parquet(
        parquet_path,
        index=False,
    )

    print(
        f"✓ events: {len(df):,} records"
    )

    print(
        f"✓ CSV: {csv_path}"
    )

    print(
        f"✓ Parquet: {parquet_path}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    shipments = pd.read_parquet(
        PARQUET_DIR / "shipments.parquet"
    )

    events = generate_events(
        shipments
    )

    save_events(events)