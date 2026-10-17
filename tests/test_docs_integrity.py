import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def test_production_documentation_files_exist():
    """Verify all core documentation and submission files exist."""
    required = [
        os.path.join(REPO_ROOT, "README.md"),
        os.path.join(REPO_ROOT, "docs", "DEMO_SCRIPT.md"),
        os.path.join(REPO_ROOT, "docs", "TRACK_MAPPING.md")
    ]
    for r in required:
        assert os.path.exists(r), f"Missing documentation file: {r}"


def test_readme_contains_zero_build_quickstart_and_track_details():
    """Verify README.md contains zero local build commands with Docker Hub user sid7899999."""
    readme_path = os.path.join(REPO_ROOT, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "sid7899999/graphsre-backend:latest" in content, "README must reference backend Docker image"
    assert "sid7899999/graphsre-frontend:latest" in content, "README must reference frontend Docker image"
    assert "docker compose pull" in content, "README must show docker compose pull quickstart"
    assert "FalkorDB" in content, "README must highlight FalkorDB"
    assert "Cytoscape" in content, "README must highlight Cytoscape"
    assert "Track 1" in content, "README must detail Track 1"
    assert "Track 2" in content, "README must detail Track 2"
    assert "Track 3" in content, "README must detail Track 3"


def test_demo_script_contains_timestamped_acts():
    """Verify DEMO_SCRIPT.md outlines the 3-minute video presentation."""
    script_path = os.path.join(REPO_ROOT, "docs", "DEMO_SCRIPT.md")
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()
    assert "Act 1" in script, "DEMO_SCRIPT must outline Act 1"
    assert "Act 2" in script, "DEMO_SCRIPT must outline Act 2"
    assert "Act 3" in script, "DEMO_SCRIPT must outline Act 3"
    assert "Act 4" in script, "DEMO_SCRIPT must outline Act 4"
    assert ("00:00" in script or "0:00" in script), "DEMO_SCRIPT must include start timestamps"
    assert "GRAPH.COPY" in script, "DEMO_SCRIPT must highlight FalkorDB GRAPH.COPY"


if __name__ == "__main__":
    tests = [
        test_production_documentation_files_exist,
        test_readme_contains_zero_build_quickstart_and_track_details,
        test_demo_script_contains_timestamped_acts,
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
