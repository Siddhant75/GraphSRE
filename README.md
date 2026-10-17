# GraphSRE: Autonomous SRE & Code Brain

> **FalkorDB + WeMakeDevs GraphHacks Hackathon (2026) Submission**  
> Powered by **FalkorDB** (GraphBLAS Linear Algebra, ACID Central Blackboard, Embedded HNSW Vector Memory & `GRAPH.COPY` Zero-Cost Sandboxing)

```
   ┌─────────────────────────────────────────────────────────────────────────────────┐
   │                       GRAPHSRE MULTI-AGENT ARCHITECTURE                         │
   │               Autonomous Site Reliability Engineering & Code Intelligence        │
   └─────────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
     │ Triage Agent │      │  RCA Agent   │      │ Memory Agent │      │ Remediation  │
     │   (Alerts)   │      │  (Causality) │      │ (Knowledge)  │      │   (Action)   │
     └──────┬───────┘      └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
            │                     │                     │                     │
            │   Model Context Protocol (FastMCP) Tools  │                     │
            └──────────────┬──────┴──────────────┬──────┴─────────────────────┘
                           │                     │
                           ▼                     ▼
     ┌────────────────────────────────────────────────────────────────────────────────┐
     │                       FALKORDB CENTRAL BLACKBOARD                              │
     │                                                                                │
     │   ACID Graph State Store  •  Vector Index  •  AST & Topology Knowledge Base   │
     │                                                                                │
     │   (:Incident) ──[:HAS_ALERT]──> (:Alert) ──[:AFFECTS]──> (:Service)           │
     │        │                                                     │                 │
     │   [:HAS_HYPOTHESIS]                                     [:CALLS]               │
     │        ▼                                                     ▼                 │
     │   (:Hypothesis) ──[:SUPPORTED_BY]──> (:Evidence) ──> (:Function)              │
     │        │                                                     ▲                 │
     │   [:LEADS_TO]                                           [:MODIFIES]            │
     │        ▼                                                     │                 │
     │   (:RemediationPlan) ──[:TESTED_IN]──> (:SandboxGraph) ── (:Commit)            │
     └────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Zero Local Build Quickstart for Hackathon Judges

To ensure developers and judges with strictly limited disk space experience zero local compilation overhead, **all container images are pre-built via GitHub Actions cloud CI/CD and hosted on Docker Hub**:

- `sid7899999/graphsre-backend:latest`
- `sid7899999/graphsre-frontend:latest`
- `falkordb/falkordb:latest`

### 1-Click Launch:
```bash
# 1. Clone the repository
git clone https://github.com/your-username/GraphHacks-hackathon.git
cd GraphHacks-hackathon

# 2. Pull pre-built images from Docker Hub (0 local build disk space!)
docker compose pull

# 3. Start the entire platform
docker compose up -d

# 4. Seed FalkorDB with mock topology, AST call trees & vector memory
docker compose exec backend python scripts/seed_mock_topology.py
# (Or locally: python scripts/seed_mock_topology.py)
```

### Access URLs:
- **Next.js 14 War Room UI (Cytoscape.js Interactive Graph Canvas):** `http://localhost:3000`
- **FastAPI OpenAPI Documentation:** `http://localhost:8000/docs`
- **FastMCP Agent Tool Server:** `http://localhost:8001` or `python server/mcp_server.py`

---

## 🛠️ Bare-Metal Local Development (Minimal Disk Footprint)

```bash
# 1. Launch lightweight FalkorDB container
docker run -d -p 6379:6379 --name falkordb falkordb/falkordb:latest

# 2. Setup Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Seed knowledge graph
python scripts/seed_mock_topology.py

# 4. Start backend & frontend
uvicorn backend.main:app --reload --port 8000 &
cd frontend && npm install && npm run dev
```

---

## 🏆 Hackathon Track Alignment

| Track | Core GraphSRE Capability | FalkorDB Feature |
| :--- | :--- | :--- |
| **Track 1: Connected Data** | Multi-hop cross-layer traversal from HTTP alerts to Tree-sitter AST & Git commits via 7 FastMCP tools. | GraphBLAS Sparse Matrix Engine |
| **Track 2: Memory & Coordination** | Central ACID blackboard replacing conversational token storms, 384-dim HNSW vector memory & quorum consensus. | Sub-millisecond Cypher Transactions & `GRAPH.COPY` |
| **Track 3: Company Brain** | Socio-technical ownership linking AST functions to git authors; Shift-Left CI/CD blast gate; $O(1)$ shortcut nets. | Dynamic Edge Synthesis with Bayesian Decay |
| **Side Prize: Technical Blog** | Publication-grade analysis of Vector RAG failure modes in SRE in `blog.md`. | Complete Platform Architecture |

---

## 🧪 Verification & Testing

```bash
# Run complete test suite (E2E lifecycle, mathematical invariants, scaffolding)
pytest -v

# Run standalone end-to-end incident lifecycle test (< 90s MTTR SLA)
python tests/test_e2e_lifecycle.py

# Run mathematical graph invariants test (anti-hallucination, bayesian decay, veto)
python tests/test_graph_invariants.py

# Run interactive CLI demonstration
python scripts/run_demo_simulation.py
```
