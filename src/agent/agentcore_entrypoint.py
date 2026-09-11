from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.session.repository_session_manager import RepositorySessionManager

from src.agent.recovery_agent import create_recovery_agent
from src.simulation.event_simulator import apply_disruption_event
from src.simulation.operational_state import OperationalState
from src.state.dynamodb_session_repository import DynamoDBSessionRepository


app = BedrockAgentCoreApp()

state = OperationalState()
agent = create_recovery_agent(state)


@app.entrypoint
def agent_invocation(payload, context):

    user_message = payload.get("prompt")
    interrupt_responses = payload.get("interrupt_responses")
    disruption_event = payload.get("disruption_event")
    run_id = payload.get("run_id")
    event_id = payload.get("event_id")

    if (disruption_event is not None or interrupt_responses is not None) and (
        not isinstance(run_id, str) or not run_id.strip()
    ):
        return {"error": "run_id must be a non-empty string for workflow requests."}

    # Resume an interrupted HITL request
    if interrupt_responses is not None:

        if user_message is not None or disruption_event is not None:
            return {
                "error": (
                    "Provide only 'interrupt_responses' when resuming "
                    "an interrupted request."
                )
            }

        if (
            not isinstance(interrupt_responses, list)
            or not interrupt_responses
            or any(
                not isinstance(response, dict)
                or not isinstance(response.get("interruptId"), str)
                or "response" not in response
                for response in interrupt_responses
            )
        ):
            return {
                "error": (
                    "'interrupt_responses' must be a non-empty list of "
                    "objects containing 'interruptId' and 'response'."
                )
            }

        agent_input = [
            {
                "interruptResponse": {
                    "interruptId": response["interruptId"],
                    "response": response["response"],
                }
            }
            for response in interrupt_responses
        ]

    # Operational disruption event
    elif disruption_event is not None:
        if user_message is not None:
            return {
                "error": (
                    "Provide either 'prompt' or 'disruption_event', "
                    "not both."
                )
            }

        try:
            processing_result = apply_disruption_event(
                state=state,
                event=disruption_event,
            )
        except ValueError as error:
            return {"error": str(error)}

        if not processing_result["applied"]:
            return {
                "status": processing_result["status"],
                "event": processing_result["event"],
                "message": (
                    "Disruption event "
                    f"{processing_result['event']['event_id']} "
                    "was already processed."
                ),
            }

        canonical_event = processing_result["event"]
        event_id = canonical_event["event_id"]
        agent_input = (
            f"Investigate shipment {canonical_event['shipment_id']} "
            "after this operational disruption and determine the best "
            "recovery action."
        )

    # Normal invocation
    elif not isinstance(user_message, str) or not user_message.strip():
        return {
            "error": "Invalid input: 'prompt' must be a non-empty string"
        }

    else:
        agent_input = user_message

    request_session_id = getattr(context, "session_id", None)
    request_agent = agent
    if disruption_event is not None or interrupt_responses is not None:
        session_manager = None
        if request_session_id:
            session_manager = RepositorySessionManager(
                session_id=request_session_id,
                session_repository=DynamoDBSessionRepository(),
            )
        request_agent = create_recovery_agent(
            state,
            session_manager=session_manager,
            run_id=run_id,
            event_id=event_id,
            runtime_session_id=request_session_id,
        )

    result = request_agent(agent_input)

    response = {
        "result": result.message,
        "stop_reason": result.stop_reason,
    }

    if result.interrupts:
        response["interrupts"] = [
            interrupt.to_dict()
            for interrupt in result.interrupts
        ]

    return response


if __name__ == "__main__":
    app.run()