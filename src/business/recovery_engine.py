from pathlib import Path

import pandas as pd

from src.business.recovery_options import (
    RecoveryOption,
    DO_NOTHING,
    INVENTORY_REALLOCATION,
    EXPEDITED_TRANSPORT,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PARQUET_DIR = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "parquet"
)


class RecoveryEngine:

    def __init__(self):

        self.inventory = pd.read_parquet(
            PARQUET_DIR / "inventory.parquet"
        )

        self.routes = pd.read_parquet(
            PARQUET_DIR / "routes.parquet"
        )

        self.carriers = pd.read_parquet(
            PARQUET_DIR / "carriers.parquet"
        )

        self.orders = pd.read_parquet(
            PARQUET_DIR / "orders.parquet"
        )

    def evaluate_recovery_options(
        self,
        shipment,
        consequences,
    ) -> list[RecoveryOption]:

        options = []

        penalty = float(
            consequences[
                "projected_sla_penalty_eur"
            ]
        )

        # -------------------------------------------------
        # OPTION 1 — DO NOTHING
        # -------------------------------------------------

        options.append(
            RecoveryOption(
                option_type=DO_NOTHING,
                description=(
                    "Accept the current shipment "
                    "trajectory without intervention."
                ),
                feasible=True,
                recovery_cost_eur=0.0,
                avoided_sla_penalty_eur=0.0,
                net_benefit_eur=-penalty,
                reason=(
                    "No recovery action is taken. "
                    "Any projected SLA penalty remains."
                ),
            )
        )

        # -------------------------------------------------
        # OPTION 2 — INVENTORY REALLOCATION
        # -------------------------------------------------

        reallocation = (
            self._evaluate_inventory_reallocation(
                shipment,
                penalty,
            )
        )

        if reallocation is not None:
            options.append(reallocation)

        # -------------------------------------------------
        # OPTION 3 — EXPEDITED TRANSPORT
        # -------------------------------------------------

        expedited = (
            self._evaluate_expedited_transport(
                shipment,
                consequences,
            )
        )

        if expedited is not None:
            options.append(expedited)

        # -------------------------------------------------
        # RANK OPTIONS
        # -------------------------------------------------

        options.sort(
            key=lambda option: (
                option.feasible,
                option.net_benefit_eur,
            ),
            reverse=True,
        )

        return options

    # =====================================================
    # INVENTORY REALLOCATION
    # =====================================================

    def _evaluate_inventory_reallocation(
        self,
        shipment,
        current_penalty,
    ):

        destination = shipment[
            "destination_warehouse_id"
        ]

        shipment_origin = shipment[
            "origin_warehouse_id"
        ]

        product_id = (
            self._get_product_id_for_shipment(
                shipment
            )
        )

        if product_id is None:

            return RecoveryOption(
                option_type=INVENTORY_REALLOCATION,
                description=(
                    "Reallocate inventory from "
                    "another warehouse."
                ),
                feasible=False,
                recovery_cost_eur=0.0,
                avoided_sla_penalty_eur=0.0,
                net_benefit_eur=0.0,
                reason=(
                    "Unable to determine the "
                    "shipment product."
                ),
            )

        required_units = int(
            shipment["quantity_units"]
        )

        # -------------------------------------------------
        # Find OTHER warehouses stocking the product
        # -------------------------------------------------

        candidates = self.inventory[
            (
                self.inventory["product_id"]
                == product_id
            )
            &
            (
                self.inventory["warehouse_id"]
                != shipment_origin
            )
        ].copy()

        if candidates.empty:

            return RecoveryOption(
                option_type=INVENTORY_REALLOCATION,
                description=(
                    "Reallocate inventory from "
                    "another warehouse."
                ),
                feasible=False,
                recovery_cost_eur=0.0,
                avoided_sla_penalty_eur=0.0,
                net_benefit_eur=0.0,
                reason=(
                    "No other warehouse stocks "
                    f"product {product_id}."
                ),
            )

        # -------------------------------------------------
        # Calculate safely transferable inventory
        # -------------------------------------------------

        candidates["safe_transferable_units"] = (
            candidates["available_units"]
            - candidates["safety_stock_units"]
        ).clip(lower=0)

        candidates = candidates[
            candidates[
                "safe_transferable_units"
            ]
            > 0
        ].copy()

        if candidates.empty:

            return RecoveryOption(
                option_type=INVENTORY_REALLOCATION,
                description=(
                    "Reallocate inventory from "
                    "another warehouse."
                ),
                feasible=False,
                recovery_cost_eur=0.0,
                avoided_sla_penalty_eur=0.0,
                net_benefit_eur=0.0,
                reason=(
                    "No other warehouse has "
                    "inventory available above "
                    "its safety-stock threshold."
                ),
                destination_warehouse_id=destination,
                quantity_units=0,
                safety_stock_protected=True,
            )

        # -------------------------------------------------
        # Select the warehouse with the largest
        # safely transferable quantity.
        # -------------------------------------------------

        candidates = candidates.sort_values(
            "safe_transferable_units",
            ascending=False,
        )

        source = candidates.iloc[0]

        source_warehouse = source[
            "warehouse_id"
        ]

        safe_transferable = int(
            source[
                "safe_transferable_units"
            ]
        )

        transfer_quantity = min(
            required_units,
            safe_transferable,
        )

        # -------------------------------------------------
        # Cannot fulfil entire requirement
        # -------------------------------------------------

        if transfer_quantity < required_units:

            return RecoveryOption(
                option_type=INVENTORY_REALLOCATION,
                description=(
                    "Reallocate available inventory "
                    "from another warehouse."
                ),
                feasible=False,
                recovery_cost_eur=0.0,
                avoided_sla_penalty_eur=0.0,
                net_benefit_eur=0.0,
                reason=(
                    f"{source_warehouse} can safely "
                    f"transfer only "
                    f"{safe_transferable} units, "
                    f"but {required_units} units "
                    "are required."
                ),
                source_warehouse_id=source_warehouse,
                destination_warehouse_id=destination,
                quantity_units=transfer_quantity,
                safety_stock_protected=True,
            )

        # -------------------------------------------------
        # Calculate transfer economics
        # -------------------------------------------------

        transport_cost = (
            self._calculate_reallocation_cost(
                source_warehouse,
                destination,
                shipment,
            )
        )

        if transport_cost is None:

            return RecoveryOption(
                option_type=INVENTORY_REALLOCATION,
                description=(
                    "Reallocate inventory from "
                    "another warehouse."
                ),
                feasible=False,
                recovery_cost_eur=0.0,
                avoided_sla_penalty_eur=0.0,
                net_benefit_eur=0.0,
                reason=(
                    f"No defined transportation route "
                    f"exists from {source_warehouse} "
                    f"to {destination}."
                ),
                source_warehouse_id=source_warehouse,
                destination_warehouse_id=destination,
                quantity_units=transfer_quantity,
                safety_stock_protected=True,
            )

        net_benefit = (
            current_penalty
            - transport_cost
        )

        return RecoveryOption(
            option_type=INVENTORY_REALLOCATION,
            description=(
                "Reallocate inventory from another warehouse."
            ),
            feasible=True,
            recovery_cost_eur=transport_cost,
            avoided_sla_penalty_eur=current_penalty,
            net_benefit_eur=net_benefit,
            reason=(
                f"Transfer {transfer_quantity} units from "
                f"{source_warehouse} to {destination} "
                "while protecting safety stock."
            ),
            source_warehouse_id=source_warehouse,
            destination_warehouse_id=destination,
            quantity_units=transfer_quantity,
            safety_stock_protected=True,
        )

    # =====================================================
    # EXPEDITED TRANSPORT
    # =====================================================

    def _evaluate_expedited_transport(
    self,
    shipment,
    consequences,
    ):
        route_id = shipment[
            "route_id"
        ]

        route = self.routes[
            self.routes["route_id"]
            == route_id
        ]

        if route.empty:
            return RecoveryOption(
                option_type=EXPEDITED_TRANSPORT,
                description=(
                    "Use expedited transportation "
                    "on the current route."
                ),
                feasible=False,
                recovery_cost_eur=0.0,
                avoided_sla_penalty_eur=0.0,
                net_benefit_eur=0.0,
                reason=(
                    f"Route {route_id} "
                    "could not be found."
                ),
            )

        route = route.iloc[0]

        distance_km = float(
            route["distance_km"]
        )

        # Temporary deterministic rate.
        expedited_rate = 1.50

        recovery_cost = round(
            distance_km
            * expedited_rate,
            2,
        )

        estimated_recovery_hours = max(
            float(
                route[
                    "typical_transit_hours"
                ]
            )
            * 0.5,
            1.0,
        )

        current_eta = pd.to_datetime(
            shipment["current_eta"]
        )

        sla_deadline = pd.to_datetime(
            consequences["sla_deadline"]
        )

        current_breach_hours = max(
            (
                current_eta
                - sla_deadline
            ).total_seconds()
            / 3600,
            0.0,
        )

        recovery_eta = (
            current_eta
            - pd.Timedelta(
                hours=estimated_recovery_hours
            )
        )

        remaining_breach_hours = max(
            (
                recovery_eta
                - sla_deadline
            ).total_seconds()
            / 3600,
            0.0,
        )

        current_penalty = float(
            consequences["projected_sla_penalty_eur"]
        )

        penalty_rate_per_hour = (
            current_penalty
            / current_breach_hours
            if current_breach_hours > 0
            else 0.0
        )

        remaining_penalty = round(
            remaining_breach_hours
            * penalty_rate_per_hour,
            2,
        )

        actual_avoided_penalty = round(
            current_penalty
            - remaining_penalty,
            2,
        )

        net_benefit = round(
            actual_avoided_penalty
            - recovery_cost,
            2,
        )

        return RecoveryOption(
            option_type=EXPEDITED_TRANSPORT,
            description=(
                "Use expedited transportation "
                "to reduce delivery delay."
            ),
            feasible=True,
            recovery_cost_eur=recovery_cost,
            avoided_sla_penalty_eur=(
                actual_avoided_penalty
            ),
            net_benefit_eur=net_benefit,
            reason=(
                "An expedited transport option "
                "is available for the shipment route."
            ),
            estimated_recovery_hours=(
                estimated_recovery_hours
            ),
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _get_product_id_for_shipment(
        self,
        shipment,
    ):

        order_id = shipment[
            "order_id"
        ]

        order = self.orders[
            self.orders["order_id"]
            == order_id
        ]

        if order.empty:
            return None

        return order.iloc[0][
            "product_id"
        ]

    def _calculate_reallocation_cost(

        self,
        source_warehouse,
        destination_warehouse,
        shipment,
    ):
        """
        Calculate the transportation cost of moving
        inventory between two warehouses.

        A reallocation is only considered valid when
        an explicit route exists in routes.parquet.

        We deliberately do not invent a distance or
        transportation cost for missing lanes.
        """

        routes = self.routes

        route = routes[
            (
                routes["origin_warehouse"]
                == source_warehouse
            )
            &
            (
                routes["destination_warehouse"]
                == destination_warehouse
            )
        ]

        if route.empty:
            return None

        route = route.iloc[0]

        distance_km = float(
            route["distance_km"]
        )

        # Use the shipment's carrier when possible.
        carrier_id = shipment.get(
            "carrier_id"
        )

        carrier = self.carriers[
            self.carriers["carrier_id"]
            == carrier_id
        ]

        if carrier.empty:
            return None

        base_cost_per_km = float(
            carrier.iloc[0][
                "base_cost_per_km"
            ]
        )

        return round(
            distance_km
            * base_cost_per_km,
            2,
        )