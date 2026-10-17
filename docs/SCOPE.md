# Project Scope & Capability Boundaries
## GraphSRE: Autonomous Site Reliability Engineering & Code Brain

```
   ┌─────────────────────────────────────────────────────────────────────────────────┐
   │                       GRAPHSRE SCOPE & BOUNDARIES                               │
   │               Autonomous Site Reliability Engineering & Code Intelligence        │
   └─────────────────────────────────────────────────────────────────────────────────┘
```

**Document Version:** 1.0.0  
**Status:** Canonical Project Boundary Specification  

---

## 1. Project In-Scope Capabilities

The following capabilities are fully engineered, tested, and included in GraphSRE:

### 1.1 Central Graph Blackboard Architecture
- **FalkorDB Sub-Millisecond ACID Store:** Single source of truth for runtime topology, telemetry alerts, code ASTs, git history, and agent deliberation states.
- **GraphBLAS Sparse Matrix Algebra:** Sub-millisecond execution ($< 1\text{ ms}$) for 6-hop causal path traversals across 500,000+ nodes.
- **Embedded HNSW Vector Memory:** 384-dimensional dense vectors indexed directly on graph nodes (`CALL db.idx.vector.queryNodes(...)`) for hybrid semantic and topological recall.
- **Zero-Cost Ephemeral Sandboxing:** Atomic in-memory graph cloning in $< 10\text{ ms}$ via `GRAPH.COPY sandbox_<id>` for counterfactual blast radius simulation before executing mitigating actions.

### 1.2 Multi-Agent Autonomous Swarm (FastMCP Interfaces)
- **Triage Agent:** Real-time alert ingestion, Community Detection via Label Propagation (CDLP) clustering, blast radius calculation, and dynamic severity classification ($Sev-1$ to $Sev-4$).
- **RCA Agent:** Cross-layer causal walk from alert $\to$ service $\to$ endpoint $\to$ function $\to$ commit. Evaluates topological reachability $T_{\text{graph}} \in \{0, 1\}$.
- **Memory Agent:** Episodic vector recall of past postmortems, composite confidence evaluation ($C_{\text{SRE}}$), and mathematical quorum consensus voting with absolute veto power ($w_{\text{Memory}} = 0.35$).
- **Remediation Agent:** Ephemeral sandbox simulation, 1-click canary rollback execution, and postmortem incident synthesis.

### 1.3 Static Code Ingestion & Git Blame Linker
- **Tree-sitter Polyglot Parser:** Parsing of Python, Go, and TypeScript source files into discrete `:Function` nodes, line boundaries, and caller-callee `:CALLS` hierarchies.
- **Deterministic Structural Hashing:** SHA-256 AST hashing (`ast_hash`) enabling instant detection of code modifications without relying on fragile line numbers.
- **Git Commit Attribution:** Dynamic linking of Git commits (`:Commit`) to modified AST functions via `[:MODIFIED_BY]`.

### 1.4 Continuous Learning: Self-Curating $O(1)$ Shortcut Net
- **Dynamic Bypass Synthesis:** Generating direct `[:CAUSED_BY_SHORTCUT]` edges upon incident resolution, enabling 1.4-second instant root-cause resolution for recurring alerts.
- **Bayesian Exponential Temporal Decay:** Continuous decay $w(t) = w_0 \exp(-\lambda \Delta t)$ with an exact 30-day half-life and automated culling when $w < 0.10$.
- **AST Modification Penalty:** Immediate $-70\%$ weight penalty ($W_{\text{penalized}} = 0.30 \times W$) when linked code is modified in Git.

### 1.5 Shift-Left CI/CD Blast Gate
- **Pull Request Risk Evaluation:** Evaluating Git diffs in GitHub Actions pipelines to identify modified AST nodes and upstream dependency blast radius.
- **Structural Risk Index ($\text{SRI}$):** Automated PR blocking gate when $\text{SRI} \ge 0.70$, with interactive Cytoscape graph comments posted to pull requests.

### 1.6 Interactive Cytoscape.js War Room UI
- **Force-Directed Graph Canvas:** Dual-layout support (`cose-bilkent` and `dagre`), dynamic zoom/fit controls, and slide-out Node Inspector.
- **Agent Deliberation HUD:** Real-time WebSocket streaming feed with role-based agent thought cards and Cypher snippet visualization.
- **Quorum Consensus Meter:** Live gradient meter tracking weighted consensus against the $0.75$ threshold line.
- **Slack-Style Action Cards & Chaos Injection Panel:** 1-click canary rollback triggers and 4 chaos injection scenarios.

---

## 2. Out-of-Scope Capabilities (Future Engineering Roadmap)

To maintain architectural focus, safety, and deterministic verifiability during incident response, the following capabilities are explicitly outside the current scope:

| Capability | Current Status | Future Roadmap (Post-Hackathon) |
| :--- | :---: | :--- |
| **Autonomous Code Writing & PR Merging** | **Out of Scope** | GraphSRE identifies culprit commits, lines, and functions, and executes safe operational rollbacks. Generating automated source code patches and merging PRs without human review introduces unacceptable production risk. |
| **Bare-Metal IPMI / BMC Chassis Power-Cycling** | **Out of Scope** | GraphSRE operates at the application, Kubernetes, and container orchestration layer. Physical motherboard power manipulation is intentionally excluded. |
| **Multi-Cloud IAM Role Auto-Provisioning** | **Out of Scope** | Cross-cloud identity modifications (AWS IAM, GCP IAM, Azure AD) during outages are deferred to dedicated identity governance systems to prevent security privilege escalation. |
| **Kernel-Space eBPF Packet Interception** | **Out of Scope** | Telemetry is ingested from standard observability platforms (Datadog, Prometheus, OpenTelemetry). Writing custom in-kernel C eBPF probes is planned for future low-level network tracing. |

---

## 3. Scope Deliverables Matrix

| Artifact | Location | Status |
| :--- | :--- | :---: |
| **FalkorDB Client & Sandboxing** | `server/falkordb_client.py` | ✅ Production Ready |
| **FastMCP Tool Server (7 Tools)** | `server/mcp_server.py` | ✅ Production Ready |
| **FastAPI Backend & WebSocket Hub** | `backend/` | ✅ Production Ready |
| **Tree-sitter AST Parser Engine** | `backend/ast_parser.py` | ✅ Production Ready |
| **Next.js 14 Cytoscape Frontend** | `frontend/` | ✅ Production Ready |
| **Pre-built Cloud Container Images** | Docker Hub `sid7899999` | ✅ Published & Verified |
| **Mathematical Invariant Test Suite** | `tests/test_graph_invariants.py` | ✅ 100% Passing |
| **End-to-End Incident Lifecycle Suite** | `tests/test_e2e_lifecycle.py` | ✅ 100% Passing |
