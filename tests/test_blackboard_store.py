import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def test_blackboard_zustand_store_file_exists_and_exports():
    """Verify Zustand store defines state shape for blackboard entities and WebSocket delta handling."""
    store_path = os.path.join(REPO_ROOT, "frontend", "store", "useBlackboardStore.ts")
    assert os.path.exists(store_path), "frontend/store/useBlackboardStore.ts must exist"

    with open(store_path, "r", encoding="utf-8") as f:
        src = f.read()

    assert "useBlackboardStore" in src, "Must export useBlackboardStore"
    assert "GRAPH_MUTATION" in src or "delta" in src, "Must handle graph mutations / delta"
    assert "AGENT_THOUGHT" in src or "agentThoughts" in src, "Must handle agent thoughts"
    assert "CONSENSUS_VOTE" in src or "wcs" in src, "Must handle consensus votes / wcs"
    assert "elements" in src, "Must maintain Cytoscape elements"
    assert "reconcileGraphMutation" in src, "Must provide reconcileGraphMutation"
    assert "initializeWebSocket" in src, "Must provide initializeWebSocket"


def test_agent_feed_and_thought_card_exist():
    """Verify AgentFeed and AgentThoughtCard components are implemented and wire to the Zustand store."""
    feed_path = os.path.join(REPO_ROOT, "frontend", "components", "AgentFeed.tsx")
    card_path = os.path.join(REPO_ROOT, "frontend", "components", "AgentThoughtCard.tsx")

    assert os.path.exists(feed_path), "AgentFeed.tsx must exist"
    assert os.path.exists(card_path), "AgentThoughtCard.tsx must exist"

    with open(feed_path, "r", encoding="utf-8") as f:
        feed_src = f.read()
    assert "AgentFeed" in feed_src, "Must define AgentFeed component"
    assert "useBlackboardStore" in feed_src, "AgentFeed must consume useBlackboardStore"
    assert "AgentThoughtCard" in feed_src, "AgentFeed must render AgentThoughtCard"

    with open(card_path, "r", encoding="utf-8") as f:
        card_src = f.read()
    assert "AgentThoughtCard" in card_src, "Must define AgentThoughtCard component"
    assert "Triage" in card_src and "RCA" in card_src and "Memory" in card_src and "Remediation" in card_src, (
        "AgentThoughtCard must style all 4 agent roles"
    )


if __name__ == "__main__":
    tests = [
        test_blackboard_zustand_store_file_exists_and_exports,
        test_agent_feed_and_thought_card_exist,
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
