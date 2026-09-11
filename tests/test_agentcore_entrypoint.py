import importlib

import pytest

from src.simulation.operational_state import OperationalState
from src.state.in_memory_state_repository import InMemoryStateRepository


@pytest.fixture
def entrypoint_module(monkeypatch):
    monkeypatch.setenv("STATE_REPOSITORY", "in_memory")
    module = importlib.import_module("src.agent.agentcore_entrypoint")
    module.state = OperationalState(repository=InMemoryStateRepository())
    return module


def make_event(**overrides):
    event = {
        "event_id": "SIM-ENTRYPOINT-001",
        "event_type": "VEHICLE_BREAKDOWN",
        "shipment_id": "SHP-0048",
        "delay_minutes": 480,
        "severity": "LOW",
        "source": "simulation_ui",
    }
    event.update(overrides)
    return event


def workflow_payload(**overrides):
    payload = {"run_id": "RUN-ENTRYPOINT-001"}
    payload.update(overrides)
    return payload


def test_valid_disruption_event_reaches_centralized_processing(
    entrypoint_module,
    monkeypatch,
):
    processing_result = {
        "applied": True,
        "status": "applied",
        "event": make_event(severity="HIGH"),
    }
    process = lambda state, event: processing_result
    monkeypatch.setattr(
        entrypoint_module,
        "apply_disruption_event",
        process,
    )

    captured = {}

    def fake_agent(prompt):
        captured["prompt"] = prompt
        return type(
            "Result",
            (),
            {"message": "started", "stop_reason": "end_turn", "interrupts": []},
        )()

    monkeypatch.setattr(entrypoint_module, "agent", fake_agent)
    monkeypatch.setattr(
        entrypoint_module,
        "create_recovery_agent",
        lambda *args, **kwargs: fake_agent,
    )

    response = entrypoint_module.agent_invocation(
        workflow_payload(disruption_event=make_event()),
        None,
    )

    assert response["result"] == "started"
    assert captured["prompt"] == (
        "Investigate shipment SHP-0048 after this operational disruption "
        "and determine the best recovery action."
    )


def test_invalid_disruption_event_does_not_invoke_agent(
    entrypoint_module,
    monkeypatch,
):
    monkeypatch.setattr(
        entrypoint_module,
        "apply_disruption_event",
        lambda state, event: (_ for _ in ()).throw(
            ValueError("invalid disruption event")
        ),
    )
    fake_agent = lambda prompt: pytest.fail("agent should not be invoked")
    monkeypatch.setattr(entrypoint_module, "agent", fake_agent)
    monkeypatch.setattr(
        entrypoint_module,
        "create_recovery_agent",
        lambda *args, **kwargs: fake_agent,
    )

    response = entrypoint_module.agent_invocation(
        workflow_payload(disruption_event=make_event()),
        None,
    )

    assert response == {"error": "invalid disruption event"}


def test_duplicate_disruption_event_does_not_invoke_agent(
    entrypoint_module,
    monkeypatch,
):
    duplicate = {
        "applied": False,
        "status": "already_processed",
        "event": make_event(),
    }
    monkeypatch.setattr(
        entrypoint_module,
        "apply_disruption_event",
        lambda state, event: duplicate,
    )
    monkeypatch.setattr(
        entrypoint_module,
        "agent",
        lambda prompt: pytest.fail("agent should not be invoked"),
    )

    response = entrypoint_module.agent_invocation(
        workflow_payload(disruption_event=make_event()),
        None,
    )

    assert response["status"] == "already_processed"
    assert "already processed" in response["message"]


def test_normal_prompt_still_works(entrypoint_module, monkeypatch):
    captured = {}

    def fake_agent(prompt):
        captured["prompt"] = prompt
        return type(
            "Result",
            (),
            {"message": "normal", "stop_reason": "end_turn", "interrupts": []},
        )()

    monkeypatch.setattr(entrypoint_module, "agent", fake_agent)

    response = entrypoint_module.agent_invocation(
        {"prompt": "Investigate SHP-0048."},
        None,
    )

    assert captured["prompt"] == "Investigate SHP-0048."
    assert response["result"] == "normal"


