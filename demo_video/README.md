# Automated Demo Video Recorder

This directory uses **Playwright** and the system's local Google Chrome browser to record an automated, high-definition 1080p demonstration video of **GraphSRE** for hackathon submission.

---

## 🎬 How It Works

The automated script (`record_demo.js`):
1. Detects and verifies that the FastAPI backend (`http://localhost:8000`) and Next.js frontend (`http://localhost:3001`) are running. If not, it automatically boots them.
2. Launches Google Chrome in **1920x1080 (Full HD 1080p)** resolution with Playwright's native hardware video recorder.
3. Injects an on-screen **Keynote HUD Banner** that describes each act as it plays.
4. Executes the complete 4-Act walkthrough from `docs/DEMO_SCRIPT.md`:
   - **Act 1:** Outage Alert Storm & CDLP Ingestion into SEV-1.
   - **Act 2:** Cross-Layer Multi-Hop RCA, Tree-sitter AST hash inspection, and Quorum Consensus.
   - **Act 3:** Ephemeral Sandboxing (`GRAPH.COPY`), 1-Click Canary Rollback, and $O(1)$ Shortcut Net synthesis.
   - **Act 4:** Shift-Left CI/CD Blast Gate PR blocking and 384-dimensional HNSW Vector Memory.
5. Saves the final video file directly to:
   👉 **`demo_video/graphsre_demo_submission.webm`**

---

## 🚀 Running the Automated Recorder

To run the automated recorder and watch the browser perform the full walkthrough live:

```powershell
cd d:\GraphHacks-hackathon\demo_video
node record_demo.js
```

Or using pnpm:
```powershell
pnpm record
```

When finished, `graphsre_demo_submission.webm` is generated and ready to upload directly to YouTube, Loom, or Devpost!
