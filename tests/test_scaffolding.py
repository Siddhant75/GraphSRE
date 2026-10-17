import os
try:
    import pytest
except ImportError:
    pytest = None

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

if __name__ == "__main__":
    test_directory_packages_exist()
    test_requirements_file_contains_core_dependencies()
    test_env_example_has_all_required_variables()
    test_gitignore_covers_python_and_node()
    print("All tests in test_scaffolding.py passed.")
