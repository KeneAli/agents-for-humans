from src.agent.tools.recovery_tools import create_recovery_tools
from src.business.consequence_engine import ConsequenceEngine
from src.business.recovery_engine import RecoveryEngine
from src.simulation.event_simulator import simulate_disruption
from src.simulation.operational_state import OperationalState


def test_inventory_reallocation_evaluates_and_executes_successfully():
    state = OperationalState()
    simulate_disruption(
        state=state,
        shipment_id="SHP-0008",
        event_type="VEHICLE_BREAKDOWN",
        delay_minutes=480,
    )

    shipment = state.get_shipment("SHP-0008")
    assert shipment is not None
    assert shipment["shipment_status"] == "DELAYED"

    consequence_engine = ConsequenceEngine()
    consequences = consequence_engine.calculate_shipment_consequences(shipment)
    assert consequences["sla_breached"] is True

    recovery_engine = RecoveryEngine()
    options = recovery_engine.evaluate_recovery_options(shipment, consequences)
    reallocation = next(
        (opt for opt in options if opt.option_type == "INVENTORY_REALLOCATION"),
        None,
    )
    assert reallocation is not None
    assert reallocation.feasible is True
    assert reallocation.estimated_recovery_hours is not None
    assert reallocation.estimated_recovery_hours > 0

    tools = {
        t.__name__: t
        for t in create_recovery_tools(
            state,
            run_id="RUN-REGRESSION-0008",
            event_id="EVT-0008",
            runtime_session_id="SESS-0008",
        )
    }

    eval_result = tools["evaluate_recovery_options"](shipment_id="SHP-0008")
    assert eval_result["found"] is True

    exec_result = tools["execute_recovery_action"](
        shipment_id="SHP-0008",
        option_type="INVENTORY_REALLOCATION",
    )
    assert exec_result["found"] is True
    assert exec_result["executed"] is True
    assert exec_result["option_type"] == "INVENTORY_REALLOCATION"

    recovered_shipment = state.get_shipment("SHP-0008")
    assert recovered_shipment is not None
    assert recovered_shipment["shipment_status"] == "RECOVERY_IN_PROGRESS"

    workflow = state.repository.get_recovery_workflow("SHP-0008", "RUN-REGRESSION-0008")
    assert workflow is not None
    assert workflow["status"] == "COMPLETED"
