import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def test_action_and_chaos_components_exist():
    """Verify QuorumMeter, ChaosPanel, ActionCard, and ShortcutVisualizer exist and export functions."""
    required = [
        os.path.join(REPO_ROOT, "frontend", "components", "QuorumMeter.tsx"),
        os.path.join(REPO_ROOT, "frontend", "components", "ChaosPanel.tsx"),
        os.path.join(REPO_ROOT, "frontend", "components", "ActionCard.tsx"),
        os.path.join(REPO_ROOT, "frontend", "components", "ShortcutVisualizer.tsx")
    ]
    for r in required:
        assert os.path.exists(r), f"Missing component: {r}"


def test_chaos_panel_defines_all_four_scenarios():
    """Verify ChaosPanel supports socket_timeout, connection_exhaustion, memory_leak, and grpc_partition."""
    chaos_path = os.path.join(REPO_ROOT, "frontend", "components", "ChaosPanel.tsx")
    with open(chaos_path, "r", encoding="utf-8") as f:
        src = f.read()
    assert "socket_timeout" in src, "Must support socket_timeout scenario"
    assert "connection_exhaustion" in src, "Must support connection_exhaustion scenario"
    assert "memory_leak" in src, "Must support memory_leak scenario"
    assert "grpc_partition" in src, "Must support grpc_partition scenario"
    assert "/api/chaos/inject" in src, "Must post to /api/chaos/inject"


def test_war_room_page_integrates_all_components():
    """Verify page.tsx mounts TopologyCanvas, AgentFeed, QuorumMeter, ActionCard, and ChaosPanel."""
    page_path = os.path.join(REPO_ROOT, "frontend", "app", "page.tsx")
    with open(page_path, "r", encoding="utf-8") as f:
        src = f.read()
    assert "TopologyCanvas" in src, "Must mount TopologyCanvas"
    assert "AgentFeed" in src, "Must mount AgentFeed"
    assert "QuorumMeter" in src, "Must mount QuorumMeter"
    assert "ActionCard" in src, "Must mount ActionCard"
    assert "ChaosPanel" in src, "Must mount ChaosPanel"


if __name__ == "__main__":
    tests = [
        test_action_and_chaos_components_exist,
        test_chaos_panel_defines_all_four_scenarios,
        test_war_room_page_integrates_all_components,
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
