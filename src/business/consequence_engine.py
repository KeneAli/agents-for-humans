from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PARQUET_DIR = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "parquet"
)


class ConsequenceEngine:

    def __init__(self):

        self.shipments = pd.read_parquet(
            PARQUET_DIR / "shipments.parquet"
        )

        self.sla_rules = pd.read_parquet(
            PARQUET_DIR / "sla_rules.parquet"
        )

    def calculate_shipment_consequences(
        self,
        shipment,
    ) -> dict:

        shipment_id = shipment[
            "shipment_id"
        ]

        order_id = shipment[
            "order_id"
        ]

        departure_time = pd.to_datetime(
            shipment["departure_time"]
        )

        original_eta = pd.to_datetime(
            shipment["original_eta"]
        )

        current_eta = pd.to_datetime(
            shipment["current_eta"]
        )

        sla = self.sla_rules[
            self.sla_rules["order_id"]
            == order_id
        ]

        if sla.empty:

            raise ValueError(
                f"No SLA rule found for "
                f"order {order_id}."
            )

        sla = sla.iloc[0]

        # SLA is measured from departure,
        # not from the original ETA.
        sla_deadline = (
            original_eta
            + pd.Timedelta(
                hours=float(
                    sla["sla_tolerance_hours"]
                )
            )
        )

        delay_minutes = max(
            int(
                (
                    current_eta
                    - original_eta
                ).total_seconds()
                / 60
            ),
            0,
        )

        breach_minutes = max(
            int(
                (
                    current_eta
                    - sla_deadline
                ).total_seconds()
                / 60
            ),
            0,
        )

        breach_hours = (
            breach_minutes / 60
        )

        penalty_rate = float(
            sla[
                "sla_penalty_per_hour_eur"
            ]
        )

        projected_penalty = round(
            breach_hours
            * penalty_rate,
            2,
        )

        return {
            "shipment_id": shipment_id,
            "order_id": order_id,

            "priority": sla[
                "priority"
            ],

            "departure_time": departure_time,

            "original_eta": original_eta,

            "current_eta": current_eta,

            "sla_deadline": sla_deadline,

            "sla_tolerance_hours": float(
                sla["sla_tolerance_hours"]
            ),

            "delay_minutes": delay_minutes,

            "sla_breach_minutes": breach_minutes,

            "sla_breach_hours": breach_hours,

            "sla_penalty_per_hour_eur": (
                penalty_rate
            ),

            "projected_sla_penalty_eur": (
                projected_penalty
            ),

            "sla_breached": (
                breach_minutes > 0
            ),
        }