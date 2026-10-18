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
  triggerChaosScenario: (scenario: string, targetService?: string) => void;
  revealCausalTracer: () => void;
  applyCanaryResolution: () => void;
  triggerShortcutBypass: () => void;
  initializeWebSocket: (incidentId: string) => () => void;
}

export const useBlackboardStore = create<BlackboardState>((set, get) => ({
  incidentId: "inc_active_01",
  lifecycleState: "HEALTHY_MONITORING",
  severity: "NORMAL",
  blastRadius: 0,
  wcs: 0.0,
  wsConnected: false,
  agentThoughts: [
    {
      agent: "Triage",
      text: "FalkorDB Central Blackboard active. Monitoring 5 microservices across 3 tiers with GraphBLAS sparse reachability engine.",
      timestamp: Date.now(),
      confidence: 1.0
    }
  ],
  elements: [
    // Healthy Seed Microservice Nodes (No Alert, No Culprit, No Shortcut)
    { data: { id: "svc_frontend", label: "FrontendAPI", type: "Service", status: "HEALTHY" } },
    { data: { id: "svc_checkout", label: "CheckoutService", type: "Service", status: "HEALTHY" } },
    { data: { id: "svc_payment", label: "PaymentService", type: "Service", status: "HEALTHY" } },
    { data: { id: "svc_inventory", label: "InventoryService", type: "Service", status: "HEALTHY" } },
    { data: { id: "svc_auth", label: "AuthService", type: "Service", status: "HEALTHY" } },

    // Core Topology Dependency Edges
    { data: { id: "svc_frontend_CALLS_svc_checkout", source: "svc_frontend", target: "svc_checkout", label: "CALLS" } },
    { data: { id: "svc_frontend_CALLS_svc_auth", source: "svc_frontend", target: "svc_auth", label: "CALLS" } },
    { data: { id: "svc_checkout_DEPENDS_ON_svc_payment", source: "svc_checkout", target: "svc_payment", label: "DEPENDS_ON" } },
    { data: { id: "svc_checkout_DEPENDS_ON_svc_inventory", source: "svc_checkout", target: "svc_inventory", label: "DEPENDS_ON" } },
    { data: { id: "svc_payment_DEPENDS_ON_svc_auth", source: "svc_payment", target: "svc_auth", label: "DEPENDS_ON" } }
  ],
  selectedNode: null,

  setIncidentId: (id) => set({ incidentId: id }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  addAgentThought: (thought) => set((s) => ({ agentThoughts: [thought, ...s.agentThoughts].slice(0, 100) })),
  updateConsensus: (wcs) => set({ wcs }),
  updateLifecycleState: (state) => set({ lifecycleState: state }),

  triggerChaosScenario: (scenario: string, targetService?: string) => {
    set((state) => {
      const updatedElements = state.elements.map((el) => {
        if (el.data && (el.data.id === "svc_payment" || el.data.label === (targetService || "PaymentService"))) {
          return { ...el, data: { ...el.data, status: "CRITICAL" } };
        }
        return el;
      });

      if (!updatedElements.some((e) => e.data && e.data.id === "alt_p99")) {
        updatedElements.push({
          data: { id: "alt_p99", label: "Alert: HTTP 504 Storm", type: "Alert", status: "CRITICAL" }
        });
      }

      if (!updatedElements.some((e) => e.data && e.data.id === "alt_p99_AFFECTS_svc_payment")) {
        updatedElements.push({
          data: { id: "alt_p99_AFFECTS_svc_payment", source: "alt_p99", target: "svc_payment", label: "AFFECTS" }
        });
      }

      const triageThought: AgentThought = {
        agent: "Triage",
        text: "Ingested 420 cascading HTTP 504 alerts. Clustered via CDLP to community_01. 3-hop blast radius calculated: 3 upstream services (Cart, Checkout, FrontendAPI). Assigned SEV_1.",
        timestamp: Date.now(),
        confidence: 0.95
      };

      return {
        elements: updatedElements,
        severity: "SEV_1",
        blastRadius: 3,
        lifecycleState: "DETECTED",
        agentThoughts: [triageThought, ...state.agentThoughts].slice(0, 100)
      };
    });
  },

  revealCausalTracer: () => {
    set((state) => {
      const updatedElements = [...state.elements];

      const nodesToAdd = [
        { id: "ep_charge", label: "/charge", type: "Endpoint" },
        { id: "fn_stripe", label: "call_stripe_webhook", type: "Function", file_path: "payment/gateway.py", line_start: 42 },
        { id: "commit_c3d9", label: "c3d9a107 (Alice Chen)", type: "Commit", author: "Alice Chen", sha: "c3d9a107" }
      ];

      for (const node of nodesToAdd) {
        if (!updatedElements.some((e) => e.data && e.data.id === node.id)) {
          updatedElements.push({ data: node });
        }
      }

      const edgesToAdd = [
        { id: "svc_payment_EXPOSES_ep_charge", source: "svc_payment", target: "ep_charge", label: "EXPOSES" },
        { id: "ep_charge_IMPLEMENTED_BY_fn_stripe", source: "ep_charge", target: "fn_stripe", label: "IMPLEMENTED_BY", is_causal_path: "true" },
        { id: "fn_stripe_MODIFIED_BY_commit_c3d9", source: "fn_stripe", target: "commit_c3d9", label: "MODIFIED_BY", is_causal_path: "true" }
      ];

      for (const edge of edgesToAdd) {
        if (!updatedElements.some((e) => e.data && e.data.id === edge.id)) {
          updatedElements.push({ data: edge });
        }
      }

      const rcaThought: AgentThought = {
        agent: "RCA",
        text: "Traversed cross-layer call graph: PaymentService -> /charge -> call_stripe_webhook(). Tree-sitter AST linked to commit c3d9a107 (Alice Chen) which removed socket timeout.",
        timestamp: Date.now() - 1000,
        confidence: 0.97
      };

      const memoryThought: AgentThought = {
        agent: "Memory",
        text: "HNSW 384-dim vector search retrieved past incident postmortem_inc_historical_01 (similarity 0.941). Quorum Consensus reached: WCS 0.88 >= 0.75.",
        timestamp: Date.now(),
        confidence: 0.88
      };

      return {
        elements: updatedElements,
        lifecycleState: "HYPOTHESIS_FORMED",
        wcs: 0.88,
        agentThoughts: [memoryThought, rcaThought, ...state.agentThoughts].slice(0, 100)
      };
    });
  },

  applyCanaryResolution: () => {
    set((state) => {
      const updatedElements = state.elements.map((el) => {
        if (el.data && el.data.id === "svc_payment") {
          return { ...el, data: { ...el.data, status: "HEALTHY" } };
        }
        return el;
      });

      const shortcutEdge = {
        id: "alt_p99_SHORTCUT_fn_stripe",
        source: "alt_p99",
        target: "fn_stripe",
        label: "CAUSED_BY_SHORTCUT",
        type: "CAUSED_BY_SHORTCUT"
      };

      if (!updatedElements.some((e) => e.data && e.data.id === shortcutEdge.id)) {
        updatedElements.push({ data: shortcutEdge });
      }

      const remediationThought: AgentThought = {
        agent: "Remediation",
        text: "Canary rollback verified in GRAPH.COPY ephemeral sandbox. Incident resolved in 78s. Synthesized emerald O(1) shortcut edge.",
        timestamp: Date.now(),
        confidence: 0.99
      };

      return {
        elements: updatedElements,
        lifecycleState: "RESOLVED_SHORTCUT_COMPILED",
        severity: "NORMAL",
        agentThoughts: [remediationThought, ...state.agentThoughts].slice(0, 100)
      };
    });
  },

  triggerShortcutBypass: () => {
    set((state) => {
      const shortcutThought: AgentThought = {
        agent: "Remediation",
        text: "⚡ Repeat fault detected! O(1) Shortcut Net hit: directly bypassed multi-hop RCA to call_stripe_webhook. Resolved in 0.18s!",
        timestamp: Date.now(),
        confidence: 1.0
      };

      return {
        lifecycleState: "RESOLVED_VIA_SHORTCUT",
        agentThoughts: [shortcutThought, ...state.agentThoughts].slice(0, 100)
      };
    });
  },

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
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${window.location.hostname}:8000/ws/blackboard/${incidentId}`;
    let ws: WebSocket;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        get().setWsConnected(true);
        ws.send(JSON.stringify({ type: 'SUBSCRIBE', incident_id: incidentId }));
      };
      ws.onclose = () => get().setWsConnected(false);
      ws.onerror = (e) => {
        console.warn("WebSocket error (mock/offline mode):", e);
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'AGENT_THOUGHT') {
            const rawAgent = (msg.agent || 'Remediation').replace(/_Agent$/i, '');
            get().addAgentThought({
              agent: rawAgent as AgentThought['agent'],
              text: msg.text || msg.thought || '',
              timestamp: msg.timestamp || Date.now(),
              cypher_query: msg.cypher_query,
              confidence: msg.confidence ?? msg.score
            });
          } else if (msg.type === 'CONSENSUS_VOTE') {
            get().updateConsensus(msg.wcs ?? msg.score ?? 0);
          } else if (msg.type === 'STATE_CHANGE') {
            get().updateLifecycleState(msg.to || msg.state);
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
