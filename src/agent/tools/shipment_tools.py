from strands import tool

from src.simulation.operational_state import (
    OperationalState,
)

from pathlib import Path
import pandas as pd


PROJECT_ROOT = (
    Path(__file__).resolve().parents[3]
)

PARQUET_DIR = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "parquet"
)


def create_shipment_tools(
    state: OperationalState,
):

    # Static reference data.
    # These do not change during the disruption.
    orders = pd.read_parquet(
        PARQUET_DIR / "orders.parquet"
    )

    routes = pd.read_parquet(
        PARQUET_DIR / "routes.parquet"
    )

    carriers = pd.read_parquet(
        PARQUET_DIR / "carriers.parquet"
    )

    @tool
    def get_shipment_context(
        shipment_id: str,
    ) -> dict:
        """
        Retrieve operational context for a shipment.

        Use this tool when investigating a disruption and
        you need factual information about the affected
        shipment, its order, route, carrier, and delivery
        commitment.

        Args:
            shipment_id: The shipment identifier, for example SHP-0048.

        Returns:
            A structured dictionary containing shipment,
            order, route, carrier, and delivery information.
        """

        # IMPORTANT:
        # Get the shipment from live OperationalState,
        # not directly from the baseline Parquet file.
        shipment = state.get_shipment(
            shipment_id
        )

        if shipment is None:
            return {
                "found": False,
                "shipment_id": shipment_id,
                "error": (
                    f"Shipment {shipment_id} "
                    f"was not found."
                ),
            }

        order_rows = orders[
            orders["order_id"]
            == shipment["order_id"]
        ]

        if order_rows.empty:
            return {
                "found": False,
                "shipment_id": shipment_id,
                "error": (
                    f"Order {shipment['order_id']} "
                    "was not found."
                ),
            }

        order = order_rows.iloc[0]

        route_rows = routes[
            routes["route_id"]
            == shipment["route_id"]
        ]

        carrier_rows = carriers[
            carriers["carrier_id"]
            == shipment["carrier_id"]
        ]

        route = (
            route_rows.iloc[0]
            if not route_rows.empty
            else None
        )

        carrier = (
            carrier_rows.iloc[0]
            if not carrier_rows.empty
            else None
        )

        result = {
            "found": True,

            "shipment": {
                "shipment_id": (
                    shipment["shipment_id"]
                ),
                "order_id": (
                    shipment["order_id"]
                ),
                "carrier_id": (
                    shipment["carrier_id"]
                ),
                "route_id": (
                    shipment["route_id"]
                ),
                "origin_warehouse_id": (
                    shipment[
                        "origin_warehouse_id"
                    ]
                ),
                "destination_warehouse_id": (
                    shipment[
                        "destination_warehouse_id"
                    ]
                ),
                "departure_time": str(
                    shipment["departure_time"]
                ),
                "original_eta": str(
                    shipment["original_eta"]
                ),
                "current_eta": str(
                    shipment["current_eta"]
                ),
                "shipment_status": (
                    shipment["shipment_status"]
                ),
                "quantity_units": int(
                    shipment["quantity_units"]
                ),
                "transport_cost_eur": float(
                    shipment[
                        "transport_cost_eur"
                    ]
                ),
            },

            "order": {
                "order_id": (
                    order["order_id"]
                ),
                "customer_id": (
                    order["customer_id"]
                ),
                "product_id": (
                    order["product_id"]
                ),
                "priority": (
                    order["priority"]
                ),
                "promised_delivery": str(
                    order["promised_delivery"]
                ),
                "quantity_units": int(
                    order["quantity_units"]
                ),
                "status": order["status"],
            },
        }

        if route is not None:
            result["route"] = {
                "route_id": (
                    route["route_id"]
                ),
                "origin_warehouse": (
                    route["origin_warehouse"]
                ),
                "destination_warehouse": (
                    route[
                        "destination_warehouse"
                    ]
                ),
                "distance_km": float(
                    route["distance_km"]
                ),
                "typical_transit_hours": float(
                    route[
                        "typical_transit_hours"
                    ]
                ),
                "risk_score": float(
                    route["risk_score"]
                ),
            }

        if carrier is not None:
            result["carrier"] = {
                "carrier_id": (
                    carrier["carrier_id"]
                ),
                "carrier_name": (
                    carrier["carrier_name"]
                ),
                "base_cost_per_km": float(
                    carrier[
                        "base_cost_per_km"
                    ]
                ),
            }

        return result

    return [
        get_shipment_context,
    ]