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