def test_hitl_interrupt_responses_behavior_is_unchanged(
    entrypoint_module,
    monkeypatch,
):
    captured = {}

    def fake_agent(prompt):
        captured["prompt"] = prompt
        return type(
            "Result",
            (),
            {"message": "resumed", "stop_reason": "end_turn", "interrupts": []},
        )()

    monkeypatch.setattr(entrypoint_module, "agent", fake_agent)
    monkeypatch.setattr(
        entrypoint_module,
        "create_recovery_agent",
        lambda *args, **kwargs: fake_agent,
    )
    interrupt_response = {
        "interruptId": "interrupt-1",
        "response": "yes",
    }

    response = entrypoint_module.agent_invocation(
        workflow_payload(interrupt_responses=[interrupt_response]),
        None,
    )

    assert captured["prompt"] == [
        {"interruptResponse": interrupt_response}
    ]
    assert response["result"] == "resumed"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "prompt": "Investigate SHP-0048.",
            "disruption_event": make_event(),
            "run_id": "RUN-ENTRYPOINT-001",
        },
        {
            "interrupt_responses": [
                {"interruptId": "interrupt-1", "response": "yes"}
            ],
            "disruption_event": make_event(),
            "run_id": "RUN-ENTRYPOINT-001",
        },
    ],
)
def test_conflicting_input_modes_are_rejected(entrypoint_module, payload):
    response = entrypoint_module.agent_invocation(payload, None)

    assert "error" in response


@pytest.mark.parametrize(
    "payload",
    [
        {"disruption_event": make_event()},
        {"interrupt_responses": [{"interruptId": "interrupt-1", "response": "yes"}]},
        {"run_id": "", "disruption_event": make_event()},
    ],
)
def test_workflow_requests_require_a_run_id(entrypoint_module, payload):
    response = entrypoint_module.agent_invocation(payload, None)

    assert response == {"error": "run_id must be a non-empty string for workflow requests."}


@pytest.mark.parametrize(
    "payload",
    [
        workflow_payload(disruption_event=make_event()),
        workflow_payload(
            event_id="SIM-ENTRYPOINT-001",
            interrupt_responses=[{"interruptId": "interrupt-1", "response": "yes"}],
        ),
    ],
)
def test_workflow_run_identity_is_bound_to_the_request_agent(
    entrypoint_module,
    monkeypatch,
    payload,
):
    monkeypatch.setattr(
        entrypoint_module,
        "apply_disruption_event",
        lambda state, event: {"applied": True, "status": "applied", "event": make_event()},
    )
    captured = {}

    def create_agent(*args, **kwargs):
        captured.update(kwargs)
        return lambda agent_input: type(
            "Result", (), {"message": "ok", "stop_reason": "end_turn", "interrupts": []}
        )()

    monkeypatch.setattr(entrypoint_module, "create_recovery_agent", create_agent)
    monkeypatch.setattr(entrypoint_module, "DynamoDBSessionRepository", lambda: object())
    monkeypatch.setattr(
        entrypoint_module,
        "RepositorySessionManager",
        lambda **kwargs: object(),
    )

    response = entrypoint_module.agent_invocation(
        payload,
        type("Context", (), {"session_id": "runtime-session-1"})(),
    )

    assert response["stop_reason"] == "end_turn"
    assert captured["run_id"] == "RUN-ENTRYPOINT-001"
    assert captured["runtime_session_id"] == "runtime-session-1"
    assert captured["event_id"] == "SIM-ENTRYPOINT-001"


def test_resume_without_context_session_id_still_binds_run_identity(
    entrypoint_module,
    monkeypatch,
):
    captured = {}

    def create_agent(*args, **kwargs):
        captured.update(kwargs)
        return lambda agent_input: type(
            "Result", (), {"message": "ok", "stop_reason": "end_turn", "interrupts": []}
        )()

    monkeypatch.setattr(entrypoint_module, "create_recovery_agent", create_agent)

    response = entrypoint_module.agent_invocation(
        workflow_payload(
            event_id="SIM-ENTRYPOINT-001",
            interrupt_responses=[{"interruptId": "interrupt-1", "response": "yes"}],
        ),
        None,
    )

    assert response["stop_reason"] == "end_turn"
    assert captured["run_id"] == "RUN-ENTRYPOINT-001"
    assert captured["event_id"] == "SIM-ENTRYPOINT-001"
    assert captured["runtime_session_id"] is None
    assert captured["session_manager"] is None