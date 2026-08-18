import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum

class EventType(Enum):
    STATE_SET = "STATE_SET"
    STATE_INCREMENT = "STATE_INCREMENT"
    STATE_DELETE = "STATE_DELETE"
    GOVERNANCE_APPROVE = "GOVERNANCE_APPROVE"
    INNOVATION_PROPOSE = "INNOVATION_PROPOSE"
    CONSTITUTION_RATIFY = "CONSTITUTION_RATIFY"

@dataclass(frozen=True)
class CanonicalEvent:
    """
    Immutable event record.
    Every field is committed; no field can change after creation.
    """
    event_id: str
    stream_id: str
    sequence: int
    event_type: str
    schema_version: int
    causation_id: Optional[str]
    correlation_id: str
    actor_id: str
    payload: Dict[str, Any]
    constitution_hash: str
    vik_hash: str
    previous_event_hash: Optional[str]
    timestamp: float
    
    def compute_hash(self) -> str:
        """
        Deterministic event hash.
        Includes all fields + previous hash (chain).
        """
        event_data = {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "causation_id": self.causation_id,
            "correlation_id": self.correlation_id,
            "actor_id": self.actor_id,
            "payload": self.payload,
            "constitution_hash": self.constitution_hash,
            "vik_hash": self.vik_hash,
            "previous_event_hash": self.previous_event_hash,
            "timestamp": self.timestamp,
        }
        event_json = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(event_json.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "stream_id": self.stream_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "causation_id": self.causation_id,
            "correlation_id": self.correlation_id,
            "actor_id": self.actor_id,
            "payload": self.payload,
            "constitution_hash": self.constitution_hash,
            "vik_hash": self.vik_hash,
            "previous_event_hash": self.previous_event_hash,
            "timestamp": self.timestamp,
        }

class CanonicalEventBuilder:
    """
    Builder for CanonicalEvent.
    Ensures all required fields are set and validated.
    """
    
    def __init__(self):
        self.fields = {}
    
    def event_id(self, event_id: str) -> 'CanonicalEventBuilder':
        self.fields["event_id"] = event_id
        return self
    
    def stream_id(self, stream_id: str) -> 'CanonicalEventBuilder':
        self.fields["stream_id"] = stream_id
        return self
    
    def sequence(self, sequence: int) -> 'CanonicalEventBuilder':
        self.fields["sequence"] = sequence
        return self
    
    def event_type(self, event_type: str) -> 'CanonicalEventBuilder':
        self.fields["event_type"] = event_type
        return self
    
    def schema_version(self, schema_version: int) -> 'CanonicalEventBuilder':
        self.fields["schema_version"] = schema_version
        return self
    
    def causation_id(self, causation_id: Optional[str]) -> 'CanonicalEventBuilder':
        self.fields["causation_id"] = causation_id
        return self
    
    def correlation_id(self, correlation_id: str) -> 'CanonicalEventBuilder':
        self.fields["correlation_id"] = correlation_id
        return self
    
    def actor_id(self, actor_id: str) -> 'CanonicalEventBuilder':
        self.fields["actor_id"] = actor_id
        return self
    
    def payload(self, payload: Dict[str, Any]) -> 'CanonicalEventBuilder':
        self.fields["payload"] = payload
        return self
    
    def constitution_hash(self, constitution_hash: str) -> 'CanonicalEventBuilder':
        self.fields["constitution_hash"] = constitution_hash
        return self
    
    def vik_hash(self, vik_hash: str) -> 'CanonicalEventBuilder':
        self.fields["vik_hash"] = vik_hash
        return self
    
    def previous_event_hash(self, previous_event_hash: Optional[str]) -> 'CanonicalEventBuilder':
        self.fields["previous_event_hash"] = previous_event_hash
        return self
    
    def timestamp(self, timestamp: float) -> 'CanonicalEventBuilder':
        self.fields["timestamp"] = timestamp
        return self
    
    def build(self) -> CanonicalEvent:
        required = [
            "event_id", "stream_id", "sequence", "event_type",
            "schema_version", "correlation_id", "actor_id", "payload",
            "constitution_hash", "vik_hash", "timestamp"
        ]
        
        missing = [f for f in required if f not in self.fields]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        return CanonicalEvent(**self.fields)
