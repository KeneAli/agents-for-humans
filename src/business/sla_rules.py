from pathlib import Path

import pandas as pd


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


def generate_sla_rules(
    orders: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for _, order in orders.iterrows():

        priority = str(order.get(
            "priority",
            "STANDARD",
        ))

        if priority == "CRITICAL":

            tolerance_hours = 2
            penalty_per_hour = 250.0

        elif priority == "PREMIUM":

            tolerance_hours = 4
            penalty_per_hour = 200.0

        else:

            tolerance_hours = 12
            penalty_per_hour = 75.0

        records.append(
            {
                "order_id": order[
                    "order_id"
                ],
                "sla_tolerance_hours": (
                    tolerance_hours
                ),
                "sla_penalty_per_hour_eur": (
                    penalty_per_hour
                ),
                "priority": priority,
            }
        )

    return pd.DataFrame(records)


def save_sla_rules(
    df: pd.DataFrame,
):

    csv_path = (
        CSV_DIR / "sla_rules.csv"
    )

    parquet_path = (
        PARQUET_DIR
        / "sla_rules.parquet"
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
        f"✓ sla_rules: {len(df):,} records"
    )


if __name__ == "__main__":

    orders = pd.read_parquet(
        PARQUET_DIR
        / "orders.parquet"
    )

    sla_rules = generate_sla_rules(
        orders
    )

    save_sla_rules(
        sla_rules
    )