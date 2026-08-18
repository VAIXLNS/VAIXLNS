from typing import List, Dict, Any, Tuple
from canonical_event import CanonicalEvent
from canonical_state import CanonicalState
from transition import TransitionFunction
import hashlib
import json

class ReplayEngine:
    """
    Deterministic replay from genesis through event sequence.
    Proves that same history produces same state root.
    """
    
    def __init__(self, transition_func: TransitionFunction):
        self.transition = transition_func
        self.replay_log: List[Dict[str, Any]] = []
    
    def validate_event_sequence(self, events: List[CanonicalEvent]) -> Tuple[bool, str]:
        """
        Validate event sequence integrity before replay.
        Checks: sequence continuity, hash chain, constitution, VIK.
        """
        
        if not events:
            return True, "Empty sequence is valid"
        
        # Check sequence starts at 1
        if events[0].sequence != 1:
            return False, f"First event must have sequence 1, got {events[0].sequence}"
        
        # Check sequence is monotonic
        for i, event in enumerate(events):
            expected_seq = i + 1
            if event.sequence != expected_seq:
                return False, f"Event {i}: expected sequence {expected_seq}, got {event.sequence}"
        
        # Check hash chain
        if events[0].previous_event_hash is not None:
            return False, "First event must have no previous hash"
        
        for i in range(1, len(events)):
            expected_prev = events[i-1].compute_hash()
            actual_prev = events[i].previous_event_hash
            if expected_prev != actual_prev:
                return False, f"Event {i}: hash chain broken. Expected {expected_prev}, got {actual_prev}"
        
        # Check constitution consistency
        const_hash = events[0].constitution_hash
        for i, event in enumerate(events):
            if event.constitution_hash != const_hash:
                return False, f"Event {i}: constitution hash changed"
        
        # Check VIK consistency
        vik_hash = events[0].vik_hash
        for i, event in enumerate(events):
            if event.vik_hash != vik_hash:
                return False, f"Event {i}: VIK hash changed"
        
        return True, "Sequence valid"
    
    def replay(self, genesis: CanonicalState, events: List[CanonicalEvent]) -> Tuple[CanonicalState, Dict[str, Any]]:
        """
        Deterministic replay from genesis through events.
        Returns final state and replay metadata.
        """
        
        # Clear log
        self.replay_log = []
        
        # Validate sequence
        valid, reason = self.validate_event_sequence(events)
        if not valid:
            raise ValueError(f"Invalid event sequence: {reason}")
        
        # Log start
        self.replay_log.append({
            "type": "REPLAY_START",
            "genesis_version": genesis.state_version,
            "genesis_root": genesis.compute_state_root(),
            "event_count": len(events),
            "constitution_hash": genesis.constitution_hash if events else "N/A",
        })
        
        # Apply each event
        current_state = genesis
        for i, event in enumerate(events):
            try:
                next_state = self.transition.apply(current_state, event)
                
                self.replay_log.append({
                    "type": "TRANSITION",
                    "event_index": i,
                    "event_id": event.event_id,
                    "sequence": event.sequence,
                    "from_state_version": current_state.state_version,
                    "to_state_version": next_state.state_version,
                    "from_root": current_state.compute_state_root(),
                    "to_root": next_state.compute_state_root(),
                })
                
                current_state = next_state
            
            except Exception as e:
                self.replay_log.append({
                    "type": "TRANSITION_FAIL",
                    "event_index": i,
                    "event_id": event.event_id,
                    "error": str(e),
                })
                raise ValueError(f"Replay failed at event {i}: {e}")
        
        # Log end
        final_root = current_state.compute_state_root()
        self.replay_log.append({
            "type": "REPLAY_END",
            "final_state_version": current_state.state_version,
            "final_root": final_root,
            "event_count": len(events),
        })
        
        metadata = {
            "replay_valid": True,
            "genesis_root": genesis.compute_state_root(),
            "final_root": final_root,
            "events_processed": len(events),
            "log": self.replay_log,
        }
        
        return current_state, metadata
    
    def get_replay_log(self) -> List[Dict[str, Any]]:
        """Return immutable replay log."""
        return [entry.copy() for entry in self.replay_log]
