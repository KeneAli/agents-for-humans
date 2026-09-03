from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42

rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_DIR = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "csv"
)

PARQUET_DIR = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "parquet"
)


def generate_shipments(
    orders: pd.DataFrame,
    routes: pd.DataFrame,
    carriers: pd.DataFrame,
) -> pd.DataFrame:

    shipments = []

    route_lookup = routes.set_index(
        [
            "origin_warehouse",
            "destination_warehouse",
        ]
    )

    for _, order in orders.iterrows():

        origin = order[
            "origin_warehouse_id"
        ]

        destination = order[
            "destination_warehouse_id"
        ]

        route_key = (
            origin,
            destination,
        )

        if route_key in route_lookup.index:

            route = route_lookup.loc[
                route_key
            ]

        else:

            # Fallback for any randomly generated route
            route = routes.sample(
                1,
                random_state=(
                    SEED
                    + int(
                        order[
                            "order_id"
                        ].split("-")[1]
                    )
                ),
            ).iloc[0]

        carrier = carriers.sample(
            1,
            random_state=(
                SEED
                + int(
                    order[
                        "order_id"
                    ].split("-")[1]
                )
                + 5000
            ),
        ).iloc[0]

        transit_hours = float(
            route[
                "typical_transit_hours"
            ]
        )

        departure_time = order[
            "order_date"
        ]

        expected_arrival = (
            departure_time
            + pd.Timedelta(
                hours=transit_hours
            )
        )

        shipments.append(
            {
                "shipment_id": (
                    f"SHP-{order['order_id'].split('-')[1]}"
                ),
                "order_id": order[
                    "order_id"
                ],
                "carrier_id": carrier[
                    "carrier_id"
                ],
                "route_id": route[
                    "route_id"
                ],
                "origin_warehouse_id": origin,
                "destination_warehouse_id": destination,
                "departure_time": departure_time,
                "original_eta": expected_arrival,
                "current_eta": expected_arrival,
                "shipment_status": "IN_TRANSIT",
                "quantity_units": order[
                    "quantity_units"
                ],
                "transport_cost_eur": round(
                    route["distance_km"]
                    * carrier[
                        "base_cost_per_km"
                    ],
                    2,
                ),
            }
        )

    return pd.DataFrame(shipments)


def save_shipments(
    df: pd.DataFrame,
):

    csv_path = (
        CSV_DIR / "shipments.csv"
    )

    parquet_path = (
        PARQUET_DIR
        / "shipments.parquet"
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
        f"✓ shipments: {len(df):,} records"
    )


if __name__ == "__main__":

    orders = pd.read_parquet(
        PARQUET_DIR
        / "orders.parquet"
    )

    routes = pd.read_parquet(
        PARQUET_DIR
        / "routes.parquet"
    )

    carriers = pd.read_parquet(
        PARQUET_DIR
        / "carriers.parquet"
    )

    shipments = generate_shipments(
        orders,
        routes,
        carriers,
    )

    save_shipments(
        shipments
    )