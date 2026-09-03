from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
rng = np.random.default_rng(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_DIR = PROJECT_ROOT / "data" / "generated" / "csv"
PARQUET_DIR = PROJECT_ROOT / "data" / "generated" / "parquet"


def generate_inventory(
    products: pd.DataFrame,
    warehouses: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for _, warehouse in warehouses.iterrows():

        for _, product in products.iterrows():

            # Some products are not stocked at every location.
            if rng.random() < 0.18:
                continue

            criticality = product["criticality"]

            if criticality == "CRITICAL":
                base_stock = rng.integers(150, 500)
                safety_factor = 0.35

            elif criticality == "HIGH":
                base_stock = rng.integers(100, 400)
                safety_factor = 0.25

            elif criticality == "MEDIUM":
                base_stock = rng.integers(50, 250)
                safety_factor = 0.20

            else:
                base_stock = rng.integers(20, 150)
                safety_factor = 0.15

            on_hand = int(base_stock)

            safety_stock = int(on_hand * safety_factor)

            allocated = int(
                rng.uniform(
                    0.05,
                    min(0.45, 0.75),
                ) * on_hand
            )

            available = max(on_hand - allocated, 0)

            inbound = int(
                rng.choice(
                    [0, 0, 0, 50, 100, 150, 250]
                )
            )

            records.append(
                {
                    "inventory_id": (
                        f"INV-{warehouse['warehouse_id']}-"
                        f"{product['product_id']}"
                    ),
                    "warehouse_id": warehouse["warehouse_id"],
                    "product_id": product["product_id"],
                    "on_hand_units": on_hand,
                    "allocated_units": allocated,
                    "available_units": available,
                    "safety_stock_units": safety_stock,
                    "inbound_units": inbound,
                }
            )

    inventory = pd.DataFrame(records)

    # ========================================================
    # HERO SCENARIO
    # ========================================================

    # Brussels DC
    # --------------------------------------------------------
    # This inventory position deliberately creates an
    # economically viable emergency transfer to Frankfurt.
    #
    # Before transfer:
    # Available = 270
    # Safety stock = 150
    #
    # Proposed transfer = 120
    #
    # After transfer:
    # Available = 150
    # Safety stock = 150
    #
    # Therefore the transfer does NOT breach the buffer.
    # --------------------------------------------------------

    bru_mask = (
        (inventory["warehouse_id"] == "BRU-01")
        & (inventory["product_id"] == "PRD-042")
    )

    inventory.loc[bru_mask, "on_hand_units"] = 350
    inventory.loc[bru_mask, "allocated_units"] = 80
    inventory.loc[bru_mask, "available_units"] = 270
    inventory.loc[bru_mask, "safety_stock_units"] = 150
    inventory.loc[bru_mask, "inbound_units"] = 200

    # Frankfurt DC
    # --------------------------------------------------------
    # Frankfurt has insufficient available stock and no
    # inbound inventory currently scheduled.
    # --------------------------------------------------------

    fra_mask = (
        (inventory["warehouse_id"] == "FRA-01")
        & (inventory["product_id"] == "PRD-042")
    )

    inventory.loc[fra_mask, "on_hand_units"] = 65
    inventory.loc[fra_mask, "allocated_units"] = 40
    inventory.loc[fra_mask, "available_units"] = 25
    inventory.loc[fra_mask, "safety_stock_units"] = 50
    inventory.loc[fra_mask, "inbound_units"] = 0

    return inventory


def save_inventory(df: pd.DataFrame):

    csv_path = CSV_DIR / "inventory.csv"
    parquet_path = PARQUET_DIR / "inventory.parquet"

    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)

    print(f"✓ inventory: {len(df):,} records")


if __name__ == "__main__":

    products = pd.read_parquet(
        PARQUET_DIR / "products.parquet"
    )

    warehouses = pd.read_parquet(
        PARQUET_DIR / "warehouses.parquet"
    )

    inventory = generate_inventory(
        products,
        warehouses,
    )

    save_inventory(inventory)