import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class CanonicalState:
    """
    Immutable state snapshot.
    Includes versioning metadata to ensure deterministic encoding.
    """
    state_version: int
    constitution_hash: str
    vik_hash: str
    last_sequence: int
    last_event_hash: str
    data: Dict[str, Any]
    
    def canonical_encode(self) -> str:
        """
        Deterministic canonical encoding.
        Same state always produces same encoding (no hash variation).
        """
        state_dict = {
            "state_version": self.state_version,
            "constitution_hash": self.constitution_hash,
            "vik_hash": self.vik_hash,
            "last_sequence": self.last_sequence,
            "last_event_hash": self.last_event_hash,
            "data": self.data,
        }
        return json.dumps(state_dict, sort_keys=True, separators=(',', ':'))
    
    def compute_state_root(self) -> str:
        """
        Canonical state root hash.
        Deterministic: same state → same root.
        """
        encoding = self.canonical_encode()
        return hashlib.sha256(encoding.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_version": self.state_version,
            "constitution_hash": self.constitution_hash,
            "vik_hash": self.vik_hash,
            "last_sequence": self.last_sequence,
            "last_event_hash": self.last_event_hash,
            "data": self.data,
        }

class CanonicalStateBuilder:
    """
    Builder for CanonicalState with validation.
    """
    
    def __init__(self):
        self.fields = {}
    
    def state_version(self, version: int) -> 'CanonicalStateBuilder':
        self.fields["state_version"] = version
        return self
    
    def constitution_hash(self, hash: str) -> 'CanonicalStateBuilder':
        self.fields["constitution_hash"] = hash
        return self
    
    def vik_hash(self, hash: str) -> 'CanonicalStateBuilder':
        self.fields["vik_hash"] = hash
        return self
    
    def last_sequence(self, seq: int) -> 'CanonicalStateBuilder':
        self.fields["last_sequence"] = seq
        return self
    
    def last_event_hash(self, hash: str) -> 'CanonicalStateBuilder':
        self.fields["last_event_hash"] = hash
        return self
    
    def data(self, data: Dict[str, Any]) -> 'CanonicalStateBuilder':
        self.fields["data"] = data
        return self
    
    def build(self) -> CanonicalState:
        required = [
            "state_version", "constitution_hash", "vik_hash",
            "last_sequence", "last_event_hash", "data"
        ]
        
        missing = [f for f in required if f not in self.fields]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        return CanonicalState(**self.fields)
