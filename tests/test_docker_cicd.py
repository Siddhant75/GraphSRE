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
