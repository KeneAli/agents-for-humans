from strands import tool

from src.simulation.operational_state import OperationalState
from src.business.consequence_engine import ConsequenceEngine


def create_consequence_tools(
    state: OperationalState,
):

    @tool
    def get_business_consequences(
        shipment_id: str,
    ) -> dict:
        """
        Calculate the current business consequences of a
        shipment disruption using the live operational state.

        Use this tool when investigating a disrupted shipment
        and you need to understand SLA exposure, breach status,
        breach duration, and projected financial penalty.

        Args:
            shipment_id: The shipment identifier, for example SHP-0048.

        Returns:
            A structured summary of the shipment's current
            business consequences.
        """

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

        engine = ConsequenceEngine()

        consequences = (
            engine.calculate_shipment_consequences(
                shipment
            )
        )

        return {
            "found": True,
            "shipment_id": shipment_id,
            "order_id": consequences["order_id"],
            "priority": consequences["priority"],
            "sla_deadline": str(
                consequences["sla_deadline"]
            ),
            "sla_tolerance_hours": float(
                consequences["sla_tolerance_hours"]
            ),
            "delay_minutes": int(
                consequences["delay_minutes"]
            ),
            "sla_breach_minutes": int(
                consequences["sla_breach_minutes"]
            ),
            "sla_breach_hours": float(
                consequences["sla_breach_hours"]
            ),
            "penalty_rate_eur_per_hour": float(
                consequences[
                    "sla_penalty_per_hour_eur"
                ]
            ),
            "projected_sla_penalty_eur": float(
                consequences[
                    "projected_sla_penalty_eur"
                ]
            ),
            "sla_breached": bool(
                consequences["sla_breached"]
            ),
        }

    return [
        get_business_consequences,
    ]