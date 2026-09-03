from dataclasses import dataclass
from typing import Optional


DO_NOTHING = "DO_NOTHING"

INVENTORY_REALLOCATION = (
    "INVENTORY_REALLOCATION"
)

EXPEDITED_TRANSPORT = (
    "EXPEDITED_TRANSPORT"
)


@dataclass
class RecoveryOption:
    """
    Represents one possible operational recovery action.

    The recovery engine will calculate the economics
    associated with each option.
    """

    option_type: str

    description: str

    feasible: bool

    recovery_cost_eur: float

    avoided_sla_penalty_eur: float

    net_benefit_eur: float

    reason: str

    source_warehouse_id: Optional[str] = None

    destination_warehouse_id: Optional[str] = None

    quantity_units: Optional[int] = None

    estimated_recovery_hours: Optional[float] = None

    safety_stock_protected: Optional[bool] = None