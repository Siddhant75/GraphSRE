import os

try:
    import pytest
except ImportError:
    class _PytestMock:
        pass
    pytest = _PytestMock()

def test_cytoscape_styles_contains_required_selectors():
    """Verify cytoscape stylesheet contains definitions for healthy services, degraded alerts, AST functions, culprit commits, glowing causal paths, and emerald shortcuts."""
    styles_path = os.path.join("frontend", "styles", "cytoscapeStyles.ts")
    assert os.path.exists(styles_path), "frontend/styles/cytoscapeStyles.ts must exist"
    
    with open(styles_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check node styling selectors
    assert "node[type = \"Service\"]" in content
    assert "node[status = \"CRITICAL\"]" in content or "node[status = \"DEGRADED\"]" in content
    assert "node[type = \"Function\"]" in content
    assert "node[type = \"Commit\"]" in content
    
    # Check edge styling selectors
    assert "edge[is_causal_path = \"true\"]" in content or "is_causal_path" in content
    assert "edge[type = \"CAUSED_BY_SHORTCUT\"]" in content or "CAUSED_BY_SHORTCUT" in content
    
    # Check exact color codes from prd.md / spec.md
    assert "#EF4444" in content # Crimson red for critical/alert
    assert "#3B82F6" in content # Blue for Service border
    assert "#8B5CF6" in content # Purple for Function node
    assert "#F59E0B" in content # Yellow-gold for suspect commit / glowing causal path
    assert "#10B981" in content # Emerald for O(1) shortcut edge

def test_topology_canvas_and_node_inspector_exist():
    """Verify TopologyCanvas and NodeInspector components are implemented."""
    canvas_path = os.path.join("frontend", "components", "TopologyCanvas.tsx")
    inspector_path = os.path.join("frontend", "components", "NodeInspector.tsx")
    
    assert os.path.exists(canvas_path), "TopologyCanvas.tsx must exist"
    assert os.path.exists(inspector_path), "NodeInspector.tsx must exist"
    
    with open(canvas_path, "r", encoding="utf-8") as f:
        canvas_src = f.read()
    assert "cytoscape" in canvas_src
    assert "cose-bilkent" in canvas_src or "dagre" in canvas_src
    assert "TopologyCanvas" in canvas_src

if __name__ == "__main__":
    print("Running Cytoscape canvas tests...")
    test_cytoscape_styles_contains_required_selectors()
    test_topology_canvas_and_node_inspector_exist()
    print("All Cytoscape canvas tests passed successfully!")
