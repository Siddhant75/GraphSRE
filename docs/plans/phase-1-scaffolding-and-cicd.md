# Phase 1: Scaffolding, Cloud Docker CI/CD & Production Compose Implementation Plan

> **For AI Assistant:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task.

**Goal:** Establish clean repository layout, environment configuration, GitHub Actions cloud CI/CD pipeline targeting Docker Hub user `sid7899999`, zero-build production `docker-compose.yml`, and bare-metal local development setup.

**Architecture:** Cloud-first Docker build strategy to honor local disk space constraints. GitHub Actions builds and pushes multi-architecture images to Docker Hub; local environment runs bare-metal Python/Node or pulls pre-built containers with zero build cache usage.

**Tech Stack:** Python 3.11+, Node.js 18+, Docker, Docker Compose, GitHub Actions, PyYAML, Pytest.

---

## Task Breakdown

### Task 1.1: Project Directory Structure & Environment Scaffolding

**Files:**
- Create: `backend/__init__.py`
- Create: `server/__init__.py`
- Create: `scripts/__init__.py`
- Create: `tests/__init__.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Test: `tests/test_scaffolding.py`

**Step 1: Write the failing test**

Create `tests/test_scaffolding.py`:
```python
import os
import pytest

def test_directory_packages_exist():
    """Verify that backend, server, scripts, and tests directories exist with __init__.py files."""
    packages = ["backend", "server", "scripts", "tests"]
    for pkg in packages:
        init_file = os.path.join(pkg, "__init__.py")
        assert os.path.isfile(init_file), f"Package initialization file missing: {init_file}"

def test_requirements_file_contains_core_dependencies():
    """Verify requirements.txt exists and specifies essential libraries."""
    req_path = "requirements.txt"
    assert os.path.isfile(req_path), "requirements.txt must exist at project root"
    
    with open(req_path, "r", encoding="utf-8") as f:
        content = f.read()

    expected_deps = [
        "fastapi",
        "uvicorn",
        "redis",
        "mcp",
        "numpy",
        "httpx",
        "pytest",
        "pytest-asyncio",
        "pyyaml",
        "websockets",
        "tree-sitter"
    ]
    for dep in expected_deps:
        assert dep in content, f"Dependency '{dep}' missing from requirements.txt"

def test_env_example_has_all_required_variables():
    """Verify .env.example specifies all required blackboard, LLM, and frontend URLs."""
    env_path = ".env.example"
    assert os.path.isfile(env_path), ".env.example must exist at project root"
    
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    required_vars = [
        "FALKORDB_HOST",
        "FALKORDB_PORT",
        "PRIMARY_GRAPH",
        "OPENAI_API_KEY",
        "GROQ_API_KEY",
        "NEXT_PUBLIC_API_URL",
        "NEXT_PUBLIC_WS_URL"
    ]
    for var in required_vars:
        assert f"{var}=" in content or f"{var} =" in content, f"Environment variable {var} missing from .env.example"

def test_gitignore_covers_python_and_node():
    """Verify .gitignore properly excludes virtual environments, node_modules, and cache files."""
    gitignore_path = ".gitignore"
    assert os.path.isfile(gitignore_path), ".gitignore must exist"
    
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert ".venv" in content, ".venv should be ignored"
    assert "node_modules" in content, "node_modules should be ignored"
    assert ".env" in content, ".env secrets should be ignored"
    assert "__pycache__" in content, "__pycache__ should be ignored"
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_scaffolding.py -v
```
Expected: FAIL with `Package initialization file missing: backend/__init__.py` or `FileNotFoundError`.

**Step 3: Write minimal implementation**

Create `backend/__init__.py`:
```python
"""GraphSRE Backend Package."""
```

Create `server/__init__.py`:
```python
"""GraphSRE FastMCP & FalkorDB Server Package."""
```

Create `scripts/__init__.py`:
```python
"""GraphSRE Utility and Seeding Scripts Package."""
```

Create `tests/__init__.py`:
```python
"""GraphSRE Test Suite Package."""
```

Create `requirements.txt`:
```txt
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
redis>=5.0.4
mcp>=1.0.0
numpy>=1.26.0
httpx>=0.27.0
pytest>=8.2.0
pytest-asyncio>=0.23.0
pyyaml>=6.0.1
websockets>=12.0
tree-sitter>=0.21.3
tree-sitter-python>=0.21.0
```

Create `.env.example`:
```env
# FalkorDB Central Blackboard Configuration
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
PRIMARY_GRAPH=graphsre_production

