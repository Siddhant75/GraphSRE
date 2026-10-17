import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

BLOG_PATH = os.path.join(REPO_ROOT, "docs", "BLOG_POST.md")
if not os.path.exists(BLOG_PATH):
    BLOG_PATH = os.path.join(REPO_ROOT, "blog.md")


def test_blog_post_exists_and_meets_rigor_criteria():
    """Verify blog post draft exists, meets length requirement, and includes required technical terminology."""
    assert os.path.exists(BLOG_PATH), "docs/BLOG_POST.md must exist for hackathon side prize submission"
    
    with open(BLOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    words = content.split()
    assert len(words) >= 2000, f"Blog post must be exhaustive (>2,000 words), currently {len(words)} words"

    key_terms = [
        "FalkorDB",
        "GraphBLAS",
        "Vector RAG",
        "Asymmetric Causality",
        "Blackboard",
        "HNSW",
        "Tree-sitter",
        "GRAPH.COPY",
        "Bayesian",
        "Quorum",
        "MTTR",
        "PageRank",
        "CDLP",
        "AirPods 5",
    ]

    lower_content = content.lower()
    for term in key_terms:
        assert term.lower() in lower_content, f"Required technical term missing from blog: '{term}'"


def test_blog_contains_mathematical_formulations():
    """Verify blog.md includes core formal mathematical formulations and algorithmic rigor."""
    assert os.path.exists(BLOG_PATH), "blog.md must exist for hackathon side prize submission"
    
    with open(BLOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert (r"C_{\text{SRE}}" in content or "C_SRE" in content), "Blog must contain Composite Confidence Score C_SRE formula"
    assert (r"\lambda" in content or "half-life" in content.lower()), "Blog must contain exponential decay lambda or half-life formulation"
    assert "GraphBLAS" in content, "Blog must explicitly analyze GraphBLAS linear algebraic performance"


if __name__ == "__main__":
    tests = [
        test_blog_post_exists_and_meets_rigor_criteria,
        test_blog_contains_mathematical_formulations,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")

    print(f"\n{passed}/{len(tests)} tests passed.")
    if passed != len(tests):
        sys.exit(1)
