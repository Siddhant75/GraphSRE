# GraphSRE 3-Minute Video Demonstration Script

**Title:** Autonomous Site Reliability Engineering & Code Brain with FalkorDB  
**Total Target Duration:** 3 minutes (180 seconds)  
**URL:** `http://localhost:3000`  

---

## Act 1: The Outage Alert Storm (00:00 - 00:45)
* **Screen:** Next.js 14 War Room (`http://localhost:3000`). Cytoscape.js canvas displaying microservice topology (FrontendAPI, CheckoutService, PaymentService).
* **Voiceover (Narration):**  
  *"Modern cloud infrastructures generate deafening alert storms during outages. When a downstream microservice degrades, hundreds of cascading HTTP 504 and latency alerts flood SREs. Traditional multi-agent systems exchange raw text prompts, causing quadratic token bloat and hallucination cascades.*  
  *Watch what happens when we inject a real-world chaos fault into PaymentService."*
* **Action:** Click **[🔥 Inject Chaos Fault]** (Unbounded Socket Timeout).
* **Visual Cue:** PaymentService node turns crimson red and pulses. The Triage Agent ingests alerts, runs Community Detection (CDLP), clusters them into a single incident, and calculates a 3-hop blast radius.

---

## Act 2: Multi-Hop RCA & Quorum Consensus (00:45 - 01:30)
* **Screen:** Focus on Cytoscape.js canvas showing yellow-glowing causal tracer line and the Live Agent Blackboard Feed.
* **Voiceover (Narration):**  
  *"Instead of hallucinating, our RCA Agent traverses the connected graph from the PaymentService endpoint down through Tree-sitter AST call hierarchies to function `call_stripe_webhook()`, and straight to culprit commit `c3d9a107` authored by Alice Chen.*  
  *Notice our strict anti-hallucination invariant: if a theory has no topological path in FalkorDB, it is mathematically rejected.*  
  *Next, the Memory Agent queries FalkorDB's embedded HNSW vector index, retrieves a matching historical postmortem with 0.94 similarity, and evaluates Composite Confidence $C_{\text{SRE}} = 0.88$. Quorum consensus is reached at 0.88 over 0.75!"*

---

## Act 3: Ephemeral Sandbox & O(1) Shortcut Net (01:30 - 02:20)
* **Screen:** Human-in-the-Loop Action Card and Shortcut Net visualizer.
* **Voiceover (Narration):**  
  *"Before applying remediation, the Remediation Agent invokes FalkorDB's zero-cost `GRAPH.COPY` command, cloning the production graph in under 10 milliseconds. It simulates a 10% canary traffic shift without touching production.*  
  *With simulation passed, we click '1-Click Approve Canary Revert'. The incident resolves in 78 seconds—well within our 90-second SLA.*  
  *Even better: GraphSRE compiles continuous memory by synthesizing a radiant emerald $O(1)$ shortcut edge directly from the symptom to the root cause, subject to Bayesian temporal decay."*
* **Action:** Click **[🔥 Inject Chaos Fault]** a second time.
* **Visual Cue:** The system resolves the second incident in **1.4 seconds** by traversing the $O(1)$ shortcut edge!

---

## Act 4: Shift-Left CI/CD Blast Gate (02:20 - 03:00)
* **Screen:** Navigate to `/cicd-blast-gate`.
* **Voiceover (Narration):**  
  *"Finally, GraphSRE shifts left into CI/CD. When a developer submits Pull Request #412 proposing to strip socket timeouts, our Blast Gate evaluates the AST diff against FalkorDB, calculates a Structural Risk Index of 0.88, blocks the merge, and alerts code owners.*  
  *That is GraphSRE: Connected Data, ACID Memory, and a permanent Company Brain powered by FalkorDB."*
