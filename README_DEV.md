# GraphSRE Local Development & Zero-Build Quickstart

GraphSRE enforces a **Zero Local Docker Build** architecture to conserve developer and judge disk space.

---

## 1. Zero-Build Production Quickstart (For Judges & Evaluators)

Run the full production stack using pre-built cloud images from Docker Hub (`sid7899999`):

```bash
docker-compose up -d
```

This immediately pulls and boots:
- `falkordb/falkordb:latest` on port `6379`
- `sid7899999/graphsre-backend:latest` on port `8000` (FastAPI REST + WebSockets + FastMCP)
- `sid7899999/graphsre-frontend:latest` on port `3000` (Next.js 14 Cytoscape.js War Room)

To shut down:
```bash
docker-compose down
```

---

## 2. Bare-Metal Native Development Setup

For local development without container build overhead:

### Step 1: Start Lightweight FalkorDB
```bash
docker run -d --name graphsre-falkordb -p 6379:6379 falkordb/falkordb:latest
```

### Step 2: Backend Setup (Python 3.11+)
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend with hot reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Frontend Setup (Node.js 18+)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.