# LLM Providers (Optional for local mocks and FastMCP agents)
OPENAI_API_KEY=mock-openai-key
GROQ_API_KEY=mock-groq-key

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

Create `.gitignore`:
```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environments
.venv/
env/
venv/
ENV/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
.next/
out/

# Environment Variables & Secrets
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDEs & OS Files
.idea/
.vscode/
*.swp
*.swo
.DS_Store
Thumbs.db
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_scaffolding.py -v
```
Expected: PASS (4 tests passed).

**Step 5: Commit**

```bash
git add backend/__init__.py server/__init__.py scripts/__init__.py tests/__init__.py requirements.txt .env.example .gitignore tests/test_scaffolding.py
git commit -m "feat(scaffold): initialize project packages requirements and environment templates"
```

---

### Task 1.2: Cloud Docker CI/CD with GitHub Actions (`sid7899999`)

**Files:**
- Create: `.github/workflows/docker-build-push.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `.dockerignore`
- Test: `tests/test_docker_cicd.py`

**Step 1: Write the failing test**

Create `tests/test_docker_cicd.py`:
```python
import os
import yaml
import pytest

def test_github_actions_workflow_configuration():
    """Verify the workflow file exists, triggers on main/feat branches, and targets Docker Hub sid7899999."""
    workflow_path = ".github/workflows/docker-build-push.yml"
    assert os.path.isfile(workflow_path), f"Workflow file missing: {workflow_path}"

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = yaml.safe_load(f)

    # Validate triggers
    triggers = workflow.get("on", {})
    assert "push" in triggers or "workflow_dispatch" in triggers, "Workflow must trigger on push and/or workflow_dispatch"
    
    # Validate jobs
    jobs = workflow.get("jobs", {})
    assert "build-and-push" in jobs, "Workflow must contain 'build-and-push' job"
    job = jobs["build-and-push"]
    assert job.get("runs-on") == "ubuntu-latest", "Job should run on ubuntu-latest"

    # Validate workflow raw content for target Docker Hub user
    with open(workflow_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    assert "sid7899999/graphsre-backend:latest" in raw_text, "Workflow must tag sid7899999/graphsre-backend:latest"
    assert "sid7899999/graphsre-frontend:latest" in raw_text, "Workflow must tag sid7899999/graphsre-frontend:latest"
    assert "DOCKERHUB_TOKEN" in raw_text, "Workflow must use DOCKERHUB_TOKEN secret"

def test_backend_dockerfile():
    """Verify backend Dockerfile uses python:3.11-slim and sets uvicorn entrypoint."""
    df_path = "backend/Dockerfile"
    assert os.path.isfile(df_path), f"Backend Dockerfile missing: {df_path}"

    with open(df_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FROM python:3.11-slim" in content, "Backend Dockerfile must use python:3.11-slim base image"
    assert "COPY requirements.txt" in content, "Must copy requirements.txt"
    assert "pip install" in content, "Must install python requirements"
    assert "EXPOSE 8000" in content, "Backend must expose port 8000"

def test_frontend_dockerfile():
    """Verify frontend Dockerfile uses multi-stage node build and exposes 3000."""
    df_path = "frontend/Dockerfile"
    assert os.path.isfile(df_path), f"Frontend Dockerfile missing: {df_path}"

    with open(df_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "node:" in content, "Frontend Dockerfile must use node base image"
    assert "EXPOSE 3000" in content, "Frontend must expose port 3000"

def test_dockerignore():
    """Verify .dockerignore excludes heavy dependencies and local state."""
    di_path = ".dockerignore"
    assert os.path.isfile(di_path), ".dockerignore must exist"

    with open(di_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "node_modules" in content, "node_modules must be in .dockerignore"
    assert ".venv" in content, ".venv must be in .dockerignore"
    assert ".git" in content, ".git must be in .dockerignore"
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_docker_cicd.py -v
```
Expected: FAIL with `Workflow file missing: .github/workflows/docker-build-push.yml`.

**Step 3: Write minimal implementation**

Create `.github/workflows/docker-build-push.yml`:
```yaml
name: Build and Push Docker Images to Docker Hub

on:
  push:
    branches:
      - main
      - feat/*
      - fix/*
    tags:
      - 'v*.*.*'
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME || 'sid7899999' }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and Push Backend Image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./backend/Dockerfile
          push: true
          tags: |
            sid7899999/graphsre-backend:latest
            sid7899999/graphsre-backend:${{ github.sha }}

      - name: Build and Push Frontend Image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          push: true
          tags: |
            sid7899999/graphsre-frontend:latest
            sid7899999/graphsre-frontend:${{ github.sha }}
```

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000 8001

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine AS base

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
```

Create `.dockerignore`:
```
node_modules
.next
__pycache__
*.pyc
.git
.venv
.env
dist
build
.coverage
htmlcov
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_docker_cicd.py -v
```
Expected: PASS (4 tests passed).

**Step 5: Commit**

```bash
git add .github/workflows/docker-build-push.yml backend/Dockerfile frontend/Dockerfile .dockerignore tests/test_docker_cicd.py
git commit -m "feat(cicd): add github actions workflow for sid7899999 and container dockerfiles"
```

---

### Task 1.3: Zero-Build Production Docker Compose & Bare-Metal Native Dev Setup

**Files:**
- Create: `docker-compose.yml`
- Create: `README_DEV.md`
- Test: `tests/test_docker_compose.py`

**Step 1: Write the failing test**

Create `tests/test_docker_compose.py`:
```python
import os
import yaml
import pytest

def test_docker_compose_zero_build_compliance():
    """Verify docker-compose.yml strictly pulls pre-built images with ZERO local build instructions."""
    compose_path = "docker-compose.yml"
    assert os.path.isfile(compose_path), f"File missing: {compose_path}"

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    assert "falkordb" in services, "falkordb service must be defined"
    assert "backend" in services, "backend service must be defined"
    assert "frontend" in services, "frontend service must be defined"

    # Enforce NO 'build' directive anywhere in docker-compose.yml
    for service_name, config in services.items():
        assert "build" not in config, f"Service '{service_name}' contains a 'build' directive! Local builds are strictly prohibited."

    # Validate image references
    assert services["falkordb"].get("image") == "falkordb/falkordb:latest", "falkordb must use falkordb/falkordb:latest"
    assert services["backend"].get("image") == "sid7899999/graphsre-backend:latest", "backend must pull sid7899999/graphsre-backend:latest"
    assert services["frontend"].get("image") == "sid7899999/graphsre-frontend:latest", "frontend must pull sid7899999/graphsre-frontend:latest"

    # Validate port mappings
    assert "6379:6379" in services["falkordb"].get("ports", []), "FalkorDB port 6379 must be exposed"
    assert "8000:8000" in services["backend"].get("ports", []), "Backend port 8000 must be exposed"
    assert "3000:3000" in services["frontend"].get("ports", []), "Frontend port 3000 must be exposed"

    # Validate healthcheck & dependencies
    assert "healthcheck" in services["falkordb"], "FalkorDB service must have a healthcheck"
    assert "depends_on" in services["backend"], "Backend service must depend on healthy falkordb"

def test_readme_dev_contains_bare_metal_instructions():
    """Verify README_DEV.md documents native local dev execution and judge one-liner."""
    readme_path = "README_DEV.md"
    assert os.path.isfile(readme_path), f"File missing: {readme_path}"

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "docker-compose up" in content, "README_DEV.md must contain judge one-liner docker-compose up"
    assert "uvicorn" in content, "README_DEV.md must document running backend natively via uvicorn"
    assert "npm run dev" in content or "pnpm dev" in content, "README_DEV.md must document running frontend dev server"
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_docker_compose.py -v
```
Expected: FAIL with `File missing: docker-compose.yml`.

**Step 3: Write minimal implementation**

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  falkordb:
    image: falkordb/falkordb:latest
    container_name: graphsre-falkordb
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data
    environment:
      - FALKORDB_ARGS=--threads 4
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  backend:
    image: sid7899999/graphsre-backend:latest
    container_name: graphsre-backend
    ports:
      - "8000:8000"
    environment:
      - FALKORDB_HOST=falkordb
      - FALKORDB_PORT=6379
      - PRIMARY_GRAPH=graphsre_production
      - OPENAI_API_KEY=${OPENAI_API_KEY:-mock}
      - GROQ_API_KEY=${GROQ_API_KEY:-mock}
    depends_on:
      falkordb:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    image: sid7899999/graphsre-frontend:latest
    container_name: graphsre-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  falkordb_data:
```

Create `README_DEV.md`:
```markdown
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
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_docker_compose.py -v
```
Expected: PASS (2 tests passed).

**Step 5: Commit**

```bash
git add docker-compose.yml README_DEV.md tests/test_docker_compose.py
git commit -m "feat(compose): add zero-build docker-compose and bare-metal dev documentation"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/phase-1-scaffolding-and-cicd.md`. Two execution options:

1. **Subagent-Driven (this session)** - Dispatch fresh subagent per task, review between tasks, fast iteration.
2. **Parallel Session (separate)** - Open new session with `superpowers:executing-plans`, batch execution with checkpoints.
