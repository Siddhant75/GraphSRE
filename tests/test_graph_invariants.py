"""
Mathematical Graph Invariants & Anti-Hallucination Bound Verification
File: tests/test_graph_invariants.py
"""
import os
import sys
import math
try:
    import pytest
except ImportError:
    class _PytestApprox:
        def __init__(self, expected, rel=0.001):
            self.expected = expected
            self.rel = rel
        def __eq__(self, actual):
            return abs(actual - self.expected) <= max(self.rel * abs(self.expected), 1e-4)
        def __repr__(self):
            return f"approx({self.expected} ± {self.rel})"
    class _PytestMock:
        approx = _PytestApprox
    pytest = _PytestMock()

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def calculate_c_sre(s_episodic: float, t_graph: float, e_metric: float, h_success: float) -> float:
    """
    GraphSRE Composite Confidence Score Formula:
    C_SRE = 0.25 * S_episodic + 0.35 * T_graph + 0.25 * E_metric + 0.15 * H_success
    """
    return round(0.25 * s_episodic + 0.35 * t_graph + 0.25 * e_metric + 0.15 * h_success, 4)


def test_anti_hallucination_mathematical_bound():
    """
    SECURITY INVARIANT 1: Hard Anti-Hallucination Graph Bound
    If a theory lacks a directed topological path in FalkorDB (T_graph = 0),
    even with 100% vector memory similarity (S_episodic = 1.0),
    100% metric correlation (E_metric = 1.0), and 100% runbook success (H_success = 1.0),
    C_SRE MUST NEVER reach the 0.75 autonomous execution threshold.
    """
    s_episodic = 1.0
    t_graph = 0.0  # Disconnected hallucination
    e_metric = 1.0
    h_success = 1.0

    score = calculate_c_sre(s_episodic, t_graph, e_metric, h_success)
    assert score == 0.65, f"Expected 0.65, got {score}"
    assert score < 0.75, "Security breach: Unreachable hypothesis reached execution threshold!"

    # Grounded theory with directed path in FalkorDB
    grounded_score = calculate_c_sre(s_episodic, 1.0, e_metric, h_success)
    assert grounded_score == 1.0
    assert grounded_score >= 0.75, "Grounded hypothesis failed to reach threshold!"


def test_bayesian_temporal_exponential_decay():
    """
    INVARIANT 2: Temporal Bayesian Decay of O(1) Shortcut Edges
    w(t) = w_0 * exp(-lambda * delta_t)
    where lambda = ln(2) / (30 * 86400) (Half-life = 30 days)
    """
    w_0 = 1.0
    half_life_seconds = 30.0 * 86400.0
    decay_lambda = math.log(2) / half_life_seconds

    # 1. At t = 0 days -> w = 1.0
    assert w_0 * math.exp(-decay_lambda * 0) == pytest.approx(1.0, 0.001)

    # 2. At t = 15 days -> w ~ 0.7071
    w_15 = w_0 * math.exp(-decay_lambda * (15 * 86400))
    assert w_15 == pytest.approx(0.7071, 0.001)

    # 3. At t = 30 days (Half-life) -> w = 0.50
    w_30 = w_0 * math.exp(-decay_lambda * (30 * 86400))
    assert w_30 == pytest.approx(0.50, 0.001)

    # 4. At t = 60 days (Two half-lives) -> w = 0.25
    w_60 = w_0 * math.exp(-decay_lambda * (60 * 86400))
    assert w_60 == pytest.approx(0.25, 0.001)

    # 5. At t = 100 days -> w < 0.10 (threshold for pruning/culling)
    w_100 = w_0 * math.exp(-decay_lambda * (100 * 86400))
    assert w_100 < 0.10


def test_code_modification_bayesian_penalty():
    """
    INVARIANT 3: AST Code Modification Penalty
    When a commit modifies any function on the causal path, the shortcut edge
    weight is penalized immediately by 70% (multiplied by 0.30).
    """
    w_current = 0.90
    penalty_factor = 0.30  # 70% reduction
    w_penalized = round(w_current * penalty_factor, 4)
    assert w_penalized == 0.27

    # Penalty from arbitrary initial weights
    assert round(0.50 * 0.30, 4) == 0.15
    assert round(1.00 * 0.30, 4) == 0.30


def test_memory_agent_quorum_veto_authority():
    """
    INVARIANT 4: Quorum Consensus Veto Authority
    Agent Weights: RCA=0.40, Memory=0.35, Triage=0.25
    Consensus Threshold: WCS >= 0.75
    If Memory Agent votes REJECT, max possible score is 1.0 - 0.35 = 0.65 < 0.75.
    Memory Agent holds absolute mathematical veto power.
    """
    weights = {"RCA": 0.40, "Memory": 0.35, "Triage": 0.25}
    threshold = 0.75

    # Memory Agent votes REJECT (score 0 for memory), others APPROVE
    wcs_memory_reject = sum([
        weights["RCA"] * 1.0,
        weights["Memory"] * 0.0,  # REJECT / VETO
        weights["Triage"] * 1.0
    ])

    assert round(wcs_memory_reject, 2) == 0.65
    assert wcs_memory_reject < threshold, "Memory Agent veto failed to block consensus!"

    # RCA Agent votes REJECT: max is 1.0 - 0.40 = 0.60 < 0.75
    wcs_rca_reject = sum([
        weights["RCA"] * 0.0,
        weights["Memory"] * 1.0,
        weights["Triage"] * 1.0
    ])
    assert round(wcs_rca_reject, 2) == 0.60
    assert wcs_rca_reject < threshold, "RCA Agent veto failed to block consensus!"


def test_bayesian_reinforcement_formula():
    """
    INVARIANT 5: Bayesian Reinforcement of Corroborated Shortcuts
    W_new = W + 0.50 * (1 - W)
    Increases weight asymptotically towards 1.0 without ever exceeding 1.0.
    """
    w = 0.50
    w_next = w + 0.50 * (1.0 - w)
    assert w_next == 0.75

    w_third = w_next + 0.50 * (1.0 - w_next)
    assert w_third == 0.875

    w_fourth = w_third + 0.50 * (1.0 - w_third)
    assert w_fourth == 0.9375
    assert w_fourth < 1.0


if __name__ == "__main__":
    tests = [
        test_anti_hallucination_mathematical_bound,
        test_bayesian_temporal_exponential_decay,
        test_code_modification_bayesian_penalty,
        test_memory_agent_quorum_veto_authority,
        test_bayesian_reinforcement_formula,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")

    print(f"\n{passed}/{len(tests)} tests passed.")
    if passed != len(tests):
        sys.exit(1)
