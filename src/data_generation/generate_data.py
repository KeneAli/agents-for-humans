from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

rng = np.random.default_rng(SEED)
fake = Faker("en_GB")
Faker.seed(SEED)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_DIR = PROJECT_ROOT / "data" / "generated" / "csv"
PARQUET_DIR = PROJECT_ROOT / "data" / "generated" / "parquet"

CSV_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# WAREHOUSES
# ============================================================

def generate_warehouses() -> pd.DataFrame:

    warehouses = [
        {
            "warehouse_id": "PAR-01",
            "warehouse_name": "Nexora Paris Distribution Centre",
            "city": "Paris",
            "country": "France",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "capacity_units": 25000,
        },
        {
            "warehouse_id": "BRU-01",
            "warehouse_name": "Nexora Brussels Distribution Centre",
            "city": "Brussels",
            "country": "Belgium",
            "latitude": 50.8503,
            "longitude": 4.3517,
            "capacity_units": 22000,
        },
        {
            "warehouse_id": "FRA-01",
            "warehouse_name": "Nexora Frankfurt Distribution Centre",
            "city": "Frankfurt",
            "country": "Germany",
            "latitude": 50.1109,
            "longitude": 8.6821,
            "capacity_units": 30000,
        },
        {
            "warehouse_id": "MIL-01",
            "warehouse_name": "Nexora Milan Distribution Centre",
            "city": "Milan",
            "country": "Italy",
            "latitude": 45.4642,
            "longitude": 9.1900,
            "capacity_units": 24000,
        },
        {
            "warehouse_id": "MAD-01",
            "warehouse_name": "Nexora Madrid Distribution Centre",
            "city": "Madrid",
            "country": "Spain",
            "latitude": 40.4168,
            "longitude": -3.7038,
            "capacity_units": 26000,
        },
    ]

    return pd.DataFrame(warehouses)


# ============================================================
# CARRIERS
# ============================================================

def generate_carriers() -> pd.DataFrame:

    carriers = [
        {
            "carrier_id": "CAR-001",
            "carrier_name": "EuroTrans Logistics",
            "service_type": "Standard Road",
            "reliability_score": 0.91,
            "base_cost_per_km": 1.05,
            "expedite_multiplier": 1.60,
            "capacity_units": 5000,
        },
        {
            "carrier_id": "CAR-002",
            "carrier_name": "NorthStar Freight",
            "service_type": "Express Road",
            "reliability_score": 0.96,
            "base_cost_per_km": 1.35,
            "expedite_multiplier": 1.45,
            "capacity_units": 3500,
        },
        {
            "carrier_id": "CAR-003",
            "carrier_name": "Continental Cargo",
            "service_type": "Standard Road",
            "reliability_score": 0.89,
            "base_cost_per_km": 0.95,
            "expedite_multiplier": 1.75,
            "capacity_units": 7000,
        },
        {
            "carrier_id": "CAR-004",
            "carrier_name": "SwiftLink Transport",
            "service_type": "Express Road",
            "reliability_score": 0.94,
            "base_cost_per_km": 1.40,
            "expedite_multiplier": 1.40,
            "capacity_units": 3000,
        },
        {
            "carrier_id": "CAR-005",
            "carrier_name": "GreenRoute Freight",
            "service_type": "Low-Carbon Road",
            "reliability_score": 0.93,
            "base_cost_per_km": 1.15,
            "expedite_multiplier": 1.55,
            "capacity_units": 4500,
        },
        {
            "carrier_id": "CAR-006",
            "carrier_name": "PanEuro Logistics",
            "service_type": "Standard Road",
            "reliability_score": 0.88,
            "base_cost_per_km": 0.90,
            "expedite_multiplier": 1.80,
            "capacity_units": 8000,
        },
    ]

    return pd.DataFrame(carriers)


# ============================================================
# PRODUCTS
# ============================================================

def generate_products(n_products: int = 75) -> pd.DataFrame:

    categories = [
        "Industrial Equipment",
        "Electronics",
        "Automotive Components",
        "Medical Equipment",
        "Consumer Goods",
        "Packaging",
    ]

    criticalities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    products = []

    for i in range(1, n_products + 1):

        category = rng.choice(categories)

        criticality = rng.choice(
            criticalities,
            p=[0.30, 0.40, 0.23, 0.07],
        )

        products.append(
            {
                "product_id": f"PRD-{i:03d}",
                "product_name": f"{fake.word().title()} {category.split()[0]}",
                "category": category,
                "unit_weight_kg": round(
                    rng.uniform(0.5, 25.0),
                    2,
                ),
                "unit_value_eur": round(
                    rng.uniform(20, 1500),
                    2,
                ),
                "criticality": criticality,
            }
        )

    # Force our hero product to be deterministic.
    products[41] = {
        "product_id": "PRD-042",
        "product_name": "Industrial Control Module",
        "category": "Industrial Equipment",
        "unit_weight_kg": 2.4,
        "unit_value_eur": 850.0,
        "criticality": "CRITICAL",
    }

    return pd.DataFrame(products)


