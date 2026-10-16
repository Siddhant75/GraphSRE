import os
import sys

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    class _PytestMock:
        pass
    pytest = _PytestMock()

from backend.ast_parser import ASTCodeIngestionEngine

SAMPLE_PAYMENT_CODE = """
def process_payment(amount: float, customer_id: str):
    # Charge through payment gateway
    return execute_stripe_charge(amount)

async def execute_stripe_charge(amount: float):
    # Call Stripe webhook
    return True
"""


def test_ast_python_function_extraction():
    """Verify AST parser extracts sync and async functions with line numbers and SHA256 hashes."""
    engine = ASTCodeIngestionEngine()
    functions = engine.parse_python_source("services/payment/gateway.py", SAMPLE_PAYMENT_CODE)

    assert len(functions) == 2
    fn_map = {f["name"]: f for f in functions}

    assert "process_payment" in fn_map
    assert fn_map["process_payment"]["is_async"] is False
    assert fn_map["process_payment"]["line_start"] == 2
    assert len(fn_map["process_payment"]["ast_hash"]) == 8

    assert "execute_stripe_charge" in fn_map
    assert fn_map["execute_stripe_charge"]["is_async"] is True
    assert fn_map["execute_stripe_charge"]["line_start"] == 6


def test_ast_function_call_hierarchy():
    """Verify internal function call detection (process_payment calls execute_stripe_charge)."""
    engine = ASTCodeIngestionEngine()
    calls = engine.extract_calls(SAMPLE_PAYMENT_CODE)
    assert ("process_payment", "execute_stripe_charge") in calls


def test_generate_commit_linking_cypher():
    """Verify OpenCypher statements linking Commit to Function via [:MODIFIED_BY]."""
    engine = ASTCodeIngestionEngine()
    cypher = engine.generate_cypher_for_commit(
        commit_sha="c3d9a107",
        author="alice@company.io",
        function_name="execute_stripe_charge",
        file_path="services/payment/gateway.py"
    )
    assert "MERGE (c:Commit {sha: 'c3d9a107'})" in cypher
    assert "MERGE (f)-[:MODIFIED_BY]->(c)" in cypher


def test_generate_shortcut_invalidation_cypher():
    """Verify 70% Bayesian penalty OpenCypher query upon code commit."""
    engine = ASTCodeIngestionEngine()
    invalidation_cypher = engine.generate_invalidation_cypher("c3d9a107")
    assert "SET r.weight = r.weight * 0.30" in invalidation_cypher
    assert "r.stale = true" in invalidation_cypher
    assert "CODE_MODIFIED_c3d9a107" in invalidation_cypher


if __name__ == "__main__":
    tests = [
        ("test_ast_python_function_extraction", test_ast_python_function_extraction),
        ("test_ast_function_call_hierarchy", test_ast_function_call_hierarchy),
        ("test_generate_commit_linking_cypher", test_generate_commit_linking_cypher),
        ("test_generate_shortcut_invalidation_cypher", test_generate_shortcut_invalidation_cypher),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f"Running {name}...")
        try:
            test_fn()
            print(f"PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {name} -> {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\nAST Ingestion Test Results: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
