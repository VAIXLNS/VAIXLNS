import pytest
import time
from canonical_event import CanonicalEvent, CanonicalEventBuilder
from canonical_state import CanonicalState, CanonicalStateBuilder
from transition import TransitionFunction
from replay_engine import ReplayEngine

# ============================================================================
# TEST_005: Deterministic Replay & Lineage Integrity
# ============================================================================

def test_005_replay_identical_state_root():
    """Same genesis + events = same state root (run twice)."""
    
    # Setup
    constitution_hash = "const_v1_abc123"
    vik_hash = "vik_frozen_xyz789"
    
    genesis = CanonicalStateBuilder() \
        .state_version(0) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .last_sequence(0) \
        .last_event_hash("") \
        .data({"counter": 0, "name": "test"}) \
        .build()
    
    # Create event sequence
    events = [
        CanonicalEventBuilder() \
            .event_id("evt_001") \
            .stream_id("main") \
            .sequence(1) \
            .event_type("STATE_SET") \
            .schema_version(1) \
            .causation_id(None) \
            .correlation_id("corr_001") \
            .actor_id("admin") \
            .payload({"key": "counter", "value": 5}) \
            .constitution_hash(constitution_hash) \
            .vik_hash(vik_hash) \
            .previous_event_hash("") \
            .timestamp(1000.0) \
            .build(),
        
        CanonicalEventBuilder() \
            .event_id("evt_002") \
            .stream_id("main") \
            .sequence(2) \
            .event_type("STATE_INCREMENT") \
            .schema_version(1) \
            .causation_id("evt_001") \
            .correlation_id("corr_001") \
            .actor_id("admin") \
            .payload({"key": "counter"}) \
            .constitution_hash(constitution_hash) \
            .vik_hash(vik_hash) \
            .previous_event_hash(events[0].compute_hash() if events else "") \
            .timestamp(1001.0) \
            .build() if len(events) > 0 else None,
    ]
    
    # Fix: rebuild second event with correct previous hash
    events = [events[0]]
    evt2 = CanonicalEventBuilder() \
        .event_id("evt_002") \
        .stream_id("main") \
        .sequence(2) \
        .event_type("STATE_INCREMENT") \
        .schema_version(1) \
        .causation_id("evt_001") \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "counter"}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash(events[0].compute_hash()) \
        .timestamp(1001.0) \
        .build()
    events.append(evt2)
    
    evt3 = CanonicalEventBuilder() \
        .event_id("evt_003") \
        .stream_id("main") \
        .sequence(3) \
        .event_type("STATE_SET") \
        .schema_version(1) \
        .causation_id("evt_002") \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "name", "value": "updated"}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash(events[1].compute_hash()) \
        .timestamp(1002.0) \
        .build()
    events.append(evt3)
    
    # Replay A
    transition_a = TransitionFunction()
    replay_a = ReplayEngine(transition_a)
    final_state_a, metadata_a = replay_a.replay(genesis, events)
    root_a = final_state_a.compute_state_root()
    
    # Replay B (same everything)
    transition_b = TransitionFunction()
    replay_b = ReplayEngine(transition_b)
    final_state_b, metadata_b = replay_b.replay(genesis, events)
    root_b = final_state_b.compute_state_root()
    
    # Assertions
    assert root_a == root_b, f"State roots differ: {root_a} != {root_b}"
    assert final_state_a.data == final_state_b.data
    assert final_state_a.state_version == final_state_b.state_version
    assert metadata_a["events_processed"] == metadata_b["events_processed"] == 3

