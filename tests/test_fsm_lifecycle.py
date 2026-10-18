"""
Unit and Integration Tests for Incident Lifecycle Finite State Machine (FSM)
File: tests/test_fsm_lifecycle.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.fsm.lifecycle import IncidentLifecycleFSM, IncidentState


class TestIncidentLifecycleFSM(unittest.TestCase):

    def test_fsm_initialization(self):
        fsm = IncidentLifecycleFSM("inc_test_01", IncidentState.DETECTED)
        self.assertEqual(fsm.current_state, IncidentState.DETECTED)
        self.assertEqual(len(fsm.state_history), 1)
        self.assertFalse(fsm.is_terminal())

    def test_fsm_valid_linear_progression(self):
        fsm = IncidentLifecycleFSM("inc_test_02", IncidentState.DETECTED)

        # DETECTED -> TRIAGED
        self.assertTrue(fsm.can_transition(IncidentState.TRIAGED))
        fsm.transition(IncidentState.TRIAGED)
        self.assertEqual(fsm.current_state, IncidentState.TRIAGED)

        # TRIAGED -> INVESTIGATING
        self.assertTrue(fsm.can_transition(IncidentState.INVESTIGATING))
        fsm.transition(IncidentState.INVESTIGATING)
        self.assertEqual(fsm.current_state, IncidentState.INVESTIGATING)

        # INVESTIGATING -> HYPOTHESIS_FORMED
        self.assertTrue(fsm.can_transition(IncidentState.HYPOTHESIS_FORMED))
        fsm.transition(IncidentState.HYPOTHESIS_FORMED)
        self.assertEqual(fsm.current_state, IncidentState.HYPOTHESIS_FORMED)

        # HYPOTHESIS_FORMED -> CONSENSUS_REACHED
        self.assertTrue(fsm.can_transition(IncidentState.CONSENSUS_REACHED))
        fsm.transition(IncidentState.CONSENSUS_REACHED)
        self.assertEqual(fsm.current_state, IncidentState.CONSENSUS_REACHED)

        # CONSENSUS_REACHED -> SANDBOX_SIMULATED
        self.assertTrue(fsm.can_transition(IncidentState.SANDBOX_SIMULATED))
        fsm.transition(IncidentState.SANDBOX_SIMULATED)
        self.assertEqual(fsm.current_state, IncidentState.SANDBOX_SIMULATED)

        # SANDBOX_SIMULATED -> REMEDIATING
        self.assertTrue(fsm.can_transition(IncidentState.REMEDIATING))
        fsm.transition(IncidentState.REMEDIATING)
        self.assertEqual(fsm.current_state, IncidentState.REMEDIATING)

        # REMEDIATING -> RESOLVED
        self.assertTrue(fsm.can_transition(IncidentState.RESOLVED))
        fsm.transition(IncidentState.RESOLVED)
        self.assertEqual(fsm.current_state, IncidentState.RESOLVED)
        self.assertTrue(fsm.is_terminal())

    def test_fsm_shortcut_bypass_transition(self):
        # In O(1) Shortcut Net, repeat alerts triage and bypass multi-hop RCA directly to RESOLVED
        fsm = IncidentLifecycleFSM("inc_shortcut_01", IncidentState.DETECTED)
        fsm.transition(IncidentState.TRIAGED)
        self.assertTrue(fsm.can_transition(IncidentState.RESOLVED))
        fsm.transition(IncidentState.RESOLVED)
        self.assertEqual(fsm.current_state, IncidentState.RESOLVED)
        self.assertTrue(fsm.is_terminal())

    def test_fsm_invalid_transition_rejected(self):
        fsm = IncidentLifecycleFSM("inc_invalid_01", IncidentState.DETECTED)

        # DETECTED cannot jump directly to REMEDIATING
        self.assertFalse(fsm.can_transition(IncidentState.REMEDIATING))
        with self.assertRaises(ValueError):
            fsm.transition(IncidentState.REMEDIATING)

    def test_fsm_terminal_state_rejection(self):
        fsm = IncidentLifecycleFSM("inc_term_01", IncidentState.RESOLVED)
        self.assertTrue(fsm.is_terminal())
        self.assertFalse(fsm.can_transition(IncidentState.DETECTED))
        with self.assertRaises(ValueError):
            fsm.transition(IncidentState.DETECTED)


if __name__ == "__main__":
    unittest.main()