# ============================================================
# CUSTOMERS
# ============================================================

def generate_customers(n_customers: int = 30) -> pd.DataFrame:

    industries = [
        "Automotive",
        "Industrial Manufacturing",
        "Electronics",
        "Healthcare",
        "Retail",
        "FMCG",
    ]

    countries = [
        "France",
        "Germany",
        "Belgium",
        "Italy",
        "Spain",
        "Netherlands",
    ]

    sla_tiers = ["STANDARD", "PREMIUM", "CRITICAL"]

    customers = []

    for i in range(1, n_customers + 1):

        sla_tier = rng.choice(
            sla_tiers,
            p=[0.55, 0.35, 0.10],
        )

        penalty_rates = {
            "STANDARD": 50,
            "PREMIUM": 100,
            "CRITICAL": 150,
        }

        customers.append(
            {
                "customer_id": f"CUS-{i:03d}",
                "customer_name": fake.company(),
                "industry": rng.choice(industries),
                "country": rng.choice(countries),
                "customer_segment": (
                    "Enterprise"
                    if sla_tier != "STANDARD"
                    else "Mid-Market"
                ),
                "sla_tier": sla_tier,
                "sla_penalty_rate_eur_per_hour": penalty_rates[sla_tier],
                "credit_policy": (
                    "Guaranteed Delivery Credit"
                    if sla_tier == "CRITICAL"
                    else "Standard SLA Credit"
                ),
            }
        )

    # Make our hero customer deterministic.
    customers[0] = {
        "customer_id": "CUS-001",
        "customer_name": "NordTech Manufacturing",
        "industry": "Industrial Manufacturing",
        "country": "Germany",
        "customer_segment": "Enterprise",
        "sla_tier": "CRITICAL",
        "sla_penalty_rate_eur_per_hour": 150,
        "credit_policy": "Guaranteed Delivery Credit",
    }

    return pd.DataFrame(customers)


# ============================================================
# ROUTES
# ============================================================

def generate_routes(warehouses: pd.DataFrame) -> pd.DataFrame:

    coordinates = {
        row["warehouse_id"]: (
            row["latitude"],
            row["longitude"],
        )
        for _, row in warehouses.iterrows()
    }

    route_pairs = [
        ("PAR-01", "BRU-01"),
        ("PAR-01", "FRA-01"),
        ("PAR-01", "MAD-01"),
        ("BRU-01", "PAR-01"),
        ("BRU-01", "FRA-01"),
        ("FRA-01", "BRU-01"),
        ("FRA-01", "PAR-01"),
        ("FRA-01", "MIL-01"),
        ("MIL-01", "FRA-01"),
        ("MIL-01", "MAD-01"),
        ("MAD-01", "MIL-01"),
        ("MAD-01", "PAR-01"),
    ]

    routes = []

    for i, (origin, destination) in enumerate(route_pairs, start=1):

        lat1, lon1 = coordinates[origin]
        lat2, lon2 = coordinates[destination]

        # Approximation for initial synthetic network.
        distance_km = np.sqrt(
            ((lat2 - lat1) * 111) ** 2
            + ((lon2 - lon1) * 75) ** 2
        )

        routes.append(
            {
                "route_id": f"R-{i:03d}",
                "origin_warehouse": origin,
                "destination_warehouse": destination,
                "distance_km": round(distance_km, 1),
                "typical_transit_hours": round(
                    distance_km / 70,
                    1,
                ),
                "risk_score": round(
                    rng.uniform(0.10, 0.45),
                    2,
                ),
            }
        )

    return pd.DataFrame(routes)


# ============================================================
# SAVE
# ============================================================

def save_dataset(df: pd.DataFrame, name: str) -> None:

    csv_path = CSV_DIR / f"{name}.csv"
    parquet_path = PARQUET_DIR / f"{name}.parquet"

    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)

    print(f"✓ {name}: {len(df):,} records")


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nGenerating Nexora reference data...\n")

    warehouses = generate_warehouses()
    carriers = generate_carriers()
    products = generate_products()
    customers = generate_customers()
    routes = generate_routes(warehouses)

    save_dataset(warehouses, "warehouses")
    save_dataset(carriers, "carriers")
    save_dataset(products, "products")
    save_dataset(customers, "customers")
    save_dataset(routes, "routes")

    print("\nReference data generation complete.")
    print(f"Output directory: {CSV_DIR}")


if __name__ == "__main__":
    main()