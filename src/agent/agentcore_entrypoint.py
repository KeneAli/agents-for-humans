from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent.recovery_agent import create_recovery_agent
from src.simulation.operational_state import OperationalState


app = BedrockAgentCoreApp()

state = OperationalState()
agent = create_recovery_agent(state)


@app.entrypoint
def agent_invocation(payload, context):

    user_message = payload.get("prompt")
    interrupt_responses = payload.get("interrupt_responses")

    # Resume an interrupted HITL request
    if interrupt_responses is not None:

        if user_message is not None:
            return {
                "error": (
                    "Provide either 'prompt' or 'interrupt_responses', "
                    "not both."
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

    # Normal invocation
    elif not isinstance(user_message, str) or not user_message.strip():
        return {
            "error": "Invalid input: 'prompt' must be a non-empty string"
        }

    else:
        agent_input = user_message

    result = agent(agent_input)

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