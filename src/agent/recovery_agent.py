from strands import Agent
from strands.models import BedrockModel
from strands.vended_interventions.hitl import HumanInTheLoop

from src.agent.tools.shipment_tools import (
    create_shipment_tools,
)

from src.agent.tools.consequence_tools import (
    create_consequence_tools,
)

from src.agent.tools.recovery_tools import (
    create_recovery_tools,
)

from src.simulation.operational_state import (
    OperationalState,
)

from src.simulation.event_simulator import (
    simulate_disruption,
)

MODEL_ID = "global.anthropic.claude-sonnet-4-6"
REGION = "us-east-1"


SYSTEM_PROMPT = """
You are an autonomous logistics recovery agent.

Your job is to investigate operational disruptions,
evaluate recovery strategies, select the best action,
and execute the selected recovery action under human oversight.

You do NOT directly invent operational facts.

You must:

1. Understand the disruption.
2. Investigate the affected shipment.
3. Assess business consequences.
4. Evaluate available recovery options.
5. Compare feasible options based on business impact.
6. Select the recovery action that best protects the business.
7. After selecting the recovery action, call
   execute_recovery_action with the selected option.
8. Immediately before calling execute_recovery_action,
   you may state only that the selected action is being
   submitted for human authorization.
9. Do not state that execution is proceeding,
   underway, authorized, approved, or confirmed before
   execute_recovery_action returns a result.
10. Treat the execution tool result as the source of truth
    for whether the action was authorized and executed.
11. If execute_recovery_action returns executed=True,
    state that the recovery action was authorized and
    executed successfully, then verify the resulting
    operational state.
12. If execute_recovery_action does not return executed=True,
    state that the recovery action was not executed and
    do not report it as completed.

Important:

- The Recovery Engine evaluates operational feasibility and
  calculates recovery options.
- You are responsible for choosing between those options.
- Do not assume that the cheapest option is automatically best.
- Consider SLA impact, recovery cost, inventory protection,
  urgency, and operational risk.
Execution and human authorization:

- Do not create a separate prose approval step.
- Do not ask the user for approval in your response.
- Select the recovery action and call execute_recovery_action.
- The HumanInTheLoop intervention controls whether the
  execution tool is allowed to run.
- Before execute_recovery_action returns, do not describe
  the action as executing, proceeding, underway, approved,
  authorized, or confirmed.
- Before the tool call, the only appropriate description is:
  "The selected recovery action is being submitted for
  human authorization."
- Do not describe the HumanInTheLoop implementation itself
  to the user.
- Do not say that approval is "handled automatically."
- Do not infer approval from the fact that the tool was called.
- Approval and execution are confirmed only by the result
  returned from execute_recovery_action.
- After execution, retrieve the shipment context again and verify
  the resulting operational state.
- Clearly distinguish:
  - system-confirmed facts,
  - deterministic calculations,
  - agent decision,
  - human authorization,
  - executed action,
  - resulting operational state.
"""


def create_recovery_agent(
    state: OperationalState,
) -> Agent:

    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION,
        temperature=0.2,
    )

    shipment_tools = create_shipment_tools(
        state
    )

    consequence_tools = create_consequence_tools(
        state
    )

    recovery_tools = create_recovery_tools(
        state
    )

    human_approval = HumanInTheLoop(
        ask="stdio", 
        allowed_tools=[ 
            "get_shipment_context", 
            "get_business_consequences", 
            "evaluate_recovery_options",
            "request_recovery_approval", 
        ], 
        evaluate=lambda response: ( 
            isinstance(response, str) 
            and response.strip().lower() 
            in {"y", "yes", "approved"} 
        ), 
    )

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            *shipment_tools,
            *consequence_tools,
            *recovery_tools,
        ],
        interventions=[
            human_approval,
        ],
    )


if __name__ == "__main__":

    state = OperationalState()

    simulate_disruption(
        state=state,
        shipment_id="SHP-0048",
        event_type="VEHICLE_BREAKDOWN",
        delay_minutes=480,
    )

    agent = create_recovery_agent(
        state
    )

    response = agent(
        """
        Investigate shipment SHP-0048 after a vehicle
        breakdown causing an estimated 480-minute delay.

        Complete the following workflow:

        1. Retrieve the shipment's operational context.
        2. Determine the current business consequences.
        3. Evaluate all available recovery options.
        4. Compare the feasible options.
        5. Select the best feasible recovery option.
        6. Call execute_recovery_action for the selected action.
        7. Wait for the execution tool result.
        8. Treat the execution tool result as the authoritative
        indication of whether the action was authorized and executed.
        9. If executed=True, verify the resulting shipment state.
        10. Report the final result.

        IMPORTANT:

        - This is an execution task with human oversight.
        - Do not stop after evaluating or recommending an option.
        - Once you have selected a feasible recovery option,
        call execute_recovery_action.
        - Do not ask the user for approval in your response.
        - Do not execute an option that the Recovery Engine marked
        as infeasible.
        - If EXPEDITED_TRANSPORT is selected, call
        execute_recovery_action with:

            shipment_id="SHP-0048"
            option_type="EXPEDITED_TRANSPORT"

        - Do not claim that an action was executed unless the
        execution tool actually returns executed=True.
        - After execution, verify the resulting shipment state.

        Clearly distinguish:

        - system-confirmed facts
        - deterministic calculations
        - agent decision
        - human authorization
        - executed action
        - resulting operational state
        """
    )

    print("\n=== RECOVERY WORKFLOW STATE ===")
    print(state.get_recovery_workflow("SHP-0048"))

    print("\n=== AUDIT EVENTS ===")
    for event in state.get_audit_events("SHP-0048"):
        print(event)