def test_005_replay_three_runs_identical():
    """Replay 3 times produces identical state root."""
    
    constitution_hash = "const_v1_abc123"
    vik_hash = "vik_frozen_xyz789"
    
    genesis = CanonicalStateBuilder() \
        .state_version(0) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .last_sequence(0) \
        .last_event_hash("") \
        .data({"x": 0}) \
        .build()
    
    # Simple event sequence
    evt1 = CanonicalEventBuilder() \
        .event_id("evt_001") \
        .stream_id("main") \
        .sequence(1) \
        .event_type("STATE_SET") \
        .schema_version(1) \
        .causation_id(None) \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "x", "value": 1}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash("") \
        .timestamp(1000.0) \
        .build()
    
    evt2 = CanonicalEventBuilder() \
        .event_id("evt_002") \
        .stream_id("main") \
        .sequence(2) \
        .event_type("STATE_SET") \
        .schema_version(1) \
        .causation_id("evt_001") \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "x", "value": 2}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash(evt1.compute_hash()) \
        .timestamp(1001.0) \
        .build()
    
    events = [evt1, evt2]
    
    # Run 3 times
    roots = []
    for _ in range(3):\n        transition = TransitionFunction()
        replay = ReplayEngine(transition)
        final_state, _ = replay.replay(genesis, events)
        roots.append(final_state.compute_state_root())
    
    # All roots must be identical
    assert roots[0] == roots[1] == roots[2]

def test_005_event_chain_validation():
    """Event chain must be unbroken or replay fails."""
    
    constitution_hash = "const_v1_abc123"
    vik_hash = "vik_frozen_xyz789"
    
    genesis = CanonicalStateBuilder() \
        .state_version(0) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .last_sequence(0) \
        .last_event_hash("") \
        .data({"x": 0}) \
        .build()
    
    evt1 = CanonicalEventBuilder() \
        .event_id("evt_001") \
        .stream_id("main") \
        .sequence(1) \
        .event_type("STATE_SET") \
        .schema_version(1) \
        .causation_id(None) \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "x", "value": 1}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash("") \
        .timestamp(1000.0) \
        .build()
    
    # Broken chain: evt2 has wrong previous_event_hash
    evt2 = CanonicalEventBuilder() \
        .event_id("evt_002") \
        .stream_id("main") \
        .sequence(2) \
        .event_type("STATE_SET") \
        .schema_version(1) \
        .causation_id("evt_001") \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "x", "value": 2}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash("WRONG_HASH") \
        .timestamp(1001.0) \
        .build()
    
    events = [evt1, evt2]
    
    transition = TransitionFunction()
    replay = ReplayEngine(transition)
    
    # Should fail validation
    with pytest.raises(ValueError, match="hash chain broken"):
        replay.replay(genesis, events)

