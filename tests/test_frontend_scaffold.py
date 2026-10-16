import os
import json
try:
    import pytest
except ImportError:
    class _PytestMock:
        pass
    pytest = _PytestMock()

def test_frontend_package_json_configuration():
    """Verify package.json specifies Next 14, Cytoscape, Zustand, and layout extensions."""
    pkg_path = os.path.join("frontend", "package.json")
    assert os.path.exists(pkg_path), "frontend/package.json must exist"
    
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
        
    assert pkg.get("name") == "graphsre-frontend"
    deps = pkg.get("dependencies", {})
    assert "next" in deps, "next must be in dependencies"
    assert "cytoscape" in deps, "cytoscape must be in dependencies"
    assert "cytoscape-cose-bilkent" in deps, "cytoscape-cose-bilkent must be in dependencies"
    assert "cytoscape-dagre" in deps, "cytoscape-dagre must be in dependencies"
    assert "zustand" in deps, "zustand must be in dependencies"
    assert "lucide-react" in deps, "lucide-react must be in dependencies"

def test_frontend_app_router_routes_exist():
    """Verify all Next.js 14 App Router pages and config files are created."""
    required_files = [
        os.path.join("frontend", "tsconfig.json"),
        os.path.join("frontend", "tailwind.config.js"),
        os.path.join("frontend", "postcss.config.js"),
        os.path.join("frontend", "next.config.js"),
        os.path.join("frontend", "app", "globals.css"),
        os.path.join("frontend", "app", "layout.tsx"),
        os.path.join("frontend", "app", "page.tsx"),
        os.path.join("frontend", "app", "postmortems", "page.tsx"),
        os.path.join("frontend", "app", "cicd-blast-gate", "page.tsx")
    ]
    for file_path in required_files:
        assert os.path.exists(file_path), f"Required file missing: {file_path}"

def test_layout_contains_falkordb_header_and_navigation():
    """Verify layout.tsx renders branding, FalkorDB status badge, and navigation routes."""
    layout_path = os.path.join("frontend", "app", "layout.tsx")
    assert os.path.exists(layout_path), f"frontend/app/layout.tsx must exist"
    with open(layout_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "GraphSRE" in content
    assert "FalkorDB Central Blackboard" in content
    assert "War Room" in content
    assert "/postmortems" in content
    assert "/cicd-blast-gate" in content

if __name__ == "__main__":
    print("Running frontend scaffold tests...")
    test_frontend_package_json_configuration()
    test_frontend_app_router_routes_exist()
    test_layout_contains_falkordb_header_and_navigation()
    print("All frontend scaffold tests passed successfully!")
