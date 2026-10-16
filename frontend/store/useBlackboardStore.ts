import { create } from 'zustand';

export interface AgentThought {
  agent: 'Triage' | 'RCA' | 'Memory' | 'Remediation';
  text: string;
  timestamp: number;
  cypher_query?: string;
  confidence?: number;
}

export interface BlackboardState {
  incidentId: string;
  lifecycleState: string;
  severity: string;
  blastRadius: number;
  wcs: number;
  agentThoughts: AgentThought[];
  elements: any[];
  selectedNode: any | null;
  wsConnected: boolean;

  // Actions
  setIncidentId: (id: string) => void;
  setWsConnected: (connected: boolean) => void;
  setSelectedNode: (node: any | null) => void;
  addAgentThought: (thought: AgentThought) => void;
  updateConsensus: (wcs: number) => void;
  updateLifecycleState: (state: string) => void;
  reconcileGraphMutation: (delta: { nodes_added?: any[]; edges_added?: any[] }) => void;
  initializeWebSocket: (incidentId: string) => () => void;
}

export const useBlackboardStore = create<BlackboardState>((set, get) => ({
  incidentId: "inc_98a12c",
  lifecycleState: "INVESTIGATING",
  severity: "SEV_1",
  blastRadius: 3,
  wcs: 0.88,
  wsConnected: false,
  agentThoughts: [
    {
      agent: "Triage",
      text: "Ingested 420 cascading HTTP 504 alerts. Clustered via CDLP to community_01. 3-hop blast radius calculated: 3 upstream services (Cart, Checkout, FrontendAPI). Assigned SEV_1.",
      timestamp: Date.now() - 45000,
      confidence: 0.95
    },
    {
      agent: "RCA",
      text: "Traversed cross-layer call graph: PaymentService -> /charge -> call_stripe_webhook(). Tree-sitter AST linked to commit c3d9a107 (Alice Chen) which removed socket timeout.",
      timestamp: Date.now() - 30000,
      confidence: 0.97
    },
    {
      agent: "Memory",
      text: "HNSW 384-dim vector search retrieved past incident postmortem_inc_historical_01 (similarity 0.941). SOP Runbook RB-NET-042 loaded. Composite Confidence C_SRE: 0.88.",
      timestamp: Date.now() - 15000,
      confidence: 0.88
    }
  ],
  elements: [
    // Core Seed Microservice Nodes
    { data: { id: "svc_frontend", label: "FrontendAPI", type: "Service", status: "HEALTHY" } },
    { data: { id: "svc_checkout", label: "CheckoutService", type: "Service", status: "HEALTHY" } },
    { data: { id: "svc_payment", label: "PaymentService", type: "Service", status: "CRITICAL" } },
    { data: { id: "alt_p99", label: "Alert: P99 > 2000ms", type: "Alert", status: "CRITICAL" } },
    { data: { id: "ep_charge", label: "/charge", type: "Endpoint" } },
    { data: { id: "fn_stripe", label: "call_stripe_webhook", type: "Function", file_path: "payment/gateway.py", line_start: 42 } },
    { data: { id: "commit_c3d9", label: "c3d9a107 (Alice Chen)", type: "Commit", author: "Alice Chen", sha: "c3d9a107" } },

    // Edges
    { data: { id: "svc_frontend_CALLS_svc_checkout", source: "svc_frontend", target: "svc_checkout", label: "CALLS" } },
    { data: { id: "svc_checkout_DEPENDS_ON_svc_payment", source: "svc_checkout", target: "svc_payment", label: "DEPENDS_ON" } },
    { data: { id: "alt_p99_AFFECTS_svc_payment", source: "alt_p99", target: "svc_payment", label: "AFFECTS" } },
    { data: { id: "svc_payment_EXPOSES_ep_charge", source: "svc_payment", target: "ep_charge", label: "EXPOSES" } },
    { data: { id: "ep_charge_IMPLEMENTED_BY_fn_stripe", source: "ep_charge", target: "fn_stripe", label: "IMPLEMENTED_BY", is_causal_path: "true" } },
    { data: { id: "fn_stripe_MODIFIED_BY_commit_c3d9", source: "fn_stripe", target: "commit_c3d9", label: "MODIFIED_BY", is_causal_path: "true" } },
    { data: { id: "alt_p99_SHORTCUT_fn_stripe", source: "alt_p99", target: "fn_stripe", label: "CAUSED_BY_SHORTCUT", type: "CAUSED_BY_SHORTCUT" } }
  ],
  selectedNode: null,

  setIncidentId: (id) => set({ incidentId: id }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  addAgentThought: (thought) => set((s) => ({ agentThoughts: [thought, ...s.agentThoughts] })),
  updateConsensus: (wcs) => set({ wcs }),
  updateLifecycleState: (state) => set({ lifecycleState: state }),

  reconcileGraphMutation: (delta) => set((state) => {
    const updatedElements = [...state.elements];
    if (delta.nodes_added) {
      for (const node of delta.nodes_added) {
        if (!updatedElements.some(e => e.data && e.data.id === node.id)) {
          updatedElements.push({ data: { id: node.id, label: node.label, ...node.properties } });
        }
      }
    }
    if (delta.edges_added) {
      for (const edge of delta.edges_added) {
        const edgeId = edge.id || `${edge.source}_${edge.label}_${edge.target}`;
        if (!updatedElements.some(e => e.data && (e.data.id === edgeId || (e.data.source === edge.source && e.data.target === edge.target && e.data.label === edge.label)))) {
          updatedElements.push({
            data: {
              id: edgeId,
              source: edge.source,
              target: edge.target,
              label: edge.label,
              ...edge.properties
            }
          });
        }
      }
    }
    return { elements: updatedElements };
  }),

  initializeWebSocket: (incidentId: string) => {
    if (typeof window === 'undefined') return () => {};
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/blackboard/${incidentId}`;
    let ws: WebSocket;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        get().setWsConnected(true);
        ws.send(JSON.stringify({ type: 'SUBSCRIBE', incident_id: incidentId }));
      };
      ws.onclose = () => get().setWsConnected(false);
      ws.onerror = (e) => {
        // Clean WebSocket error suppression in local dev mock mode
        console.warn("WebSocket error (mock/offline mode):", e);
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'AGENT_THOUGHT') {
            get().addAgentThought({
              agent: msg.agent,
              text: msg.text,
              timestamp: msg.timestamp || Date.now(),
              cypher_query: msg.cypher_query,
              confidence: msg.confidence
            });
          } else if (msg.type === 'CONSENSUS_VOTE') {
            get().updateConsensus(msg.wcs);
          } else if (msg.type === 'STATE_CHANGE') {
            get().updateLifecycleState(msg.to);
          } else if (msg.type === 'GRAPH_MUTATION' && msg.delta) {
            get().reconcileGraphMutation(msg.delta);
          }
        } catch (e) {
          console.error("Failed to parse incoming WS frame:", e);
        }
      };
    } catch (e) {
      console.warn("WebSocket connection skipped in development mock mode:", e);
    }

    return () => {
      if (ws) ws.close();
    };
  }
}));
