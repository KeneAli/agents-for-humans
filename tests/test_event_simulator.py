from unittest.mock import MagicMock

import pytest

from src.simulation.event_simulator import apply_disruption_event
from src.simulation.operational_state import OperationalState
from src.state.in_memory_state_repository import InMemoryStateRepository


def make_state():
    return OperationalState(repository=InMemoryStateRepository())


def make_event(**overrides):
    event = {
        "event_id": "SIM-A1B2C3D4",
        "event_type": "VEHICLE_BREAKDOWN",
        "shipment_id": "SHP-0048",
        "delay_minutes": 480,
        "severity": "LOW",
        "source": " simulation_ui ",
        "timestamp": "2026-09-08T20:30:00+00:00",
        "description": "Vehicle breakdown from the simulation UI.",
    }
    event.update(overrides)
    return event


def test_valid_new_event_is_applied():
    state = make_state()

    result = apply_disruption_event(state, make_event())

    assert result["applied"] is True
    assert result["status"] == "applied"
    assert result["event"]["severity"] == "HIGH"
    assert result["event"]["source"] == "simulation_ui"
    assert state.get_shipment_delay("SHP-0048") == 480


def test_duplicate_event_is_not_applied_twice():
    state = make_state()
    event = make_event()

    apply_disruption_event(state, event)
    result = apply_disruption_event(state, event)

    assert result["applied"] is False
    assert result["status"] == "already_processed"
    assert state.get_shipment_delay("SHP-0048") == 480


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"event_type": "UNKNOWN"}, "Unsupported disruption type"),
        ({"shipment_id": "SHP-NOT-FOUND"}, "Shipment SHP-NOT-FOUND not found"),
        ({"delay_minutes": 0}, "greater than zero"),
        ({"delay_minutes": -1}, "greater than zero"),
        ({"event_id": ""}, "event_id must be a non-empty string"),
        ({"event_id": "   "}, "event_id must be a non-empty string"),
    ],
)
def test_invalid_event_is_rejected(overrides, message):
    with pytest.raises(ValueError, match=message):
        apply_disruption_event(make_state(), make_event(**overrides))


def test_severity_is_derived_not_trusted():
    result = apply_disruption_event(
        make_state(),
        make_event(delay_minutes=720, severity="LOW"),
    )

    assert result["event"]["severity"] == "CRITICAL"


def test_repository_claim_happens_before_state_mutation():
    state = make_state()
    add_runtime_event = MagicMock()
    state.add_runtime_event = add_runtime_event

    def claim_before_mutation(**kwargs):
        assert state.runtime_events == []
        assert add_runtime_event.call_count == 0
        return True

    claim = MagicMock(side_effect=claim_before_mutation)
    state.repository.claim_disruption_event = claim

    apply_disruption_event(state, make_event())

    claim.assert_called_once()
    add_runtime_event.assert_called_once()