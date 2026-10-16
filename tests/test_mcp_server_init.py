import os
import sys
import math

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    class _PytestMock:
        @staticmethod
        def approx(expected, tol=1e-4):
            class _Approx:
                def __init__(self, exp, t):
                    self.exp = exp
                    self.t = t

                def __eq__(self, actual):
                    return abs(self.exp - actual) <= self.t or math.isclose(
                        self.exp, actual, rel_tol=self.t, abs_tol=self.t
                    )

                def __repr__(self):
                    return f"approx({self.exp} ± {self.t})"

            return _Approx(expected, tol)

    pytest = _PytestMock()

from server.mcp_server import (
    calculate_c_sre,
    compute_sev_score,
    calculate_bayesian_reinforcement,
    calculate_continuous_decay,
    apply_code_modification_penalty,
    mcp,
    LAMBDA_DECAY,
)


def test_calculate_c_sre_anti_hallucination_bound():
    """
    Mathematical Proof Verification:
    When T_graph = 0 (no structural AST or network topological path),
    even with maximum episodic similarity (1.0), metric SNR (1.0), and playbook success (1.0):
    C_SRE = 0.25*(1.0) + 0.35*(0.0) + 0.25*(1.0) + 0.15*(1.0) = 0.65.
    Since 0.65 < 0.75 verification threshold, ungrounded hypotheses can NEVER verify autonomously.
    """
    s_episodic = 1.0
    t_graph = 0.0  # Disconnected / hallucinated causal path
    e_metric = 1.0
    h_success = 1.0

    score = calculate_c_sre(s_episodic, t_graph, e_metric, h_success)
    assert score == 0.65
    assert score < 0.75, "Security Invariant Violated: Ungrounded hypothesis breached verification threshold"


def test_calculate_c_sre_grounded_reaches_verification():
    """Verify that a topologically grounded hypothesis (T_graph = 1.0) with strong telemetry passes 0.75."""
    score = calculate_c_sre(s_episodic=0.90, t_graph=1.0, e_metric=0.85, h_success=0.80)
    # 0.25*0.90 + 0.35*1.0 + 0.25*0.85 + 0.15*0.80 = 0.225 + 0.35 + 0.2125 + 0.12 = 0.9075
    assert pytest.approx(score, 0.001) == 0.9075
    assert score >= 0.75


def test_compute_sev_score_tier1_pagerank():
    """Verify SevScore formula: 40*Tier + 35*PageRank + 25*NormalizedInDegree."""
    # Tier 1 (1.0), PageRank 0.90, InDegree 6 (capped at 1.0)
    # 40*1.0 + 35*0.90 + 25*1.0 = 40 + 31.5 + 25 = 96.5 -> SEV_1
    score = compute_sev_score(tier="TIER_1", pagerank=0.90, in_degree=6)
    assert pytest.approx(score, 0.01) == 96.5
    assert score >= 85.0


def test_compute_sev_score_tier3_low_centrality():
    """Verify SevScore for low-tier leaf service."""
    # Tier 3 (0.3), PageRank 0.10, InDegree 1 (1/5 = 0.2)
    # 40*0.3 + 35*0.10 + 25*0.2 = 12 + 3.5 + 5.0 = 20.5 -> SEV_4 (< 35)
    score = compute_sev_score(tier="TIER_3", pagerank=0.10, in_degree=1)
    assert pytest.approx(score, 0.01) == 20.5
    assert score < 35.0


def test_calculate_bayesian_reinforcement():
    """Verify discrete Bayesian reinforcement: W_new = W + 0.50 * (1 - W)."""
    initial_w = 0.60
    new_w = calculate_bayesian_reinforcement(initial_w, eta=0.50)
    assert pytest.approx(new_w, 0.001) == 0.80

    # Reinforce again from 0.80: 0.80 + 0.5*(0.20) = 0.90
    new_w2 = calculate_bayesian_reinforcement(new_w, eta=0.50)
    assert pytest.approx(new_w2, 0.001) == 0.90


def test_calculate_continuous_decay_half_life():
    """
    Verify continuous exponential decay formula: W(t) = W_last * e^(-lambda * delta_t).
    With lambda = ln(2) / (30 * 86400), elapsed time of 30 days must halve the weight.
    """
    initial_w = 1.0
    thirty_days_seconds = 30 * 86400
    decayed_w = calculate_continuous_decay(initial_w, delta_seconds=thirty_days_seconds)
    assert pytest.approx(decayed_w, 0.001) == 0.50


def test_apply_code_modification_penalty():
    """Verify 70% Bayesian penalty upon code modification (W * 0.30)."""
    w = 0.90
    penalized_w = apply_code_modification_penalty(w)
    assert pytest.approx(penalized_w, 0.001) == 0.27


def test_fastmcp_server_instance():
    """Verify FastMCP server instance initialization and metadata."""
    assert mcp.name == "GraphSRE-Blackboard-Engine"


if __name__ == "__main__":
    tests = [
        ("test_calculate_c_sre_anti_hallucination_bound", test_calculate_c_sre_anti_hallucination_bound),
        ("test_calculate_c_sre_grounded_reaches_verification", test_calculate_c_sre_grounded_reaches_verification),
        ("test_compute_sev_score_tier1_pagerank", test_compute_sev_score_tier1_pagerank),
        ("test_compute_sev_score_tier3_low_centrality", test_compute_sev_score_tier3_low_centrality),
        ("test_calculate_bayesian_reinforcement", test_calculate_bayesian_reinforcement),
        ("test_calculate_continuous_decay_half_life", test_calculate_continuous_decay_half_life),
        ("test_apply_code_modification_penalty", test_apply_code_modification_penalty),
        ("test_fastmcp_server_instance", test_fastmcp_server_instance),
    ]
    for name, test_fn in tests:
        print(f"Running {name}...")
        test_fn()
        print(f"PASS: {name}")
    print("\nAll 8 MCP server init tests passed successfully!")
