from typing import Dict, Any, Callable
from canonical_event import CanonicalEvent
from canonical_state import CanonicalState, CanonicalStateBuilder

class TransitionFunction:
    """
    Pure deterministic transition function.
    S_{n+1} = T(S_n, E_n)
    
    Same input → Same output, always.
    No side effects, no external calls, no time/randomness.
    """
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register built-in event handlers."""
        self.handlers["STATE_SET"] = self._handle_state_set
        self.handlers["STATE_INCREMENT"] = self._handle_state_increment
        self.handlers["STATE_DELETE"] = self._handle_state_delete
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register custom event handler."""
        self.handlers[event_type] = handler
    
    def _handle_state_set(self, data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """SET: update key-value pair."""
        new_data = data.copy()
        key = payload.get("key")
        value = payload.get("value")
        if key is None:
            raise ValueError("SET requires 'key' in payload")
        new_data[key] = value
        return new_data
    
    def _handle_state_increment(self, data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """INCREMENT: increment numeric value."""
        new_data = data.copy()
        key = payload.get("key")
        if key is None:
            raise ValueError("INCREMENT requires 'key' in payload")
        current = new_data.get(key, 0)
        new_data[key] = current + 1
        return new_data
    
    def _handle_state_delete(self, data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """DELETE: remove key."""
        new_data = data.copy()
        key = payload.get("key")
        if key is None:
            raise ValueError("DELETE requires 'key' in payload")
        if key in new_data:
            del new_data[key]
        return new_data
    
    def apply(self, state: CanonicalState, event: CanonicalEvent) -> CanonicalState:
        """
        Apply event to state deterministically.
        Returns new CanonicalState or raises error.
        """
        
        # Validate event type is registered
        if event.event_type not in self.handlers:
            raise ValueError(f"Unknown event type: {event.event_type}")
        
        # Validate constitution hash matches
        if state.constitution_hash != event.constitution_hash:
            raise ValueError(
                f"Constitution mismatch: state has {state.constitution_hash}, "
                f"event has {event.constitution_hash}"
            )
        
        # Validate VIK hash matches
        if state.vik_hash != event.vik_hash:
            raise ValueError(
                f"VIK mismatch: state has {state.vik_hash}, "
                f"event has {event.vik_hash}"
            )
        
        # Validate sequence is monotonic
        if event.sequence != state.last_sequence + 1:
            raise ValueError(
                f"Sequence error: expected {state.last_sequence + 1}, "
                f"got {event.sequence}"
            )
        
        # Validate event chain
        if event.previous_event_hash != state.last_event_hash:
            raise ValueError(
                f"Event chain broken: expected previous hash {state.last_event_hash}, "
                f"got {event.previous_event_hash}"
            )
        
        # Execute handler
        handler = self.handlers[event.event_type]
        try:
            new_data = handler(state.data, event.payload)
        except Exception as e:
            raise ValueError(f"Handler error for {event.event_type}: {e}")
        
        # Build new canonical state
        new_state = CanonicalStateBuilder() \
            .state_version(state.state_version + 1) \
            .constitution_hash(event.constitution_hash) \
            .vik_hash(event.vik_hash) \
            .last_sequence(event.sequence) \
            .last_event_hash(event.compute_hash()) \
            .data(new_data) \
            .build()
        
        return new_state
