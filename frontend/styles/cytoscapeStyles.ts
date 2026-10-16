/**
 * Cytoscape.js Declarative Visual Stylesheet
 * Standardized across GraphSRE for Microservices, AST Call Trees, and Shortcut Nets
 */
export const cytoscapeStylesheet: any[] = [
  // Base Node Styling
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'font-family': 'JetBrains Mono, ui-monospace, monospace',
      'font-size': '11px',
      'color': '#F8FAFC',
      'text-valign': 'bottom',
      'text-margin-y': 6,
      'background-color': '#1E293B',
      'border-width': 2,
      'border-color': '#475569',
      'width': 44,
      'height': 44,
      'transition-property': 'background-color, border-color, width, height',
      'transition-duration': '0.3s'
    }
  },

  // Service Node (Healthy)
  {
    selector: 'node[type = "Service"]',
    style: {
      'shape': 'round-rectangle',
      'background-color': '#0F172A',
      'border-color': '#3B82F6',
      'border-width': 3,
      'width': 56,
      'height': 56
    }
  },

  // Degraded / Alerted Node (Pulsing Red)
  {
    selector: 'node[status = "CRITICAL"], node[status = "DEGRADED"]',
    style: {
      'background-color': '#450A0A',
      'border-color': '#EF4444',
      'border-width': 4
    }
  },

  // Telemetry Alert Node
  {
    selector: 'node[type = "Alert"]',
    style: {
      'shape': 'hexagon',
      'background-color': '#7F1D1D',
      'border-color': '#EF4444',
      'border-width': 3,
      'width': 48,
      'height': 48
    }
  },

  // API Endpoint Node
  {
    selector: 'node[type = "Endpoint"]',
    style: {
      'shape': 'tag',
      'background-color': '#172554',
      'border-color': '#60A5FA',
      'border-width': 2,
      'width': 40,
      'height': 40
    }
  },

  // AST Function Node
  {
    selector: 'node[type = "Function"]',
    style: {
      'shape': 'ellipse',
      'background-color': '#1E1B4B',
      'border-color': '#8B5CF6',
      'border-width': 2.5,
      'width': 36,
      'height': 36
    }
  },

  // Suspect Commit Culprit Node
  {
    selector: 'node[type = "Commit"]',
    style: {
      'shape': 'diamond',
      'background-color': '#78350F',
      'border-color': '#F59E0B',
      'border-width': 3,
      'width': 48,
      'height': 48
    }
  },

  // Base Edge Styling
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#334155',
      'target-arrow-color': '#334155',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'arrow-scale': 1.1
    }
  },

  // Active Causal Investigation Path (Glowing Yellow)
  {
    selector: 'edge[is_causal_path = "true"]',
    style: {
      'width': 4,
      'line-color': '#F59E0B',
      'target-arrow-color': '#F59E0B',
      'line-style': 'solid'
    }
  },

  // Self-Curating O(1) Shortcut Net Edge (Radiant Emerald)
  {
    selector: 'edge[type = "CAUSED_BY_SHORTCUT"]',
    style: {
      'width': 4,
      'line-color': '#10B981',
      'target-arrow-color': '#10B981',
      'line-style': 'dashed'
    }
  }
];
