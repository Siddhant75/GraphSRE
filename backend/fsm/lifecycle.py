"""
Incident Finite State Machine (FSM) Lifecycle Engine
File: backend/fsm/lifecycle.py
"""
from enum import Enum
from typing import Dict, List, Set, Union


class IncidentState(str, Enum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    HYPOTHESIS_FORMED = "HYPOTHESIS_FORMED"
    CONSENSUS_REACHED = "CONSENSUS_REACHED"
    SANDBOX_SIMULATED = "SANDBOX_SIMULATED"
    REMEDIATING = "REMEDIATING"
    RESOLVED = "RESOLVED"


class IncidentLifecycleFSM:
    """
    Finite State Machine managing the lifecycle of an incident in GraphSRE.

    Valid transitions:
    - DETECTED -> TRIAGED
    - TRIAGED -> INVESTIGATING
    - INVESTIGATING -> HYPOTHESIS_FORMED
    - HYPOTHESIS_FORMED -> CONSENSUS_REACHED | INVESTIGATING (if refuted)
    - CONSENSUS_REACHED -> SANDBOX_SIMULATED | REMEDIATING
    - SANDBOX_SIMULATED -> REMEDIATING | INVESTIGATING (if simulation failed)
    - REMEDIATING -> RESOLVED | INVESTIGATING (if remediation failed)
    - RESOLVED -> terminal
    """

    VALID_TRANSITIONS: Dict[IncidentState, Set[IncidentState]] = {
        IncidentState.DETECTED: {IncidentState.TRIAGED},
        IncidentState.TRIAGED: {IncidentState.INVESTIGATING},
        IncidentState.INVESTIGATING: {IncidentState.HYPOTHESIS_FORMED},
        IncidentState.HYPOTHESIS_FORMED: {IncidentState.CONSENSUS_REACHED, IncidentState.INVESTIGATING},
        IncidentState.CONSENSUS_REACHED: {IncidentState.SANDBOX_SIMULATED, IncidentState.REMEDIATING},
        IncidentState.SANDBOX_SIMULATED: {IncidentState.REMEDIATING, IncidentState.INVESTIGATING},
        IncidentState.REMEDIATING: {IncidentState.RESOLVED, IncidentState.INVESTIGATING},
        IncidentState.RESOLVED: set()
    }

    def __init__(self, incident_id: str, initial_state: Union[IncidentState, str] = IncidentState.DETECTED):
        self.incident_id = incident_id
        if isinstance(initial_state, str) and not isinstance(initial_state, IncidentState):
            initial_state = IncidentState(initial_state)
        self.current_state = initial_state
        self.state_history: List[IncidentState] = [initial_state]

    def can_transition(self, next_state: Union[IncidentState, str]) -> bool:
        """Checks whether transitioning to next_state is valid from current_state."""
        if isinstance(next_state, str) and not isinstance(next_state, IncidentState):
            try:
                next_state = IncidentState(next_state)
            except ValueError:
                return False
        return next_state in self.VALID_TRANSITIONS.get(self.current_state, set())

    def transition(self, next_state: Union[IncidentState, str]) -> IncidentState:
        """
        Transitions the incident to next_state if valid.
        Raises ValueError if transition is invalid.
        """
        target_state = next_state
        if isinstance(target_state, str) and not isinstance(target_state, IncidentState):
            try:
                target_state = IncidentState(target_state)
            except ValueError:
                raise ValueError(
                    f"Invalid state transition for {self.incident_id}: "
                    f"cannot move from {self.current_state.value} to {next_state}"
                )

        if not self.can_transition(target_state):
            raise ValueError(
                f"Invalid state transition for {self.incident_id}: "
                f"cannot move from {self.current_state.value} to {target_state.value}"
            )
        self.current_state = target_state
        self.state_history.append(target_state)
        return self.current_state

    def is_terminal(self) -> bool:
        """Returns True if current state has no outbound transitions."""
        return len(self.VALID_TRANSITIONS.get(self.current_state, set())) == 0