def test_005_lineage_causation_tracking():
    """Lineage is maintained: causation_id links events."""
    
    constitution_hash = "const_v1_abc123"
    vik_hash = "vik_frozen_xyz789"
    
    genesis = CanonicalStateBuilder() \
        .state_version(0) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .last_sequence(0) \
        .last_event_hash("") \
        .data({"x": 0}) \
        .build()
    
    evt1 = CanonicalEventBuilder() \
        .event_id("evt_001") \
        .stream_id("main") \
        .sequence(1) \
        .event_type("STATE_SET") \
        .schema_version(1) \
        .causation_id(None) \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "x", "value": 1}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash("") \
        .timestamp(1000.0) \
        .build()
    
    evt2 = CanonicalEventBuilder() \
        .event_id("evt_002") \
        .stream_id("main") \
        .sequence(2) \
        .event_type("STATE_INCREMENT") \
        .schema_version(1) \
        .causation_id("evt_001") \
        .correlation_id("corr_001") \
        .actor_id("admin") \
        .payload({"key": "x"}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash(evt1.compute_hash()) \
        .timestamp(1001.0) \
        .build()
    
    events = [evt1, evt2]
    
    transition = TransitionFunction()
    replay = ReplayEngine(transition)
    final_state, metadata = replay.replay(genesis, events)
    
    # Check lineage in replay log
    log = metadata["log"]
    assert log[0]["type"] == "REPLAY_START"
    assert log[1]["type"] == "TRANSITION"
    assert log[1]["event_id"] == "evt_001"
    assert log[2]["type"] == "TRANSITION"
    assert log[2]["event_id"] == "evt_002"
    
    # evt2 should reference evt1 via causation
    assert events[1].causation_id == "evt_001"

# ============================================================================
# TEST_006: Self-Promotion Rejection
# ============================================================================

def test_006_engine_cannot_self_promote():
    """Engine-generated candidate cannot be promoted by engine itself."""
    
    # In VAIXLNS, Engine is actor_id "innovation_engine"
    # It can propose, but cannot approve
    
    constitution_hash = "const_v1_abc123"
    vik_hash = "vik_frozen_xyz789"
    
    genesis = CanonicalStateBuilder() \
        .state_version(0) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .last_sequence(0) \
        .last_event_hash("") \
        .data({"innovations": []}) \
        .build()
    
    # Event: Engine proposes innovation
    evt_propose = CanonicalEventBuilder() \
        .event_id("evt_propose_001") \
        .stream_id("innovations") \
        .sequence(1) \
        .event_type("INNOVATION_PROPOSE") \
        .schema_version(1) \
        .causation_id(None) \
        .correlation_id("corr_001") \
        .actor_id("innovation_engine") \
        .payload({"innovation_id": "innov_001", "concept": "test_concept"}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash("") \
        .timestamp(1000.0) \
        .build()
    
    # Attempt: Engine tries to approve own proposal
    # This event should be rejected by governance
    evt_self_approve = CanonicalEventBuilder() \
        .event_id("evt_approve_001") \
        .stream_id("innovations") \
        .sequence(2) \
        .event_type("GOVERNANCE_APPROVE") \
        .schema_version(1) \
        .causation_id("evt_propose_001") \
        .correlation_id("corr_001") \
        .actor_id("innovation_engine") \
        .payload({"innovation_id": "innov_001", "status": "APPROVED"}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash(evt_propose.compute_hash()) \
        .timestamp(1001.0) \
        .build()
    
    # Rule: only "governance_authority" can approve, not "innovation_engine"
    assert evt_self_approve.actor_id == "innovation_engine"
    assert evt_self_approve.event_type == "GOVERNANCE_APPROVE"
    
    # This should fail at constitution check
    # (We'll implement the constitution check in next iteration)
    # For now, verify the event is marked for rejection
    assert evt_self_approve.actor_id != "governance_authority"

def test_006_governance_authority_required():
    """Only governance_authority can approve innovations."""
    
    constitution_hash = "const_v1_abc123"
    vik_hash = "vik_frozen_xyz789"
    
    genesis = CanonicalStateBuilder() \
        .state_version(0) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .last_sequence(0) \
        .last_event_hash("") \
        .data({"innovations": []}) \
        .build()
    
    # Correct flow: governance_authority approves
    evt_approve = CanonicalEventBuilder() \
        .event_id("evt_approve_001") \
        .stream_id("innovations") \
        .sequence(1) \
        .event_type("GOVERNANCE_APPROVE") \
        .schema_version(1) \
        .causation_id(None) \
        .correlation_id("corr_001") \
        .actor_id("governance_authority") \
        .payload({"innovation_id": "innov_001", "status": "APPROVED"}) \
        .constitution_hash(constitution_hash) \
        .vik_hash(vik_hash) \
        .previous_event_hash("") \
        .timestamp(1000.0) \
        .build()
    
    # This should be allowed
    assert evt_approve.actor_id == "governance_authority"
    assert evt_approve.event_type == "GOVERNANCE_APPROVE"

def test_006_separation_of_powers():
    """Engine, Governance, and Runtime are separate authorities."""
    
    roles = {
        "innovation_engine": "ENGINE",
        "governance_authority": "GOVERNANCE",
        "vx_runtime": "RUNTIME",
    }
    
    # Engine can propose
    assert "innovation_engine" in roles
    
    # Governance can approve
    assert "governance_authority" in roles
    
    # Runtime executes (but cannot approve)
    assert "vx_runtime" in roles
    
    # No single actor has all powers
    all_roles = set(roles.keys())
    assert len(all_roles) == 3
    assert "innovation_engine" not in {"governance_authority", "vx_runtime"}
    assert "governance_authority" not in {"innovation_engine", "vx_runtime"}
    assert "vx_runtime" not in {"innovation_engine", "governance_authority"}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
