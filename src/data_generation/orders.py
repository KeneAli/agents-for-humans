from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


SEED = 42
rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_DIR = PROJECT_ROOT / "data" / "generated" / "csv"
PARQUET_DIR = PROJECT_ROOT / "data" / "generated" / "parquet"


def generate_orders(
    customers: pd.DataFrame,
    products: pd.DataFrame,
    warehouses: pd.DataFrame,
    n_orders: int = 750,
) -> pd.DataFrame:

    orders = []

    warehouse_ids = warehouses["warehouse_id"].tolist()

    start_date = datetime(2026, 8, 1)

    for i in range(1, n_orders + 1):

        customer = customers.sample(
            1,
            random_state=SEED + i
        ).iloc[0]

        product = products.sample(
            1,
            random_state=SEED + i + 1000
        ).iloc[0]

        origin = rng.choice(warehouse_ids)
        destination = rng.choice(
            [w for w in warehouse_ids if w != origin]
        )

        order_date = (
            start_date
            + timedelta(
                hours=int(
                    rng.integers(0, 24 * 30)
                )
            )
        )

        quantity = int(
            rng.choice(
                [10, 25, 50, 75, 100, 150, 200]
            )
        )

        sla_hours = {
            "STANDARD": 72,
            "PREMIUM": 48,
            "CRITICAL": 24,
        }[customer["sla_tier"]]

        promised_delivery = (
            order_date
            + timedelta(hours=sla_hours)
        )

        orders.append(
            {
                "order_id": f"ORD-{i:04d}",
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "origin_warehouse_id": origin,
                "destination_warehouse_id": destination,
                "order_date": order_date,
                "quantity_units": quantity,
                "priority": customer["sla_tier"],
                "promised_delivery": promised_delivery,
                "status": "IN_TRANSIT",
            }
        )

    return pd.DataFrame(orders)


def inject_hero_order(
    orders: pd.DataFrame,
) -> pd.DataFrame:

    hero_order = {
        "order_id": "ORD-1003",
        "customer_id": "CUS-001",
        "product_id": "PRD-042",
        "origin_warehouse_id": "BRU-01",
        "destination_warehouse_id": "FRA-01",
        "order_date": datetime(2026, 8, 20, 8, 0),
        "quantity_units": 120,
        "priority": "CRITICAL",
        "promised_delivery": datetime(
            2026, 8, 21, 8, 0
        ),
        "status": "IN_TRANSIT",
    }

    orders = orders[
        orders["order_id"] != "ORD-1003"
    ]

    orders = pd.concat(
        [
            orders,
            pd.DataFrame([hero_order]),
        ],
        ignore_index=True,
    )

    return orders


def save_orders(df: pd.DataFrame):

    csv_path = CSV_DIR / "orders.csv"
    parquet_path = PARQUET_DIR / "orders.parquet"

    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)

    print(f"✓ orders: {len(df):,} records")


if __name__ == "__main__":

    customers = pd.read_parquet(
        PARQUET_DIR / "customers.parquet"
    )

    products = pd.read_parquet(
        PARQUET_DIR / "products.parquet"
    )

    warehouses = pd.read_parquet(
        PARQUET_DIR / "warehouses.parquet"
    )

    orders = generate_orders(
        customers,
        products,
        warehouses,
    )

    orders = inject_hero_order(orders)

    save_orders(orders)