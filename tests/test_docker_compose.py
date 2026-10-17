import os
try:
    import yaml
except ImportError:
    yaml = None
try:
    import pytest
except ImportError:
    pytest = None

def test_docker_compose_zero_build_compliance():
    """Verify docker-compose.yml strictly pulls pre-built images with ZERO local build instructions."""
    compose_path = "docker-compose.yml"
    assert os.path.isfile(compose_path), f"File missing: {compose_path}"

    with open(compose_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    if yaml is not None:
        compose_data = yaml.safe_load(raw_text)
        services = compose_data.get("services", {})
    else:
        assert "build:" not in raw_text, "Local builds are strictly prohibited."
        assert "image: falkordb/falkordb:latest" in raw_text
        assert "image: sid7899999/graphsre-backend:latest" in raw_text
        assert "image: sid7899999/graphsre-frontend:latest" in raw_text
        services = {
            "falkordb": {
                "image": "falkordb/falkordb:latest",
                "ports": ["6379:6379"] if "6379:6379" in raw_text else [],
                "healthcheck": True if "healthcheck:" in raw_text else None
            },
            "backend": {
                "image": "sid7899999/graphsre-backend:latest",
                "ports": ["8000:8000"] if "8000:8000" in raw_text else [],
                "depends_on": ["falkordb"] if "depends_on:" in raw_text else []
            },
            "frontend": {
                "image": "sid7899999/graphsre-frontend:latest",
                "ports": ["3000:3000"] if "3000:3000" in raw_text else []
            }
        }

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

if __name__ == "__main__":
    test_docker_compose_zero_build_compliance()
    test_readme_dev_contains_bare_metal_instructions()
    print("All tests in test_docker_compose.py passed.")
