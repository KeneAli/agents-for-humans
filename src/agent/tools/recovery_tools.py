from strands import tool

from src.business.recovery_engine import RecoveryEngine
from src.simulation.operational_state import OperationalState
from src.business.consequence_engine import ConsequenceEngine


def create_recovery_tools(
    state: OperationalState,
    run_id: str | None = None,
    event_id: str | None = None,
    runtime_session_id: str | None = None,
):

    def require_run_id() -> str:
        if not run_id:
            raise ValueError("Recovery workflow requires a run_id.")
        return run_id

    @tool
    def evaluate_recovery_options(
        shipment_id: str,
    ) -> dict:
        """
        Evaluate deterministic recovery options for a disrupted shipment.

        Use this tool after investigating the shipment and its business
        consequences. It evaluates available recovery strategies using
        the current live operational state.

        Args:
            shipment_id: The shipment identifier, for example SHP-0048.

        Returns:
            A structured list of feasible and infeasible recovery options,
            including cost, avoided SLA penalty, net benefit, and rationale.
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
                    "was not found."
                ),
            }

        # CALCULATE BUSINESS CONSEQUENCES
 
        consequence_engine = ConsequenceEngine()

        consequences = (
            consequence_engine
            .calculate_shipment_consequences(
                shipment
            )
        )

        # EVALUATE RECOVERY OPTIONS
        recovery_engine = RecoveryEngine()

        options = (
            recovery_engine.evaluate_recovery_options(
                shipment=shipment,
                consequences=consequences,
            )
        )

        serialized_options = []

        for option in options:
            serialized_options.append(
                {
                    "option_type": option.option_type,
                    "description": option.description,
                    "feasible": bool(
                        option.feasible
                    ),
                    "recovery_cost_eur": float(
                        option.recovery_cost_eur
                    ),
                    "avoided_sla_penalty_eur": float(
                        option.avoided_sla_penalty_eur
                    ),
                    "net_benefit_eur": float(
                        option.net_benefit_eur
                    ),
                    "reason": option.reason,
                    "source_warehouse_id": (
                        option.source_warehouse_id
                    ),
                    "destination_warehouse_id": (
                        option.destination_warehouse_id
                    ),
                    "quantity_units": (
                        int(option.quantity_units)
                        if option.quantity_units is not None
                        else None
                    ),
                    "safety_stock_protected": (
                        bool(
                            option.safety_stock_protected
                        )
                        if option.safety_stock_protected is not None
                        else None
                    ),
                    "estimated_recovery_hours": (
                        float(
                            option.estimated_recovery_hours
                        )
                        if option.estimated_recovery_hours is not None
                        else None
                    ),
                }
            )

        workflow_run_id = require_run_id()

        # Store the decision for the approval workflow
        feasible_options = [
            option
            for option in serialized_options
            if option["feasible"]
        ]

        best_option = None
        if feasible_options:
            best_option = max(
                feasible_options,
                key=lambda option: option["net_benefit_eur"],
            )

        state.set_pending_recovery_approval(
            {
                "shipment_id": shipment_id,
                "run_id": workflow_run_id,
                "event_id": event_id,
                "runtime_session_id": runtime_session_id,
                "selected_option": (
                    best_option["option_type"]
                    if best_option is not None
                    else None
                ),
                "options": serialized_options,
                "current_delay_minutes": int(
                    consequences["delay_minutes"]
                ),
                "sla_breached": bool(
                    consequences["sla_breached"]
                ),
                "projected_sla_penalty_eur": float(
                    consequences[
                        "projected_sla_penalty_eur"
                    ]
                ),
            }
        )

        # ----------------------------------------------------
        # Update recovery workflow state
        # ----------------------------------------------------

        state.set_recovery_workflow(
            shipment_id=shipment_id,
            run_id=workflow_run_id,
            status="AWAITING_APPROVAL",
            action=(
                best_option["option_type"]
                if best_option is not None
                else None
            ),
            event_id=event_id,
            runtime_session_id=runtime_session_id,
        )

        # ----------------------------------------------------
        # Record audit trail
        # ----------------------------------------------------

        state.record_audit_event(
            event_type="OPTIONS_EVALUATED",
            shipment_id=shipment_id,
            run_id=workflow_run_id,
            details={
                "selected_option": (
                    best_option["option_type"]
                    if best_option is not None
                    else None
                ),
                "net_benefit_eur": (
                    best_option["net_benefit_eur"]
                    if best_option is not None
                    else None
                ),
                "projected_sla_penalty_eur": (
                    consequences[
                        "projected_sla_penalty_eur"
                    ]
                ),
            },
            event_id=event_id,
            runtime_session_id=runtime_session_id,
        )

        state.record_audit_event(
            event_type="RECOVERY_SELECTED",
            shipment_id=shipment_id,
            run_id=workflow_run_id,
            details={
                "option_type": (
                    best_option["option_type"]
                    if best_option is not None
                    else None
                ),
                "net_benefit_eur": (
                    best_option["net_benefit_eur"]
                    if best_option is not None
                    else None
                ),
            },
            event_id=event_id,
            runtime_session_id=runtime_session_id,
        )

        return {
            "found": True,
            "shipment_id": shipment_id,
            "current_delay_minutes": int(
                consequences["delay_minutes"]
            ),
            "sla_breached": bool(
                consequences["sla_breached"]
            ),
            "projected_sla_penalty_eur": float(
                consequences[
                    "projected_sla_penalty_eur"
                ]
            ),
            "options": serialized_options,
        }

    @tool
    def request_recovery_approval(
        shipment_id: str,
    ) -> dict:
        """
        Present the agent's existing recovery decision for
        human approval.

        This tool does not recalculate business consequences
        or recovery options. It reads the pending recovery
        approval packet created by evaluate_recovery_options().

        Args:
            shipment_id:
                The shipment awaiting recovery approval.

        Returns:
            A structured approval request containing the
            selected recovery action and the business impact
            already calculated by the recovery workflow.
        """

        workflow_run_id = require_run_id()
        approval = state.get_pending_recovery_approval(shipment_id, workflow_run_id)

        if approval is None:
            return {
                "found": False,
                "approval_required": False,
                "shipment_id": shipment_id,
                "error": (
                    "No pending recovery approval exists."
                ),
            }

        if approval["shipment_id"] != shipment_id:
            return {
                "found": False,
                "approval_required": False,
                "shipment_id": shipment_id,
                "error": (
                    "The pending recovery approval belongs "
                    f"to shipment {approval['shipment_id']}."
                ),
            }

        selected_option = None

        for option in approval["options"]:
            if (
                option["option_type"]
                == approval["selected_option"]
            ):
                selected_option = option
                break

        if selected_option is None:
            return {
                "found": False,
                "approval_required": False,
                "shipment_id": shipment_id,
                "error": (
                    "The selected recovery option could not "
                    "be found in the pending approval packet."
                ),
            }

        return {
            "found": True,
            "approval_required": True,
            "shipment_id": shipment_id,
            "selected_option": selected_option,
            "business_impact": {
                "current_delay_minutes": (
                    approval["current_delay_minutes"]
                ),
                "sla_breached": (
                    approval["sla_breached"]
                ),
                "projected_sla_penalty_eur": (
                    approval["projected_sla_penalty_eur"]
                ),
            },
        }
    
    @tool
    def execute_recovery_action(
        shipment_id: str,
        option_type: str,
    ) -> dict:
        """
        Execute a validated recovery action for a shipment.

        Use this tool only after recovery options have been
        evaluated and a feasible recovery action has been selected.

        The tool validates the requested option against the
        deterministic Recovery Engine before mutating the live
        operational state.

        Args:
            shipment_id:
                The shipment identifier.

            option_type:
                The recovery option to execute. Supported values
                are EXPEDITED_TRANSPORT and INVENTORY_REALLOCATION.

        Returns:
            A structured result describing the executed recovery
            action and the updated shipment state.
        """

        shipment = state.get_shipment(
            shipment_id
        )

        if shipment is None:
            return {
                "found": False,
                "executed": False,
                "shipment_id": shipment_id,
                "error": (
                    f"Shipment {shipment_id} "
                    "was not found."
                ),
            }

        workflow_run_id = require_run_id()

        # ----------------------------------------------------
        # Recalculate the current consequences
        # ----------------------------------------------------

        consequence_engine = ConsequenceEngine()

        consequences = (
            consequence_engine
            .calculate_shipment_consequences(
                shipment
            )
        )

        # ----------------------------------------------------
        # Recalculate recovery options
        # ----------------------------------------------------

        recovery_engine = RecoveryEngine()

        options = (
            recovery_engine
            .evaluate_recovery_options(
                shipment=shipment,
                consequences=consequences,
            )
        )

        # ----------------------------------------------------
        # Find the requested option
        # ----------------------------------------------------

        selected_option = next(
            (
                option
                for option in options
                if option.option_type
                == option_type
            ),
            None,
        )

        if selected_option is None:
            return {
                "found": True,
                "executed": False,
                "shipment_id": shipment_id,
                "error": (
                    f"Recovery option "
                    f"{option_type} "
                    "is not available."
                ),
            }

        # ----------------------------------------------------
        # Validate feasibility
        # ----------------------------------------------------

        if not selected_option.feasible:
            return {
                "found": True,
                "executed": False,
                "shipment_id": shipment_id,
                "option_type": option_type,
                "error": (
                    "The selected recovery option "
                    "is not feasible."
                ),
                "reason": selected_option.reason,
            }

        # ----------------------------------------------------
        # DO_NOTHING is not an execution action
        # ----------------------------------------------------

        if option_type == "DO_NOTHING":
            return {
                "found": True,
                "executed": False,
                "shipment_id": shipment_id,
                "option_type": option_type,
                "error": (
                    "DO_NOTHING does not require "
                    "an execution action."
                ),
            }

        # ----------------------------------------------------
        # Validate recovery time
        # ----------------------------------------------------

        if (
            selected_option
            .estimated_recovery_hours
            is None
        ):
            return {
                "found": True,
                "executed": False,
                "shipment_id": shipment_id,
                "option_type": option_type,
                "error": (
                    "The selected recovery option "
                    "does not contain a recovery-time "
                    "estimate."
                ),
            }

        # ----------------------------------------------------
        # Record human approval and begin execution
        # ----------------------------------------------------
        state.set_recovery_workflow(
            shipment_id=shipment_id,
            run_id=workflow_run_id,
            status="APPROVED",
            action=option_type,
            event_id=event_id,
            runtime_session_id=runtime_session_id,
        )

        state.record_audit_event(
            event_type="APPROVAL_GRANTED",
            shipment_id=shipment_id,
            run_id=workflow_run_id,
            details={
                "option_type": option_type,
            },
            event_id=event_id,
            runtime_session_id=runtime_session_id,
        )

        state.set_recovery_workflow(
            shipment_id=shipment_id,
            run_id=workflow_run_id,
            status="EXECUTING",
            action=option_type,
            event_id=event_id,
            runtime_session_id=runtime_session_id,
        )

        # ----------------------------------------------------
        # Apply recovery to live operational state
        # ----------------------------------------------------

        updated_shipment = (
            state.apply_recovery_action(
                shipment_id=shipment_id,
                option_type=option_type,
                recovery_hours=(
                    selected_option
                    .estimated_recovery_hours
                ),
                recovery_cost_eur=(
                    selected_option
                    .recovery_cost_eur
                ),
            )
        )

        # ----------------------------------------------------
        # Record successful recovery execution
        # ----------------------------------------------------
        state.record_audit_event(
            event_type="RECOVERY_EXECUTED",
            shipment_id=shipment_id,
            run_id=workflow_run_id,
            details={
                "option_type": option_type,
                "recovery_cost_eur": float(
                    selected_option.recovery_cost_eur
                ),
                "estimated_recovery_hours": float(
                    selected_option.estimated_recovery_hours
                ),
            },
            event_id=event_id,
            runtime_session_id=runtime_session_id,
        )

        # ----------------------------------------------------
        # Verify the operational state mutation
        # ----------------------------------------------------
        verified_shipment = state.get_shipment(
            shipment_id
        )

        state_verified = (
            verified_shipment is not None
            and verified_shipment["shipment_status"]
            == "RECOVERY_IN_PROGRESS"
            and str(
                verified_shipment["current_eta"]
            )
            == str(
                updated_shipment["current_eta"]
            )
        )

        if state_verified:
            state.record_audit_event(
                event_type="STATE_VERIFIED",
                shipment_id=shipment_id,
                run_id=workflow_run_id,
                details={
                    "shipment_status": (
                        verified_shipment[
                            "shipment_status"
                        ]
                    ),
                    "current_eta": str(
                        verified_shipment[
                            "current_eta"
                        ]
                    ),
                },
                event_id=event_id,
                runtime_session_id=runtime_session_id,
            )

            state.set_recovery_workflow(
                shipment_id=shipment_id,
                run_id=workflow_run_id,
                status="COMPLETED",
                action=option_type,
                event_id=event_id,
                runtime_session_id=runtime_session_id,
            )
        else:
            state.set_recovery_workflow(
                shipment_id=shipment_id,
                run_id=workflow_run_id,
                status="FAILED",
                action=option_type,
                event_id=event_id,
                runtime_session_id=runtime_session_id,
            )

        return {
            "found": True,
            "executed": True,
            "shipment_id": shipment_id,
            "option_type": option_type,
            "recovery_cost_eur": float(
                selected_option
                .recovery_cost_eur
            ),
            "estimated_recovery_hours": float(
                selected_option
                .estimated_recovery_hours
            ),
            "net_benefit_eur": float(
                selected_option
                .net_benefit_eur
            ),
            "reason": selected_option.reason,
            "updated_shipment": {
                "shipment_status": (
                    updated_shipment[
                        "shipment_status"
                    ]
                ),
                "current_eta": str(
                    updated_shipment[
                        "current_eta"
                    ]
                ),
            },
        }



    return [
        evaluate_recovery_options,
        request_recovery_approval,
        execute_recovery_action,
    ]