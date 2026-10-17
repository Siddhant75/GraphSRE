"""
Pytest Fixtures & Environment Configuration
File: tests/conftest.py
"""
import os
try:
    import pytest
except ImportError:
    pytest = None

if pytest is not None:
    @pytest.fixture(autouse=True)
    def configure_test_environment(monkeypatch):
        """Set test environment variables and fallback mock database credentials."""
        monkeypatch.setenv("FALKORDB_HOST", "localhost")
        monkeypatch.setenv("FALKORDB_PORT", "6379")
        monkeypatch.setenv("PRIMARY_GRAPH", "graphsre_test_blackboard")
        monkeypatch.setenv("TESTING", "true")
