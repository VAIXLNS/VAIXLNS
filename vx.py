import hashlib
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import time

@dataclass
class Event:
    index: int
    timestamp: float
    actor: str
    action: str
    payload: Dict[str, Any]
    
    def to_dict(self):
        return asdict(self)

class StateMachine:
    """
    Deterministic state machine.
    Same genesis + same events + same rules = same state root.
    """
    
    def __init__(self, genesis: Dict[str, Any]):
        self.state = genesis.copy()
        self.events: List[Event] = []
        self.state_roots: List[str] = []
        self._compute_state_root()
    
    def _compute_state_root(self) -> str:
        """Hash current state deterministically."""
        state_json = json.dumps(self.state, sort_keys=True)
        root = hashlib.sha256(state_json.encode()).hexdigest()
        self.state_roots.append(root)
        return root
    
    def apply_event(self, actor: str, action: str, payload: Dict[str, Any]) -> str:
        """Apply event, return new state root."""
        event = Event(
            index=len(self.events),
            timestamp=time.time(),
            actor=actor,
            action=action,
            payload=payload
        )
        
        # Apply to state
        if action == "set":
            key = payload.get("key")
            value = payload.get("value")
            self.state[key] = value
        elif action == "increment":
            key = payload.get("key")
            self.state[key] = self.state.get(key, 0) + 1
        elif action == "delete":
            key = payload.get("key")
            if key in self.state:
                del self.state[key]
        
        self.events.append(event)
        return self._compute_state_root()
    
    def get_state_root(self) -> str:
        """Return current state root."""
        return self.state_roots[-1] if self.state_roots else None
    
    def get_state(self) -> Dict[str, Any]:
        """Return current state."""
        return self.state.copy()
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Return event log."""
        return [e.to_dict() for e in self.events]

class EventLedger:
    """
    Append-only immutable ledger.
    No event can be modified or reordered.
    """
    
    def __init__(self):
        self.ledger: List[Dict[str, Any]] = []
        self.ledger_hash = hashlib.sha256(b"").hexdigest()
    
    def append(self, event: Dict[str, Any]) -> str:
        """Append event, return ledger hash."""
        entry = {
            "sequence": len(self.ledger),
            "event": event,
            "previous_hash": self.ledger_hash,
            "timestamp": time.time()
        }
        
        # Chain hash
        entry_json = json.dumps(entry, sort_keys=True)
        entry["hash"] = hashlib.sha256(entry_json.encode()).hexdigest()
        
        self.ledger.append(entry)
        self.ledger_hash = entry["hash"]
        
        return self.ledger_hash
    
    def get_ledger(self) -> List[Dict[str, Any]]:
        """Return immutable ledger."""
        return [e.copy() for e in self.ledger]
    
    def get_ledger_hash(self) -> str:
        """Return chain hash."""
        return self.ledger_hash
    
    def verify_integrity(self) -> bool:
        """Verify ledger chain integrity."""
        if not self.ledger:
            return True
        
        prev_hash = hashlib.sha256(b"").hexdigest()
        for entry in self.ledger:
            if entry["previous_hash"] != prev_hash:
                return False
            prev_hash = entry["hash"]
        
        return prev_hash == self.ledger_hash

class VXRuntime:
    """
    VX Runtime: Constitution + StateMachine + Ledger
    Proof-Before-Effect enforcement.
    """
    
    def __init__(self, constitution, genesis: Dict[str, Any]):
        self.constitution = constitution
        self.state_machine = StateMachine(genesis)
        self.ledger = EventLedger()
        self.executed_count = 0
        self.rejected_count = 0
    
    def execute_command(
        self,
        actor: str,
        action: str,
        payload: Dict[str, Any],
        proof_required: bool = False,
        has_proof: bool = False,
        self_certification: bool = False,
        mutates_vik: bool = False
    ) -> Tuple[bool, str, str]:
        """
        Execute command with proof-before-effect.
        Returns (success, reason, state_root).
        """
        
        current_state_root = self.state_machine.get_state_root()
        
        # Check proof requirement
        if proof_required and not has_proof:
            reason = "Proof required but not provided"
            self.rejected_count += 1
            # Log rejection without state change
            self.ledger.append({
                "actor": actor,
                "action": action,
                "result": "REJECT",
                "reason": reason
            })
            return False, reason, current_state_root
        
        # Authorize
        context = {
            "has_proof": has_proof,
            "self_certification": self_certification,
            "mutates_vik": mutates_vik
        }
        
        decision, auth_reason = self.constitution.authorize(
            actor, action, context, current_state_root
        )
        
        if decision.value == "DENY":
            self.rejected_count += 1
            self.ledger.append({
                "actor": actor,
                "action": action,
                "result": "DENY",
                "reason": auth_reason
            })
            return False, auth_reason, current_state_root
        
        # Execute
        new_state_root = self.state_machine.apply_event(actor, action, payload)
        
        # Log to ledger
        self.ledger.append({
            "actor": actor,
            "action": action,
            "payload": payload,
            "result": "ALLOW",
            "state_root": new_state_root
        })
        
        self.executed_count += 1
        return True, "Executed", new_state_root
    
    def get_state_root(self) -> str:
        return self.state_machine.get_state_root()
    
    def get_state(self) -> Dict[str, Any]:
        return self.state_machine.get_state()
    
    def get_ledger(self) -> List[Dict[str, Any]]:
        return self.ledger.get_ledger()
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "executed": self.executed_count,
            "rejected": self.rejected_count,
            "ledger_valid": self.ledger.verify_integrity(),
            "ledger_hash": self.ledger.get_ledger_hash(),
            "state_root": self.get_state_root()
        }
