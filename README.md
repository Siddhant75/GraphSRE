# GraphSRE: Autonomous SRE & Code Brain

> **FalkorDB + WeMakeDevs GraphHacks Hackathon (2026) Submission**  
> Powered by **FalkorDB** (GraphBLAS Linear Algebra, ACID Central Blackboard, Embedded HNSW Vector Memory & `GRAPH.COPY` Zero-Cost Sandboxing)

---

## 🎬 Official 3-Minute Hackathon Demo Video
🎥 **Watch the Full Submission Video**: [`demo_video/graphsre_demo_submission.webm`](file:///d:/GraphHacks-hackathon/demo_video/graphsre_demo_submission.webm)
- **Act 1: Clean Baseline Monitoring** — FalkorDB Central Blackboard monitoring 5 microservices across 3 tiers with GraphBLAS sparse reachability engine.
- **Act 2: Chaos Injection & Autonomous Cross-Layer RCA** — HTTP 504 storm clustered via CDLP, golden causal path traversed across 5 layers down to commit `c3d9a107` (Alice Chen).
- **Act 3: Multi-Agent Quorum & Sub-15ms `GRAPH.COPY` Sandboxing** — Agents persist votes directly to FalkorDB (`WCS = 0.88 >= 0.75`), ephemeral sandbox cloned and verified, 1-click canary rollback executed.
- **Act 4: Closed-Loop O(1) Shortcut Net & Shift-Left CI/CD Blast Gate** — Persistent emerald shortcut edge compiled (`mttr: 78s -> 0.18s`), and PR #412 blocked via AST diff call-graph reachability!

---

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
git clone https://github.com/Siddhant75/GraphSRE.git
cd GraphSRE

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

## 📊 What Data is GraphSRE Checking?

GraphSRE bridges the gap between runtime telemetry and code-level version control by constructing a living **5-layer socio-technical graph** inside FalkorDB:

```
[Layer 1: Telemetry]     (:Alert {name: "HTTP 504 Gateway Timeout Storm", metric: 4800ms})
                                  │
                              [:AFFECTS]
                                  ▼
[Layer 2: Architecture]  (:Service {name: "PaymentService", tier: "TIER_1"})
                                  │
                              [:EXPOSES]
                                  ▼
[Layer 3: API Surface]   (:Endpoint {path: "/api/v1/charge", method: "POST"})
                                  │
                        [:IMPLEMENTED_BY]
                                  ▼
[Layer 4: Code AST]      (:Function {name: "call_stripe_webhook", file: "services/payment/stripe.py"})
                                  │
                            [:MODIFIED_BY]
                                  ▼
[Layer 5: Git & People]  (:Commit {sha: "c3d9a107", author: "Alice Chen"})
```

### 1. Benchmark Open-Source Reference Topology
The default seeded dataset in [`scripts/seed_mock_topology.py`](file:///d:/GraphHacks-hackathon/scripts/seed_mock_topology.py) is directly modeled on the industry-standard **Google Cloud Microservices Demo (Online Boutique)** and **Weaveworks Sock Shop**:
- **Services:** `FrontendAPI`, `CheckoutService`, `PaymentService`, `InventoryService`, `NotificationService`, `AuthService`.
- **Telemetry:** Ingests Prometheus/OpenTelemetry alert streams (`P99 Latency > 2000ms`, `HTTP 504 Gateway Timeout`, `DB Connection Pool Starvation`).
- **Failure Scenario:** A real-world distributed outage pattern — an unhandled third-party gateway read timeout (`timeout=None`) inducing thread pool exhaustion and cascading ingress 504s.

### 2. Generic Open-Source Codebase Ingestion
The underlying engines are **completely open and generic**:
- **AST Code Ingestion Engine ([`backend/ast_parser.py`](file:///d:/GraphHacks-hackathon/backend/ast_parser.py)):** Can parse **any** open-source Python repository. It automatically walks the AST, extracts function call hierarchies (`[:CALLS]`), generates structural SHA256 hashes, and emits OpenCypher statements to populate FalkorDB.
- **Shift-Left CI/CD Blast Gate ([`backend/api/cicd.py`](file:///d:/GraphHacks-hackathon/backend/api/cicd.py)):** Ingests arbitrary GitHub Pull Request diff patches, sanitizes unified diffs, extracts modified symbols, and calculates a 4-hop Structural Risk Index (SRI) before code is merged into production.
- **HNSW Vector Memory:** Ingests 384-dimensional sentence-transformer embeddings of historical SRE postmortems into native FalkorDB vector indices (`vecf32`) for sub-millisecond episodic recall.

---

## 🏆 Hackathon Track Alignment

| Track | Core GraphSRE Capability | FalkorDB Feature |
| :--- | :--- | :--- |
| **Track 1: Connected Data** | Multi-hop cross-layer traversal from HTTP alerts to AST functions & Git commits via 7 FastMCP tools. | GraphBLAS Sparse Matrix Engine |
| **Track 2: Memory & Coordination** | Central ACID blackboard replacing conversational token storms, 384-dim HNSW vector memory & quorum consensus. | Sub-millisecond Cypher Transactions & `GRAPH.COPY` |
| **Track 3: Company Brain** | Socio-technical ownership linking AST functions to git authors; Shift-Left CI/CD blast gate; $O(1)$ shortcut nets. | Dynamic Edge Synthesis with Bayesian Decay |
| **Side Prize: Technical Blog** | Publication-grade analysis of Vector RAG failure modes in SRE in [`blog.md`](file:///d:/GraphHacks-hackathon/blog.md) and [`docs/BLOG_POST.md`](file:///d:/GraphHacks-hackathon/docs/BLOG_POST.md). | Complete Platform Architecture |

---

## 🧪 Verification & Testing
All **23 test suites** pass with 100% success (`exit code 0`, 0 errors):

```bash
# Run complete test suite (23/23 unit, invariant, and E2E lifecycle tests)
python tests/test_fsm_lifecycle.py
python tests/test_e2e_lifecycle.py
python tests/test_graph_invariants.py
python tests/test_fsm_and_chaos.py
python tests/test_cicd_blast_gate.py

# Run standalone end-to-end incident lifecycle test (< 90s MTTR SLA)
python tests/test_e2e_lifecycle.py

# Run mathematical graph invariants test (anti-hallucination bound, bayesian decay, veto)
python tests/test_graph_invariants.py

# Run interactive CLI demonstration
python scripts/run_demo_simulation.py
```
