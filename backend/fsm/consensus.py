"""
Multi-Agent Quorum Consensus Engine
File: backend/fsm/consensus.py
"""
from typing import Dict, List, Any


class QuorumConsensusEngine:
    """
    Evaluates Weighted Consensus Score:
    WCS(H) = sum(w_i * I(Vote_i = APPROVE))
    Weights: RCA=0.40, Memory=0.35, Triage=0.25
    Verification requires WCS >= 0.75 AND no veto from any agent with w_i >= 0.35.
    Explicit decision="VETO" also triggers an unconditional veto.
    """

    @staticmethod
    def evaluate_quorum(votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        wcs = 0.0
        has_veto = False
        veto_reasons: List[str] = []

        for v in votes:
            decision = str(v.get("decision", "")).strip().upper()
            raw_weight = v.get("weight")
            weight = float(raw_weight) if raw_weight is not None else 0.0
            reasoning = v.get("reasoning", "")
            agent_id = v.get("agent_id", "UnknownAgent")

            if decision == "APPROVE":
                wcs += weight
            elif decision == "REJECT":
                if weight >= 0.35:
                    has_veto = True
                    veto_reasons.append(f"High-weight agent {agent_id} rejected: {reasoning}")
            elif decision == "VETO":
                has_veto = True
                veto_reasons.append(f"Explicit veto cast by {agent_id}: {reasoning}")

        quorum_reached = (round(wcs, 4) >= 0.75) and not has_veto
        status = "HYPOTHESIS_VERIFIED" if quorum_reached else ("REJECTED_BY_VETO" if has_veto else "PENDING_CONSENSUS")

        return {
            "weighted_consensus_score": round(wcs, 3),
            "quorum_reached": quorum_reached,
            "has_veto": has_veto,
            "veto_reasons": veto_reasons,
            "status": status,
            "votes": votes
        }
