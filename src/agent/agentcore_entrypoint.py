from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent.recovery_agent import create_recovery_agent
from src.simulation.operational_state import OperationalState


app = BedrockAgentCoreApp()

state = OperationalState()
agent = create_recovery_agent(state)


@app.entrypoint
def agent_invocation(payload, context):
    user_message = payload.get("prompt", "")

    if not isinstance(user_message, str) or not user_message.strip():
        return {
            "error": "Invalid input: 'prompt' must be a non-empty string"
        }

    result = agent(user_message)

    return {
        "result": result.message,
        "stop_reason": result.stop_reason,
    }


if __name__ == "__main__":
    app.run()