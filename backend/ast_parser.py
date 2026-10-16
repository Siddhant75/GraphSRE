"""
Tree-sitter & Native Python AST Code Ingestion Engine
File: backend/ast_parser.py
"""
import ast
import hashlib
from typing import Any, Dict, List, Tuple


class ASTCodeIngestionEngine:
    """
    Parses source code into AST functions, computes deterministic AST hashes,
    extracts call hierarchies, and generates OpenCypher mutation batches.
    """

    def __init__(self):
        pass

    def parse_python_source(self, file_path: str, source_code: str) -> List[Dict[str, Any]]:
        """
        Parses python source code and extracts function definitions with metadata,
        line ranges, async indicators, and deterministic 8-char SHA256 AST hashes.
        """
        tree = ast.parse(source_code)
        functions = []

        # Normalize module qualified name from file path
        clean_path = file_path.replace("\\", "/")
        if clean_path.endswith(".py"):
            clean_path = clean_path[:-3]
        module_path = clean_path.replace("/", ".")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_name = node.name
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line + 1)
                is_async = isinstance(node, ast.AsyncFunctionDef)

                # Compute deterministic AST structural hash
                ast_repr = ast.dump(node)
                ast_hash = hashlib.sha256(ast_repr.encode("utf-8")).hexdigest()[:8]

                functions.append({
                    "name": fn_name,
                    "qualified_name": f"{module_path}.{fn_name}",
                    "file_path": file_path,
                    "line_start": start_line,
                    "line_end": end_line,
                    "ast_hash": ast_hash,
                    "is_async": is_async,
                })

        functions.sort(key=lambda f: f["line_start"])
        return functions

    def extract_calls(self, source_code: str) -> List[Tuple[str, str]]:
        """
        Identifies caller -> callee pairs within source code.
        """
        tree = ast.parse(source_code)
        calls = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        callee_name = None
                        if isinstance(child.func, ast.Name):
                            callee_name = child.func.id
                        elif isinstance(child.func, ast.Attribute):
                            callee_name = child.func.attr
                        if callee_name and callee_name != caller_name:
                            calls.append((caller_name, callee_name))
        return calls

    def generate_cypher_for_commit(
        self,
        commit_sha: str,
        author: str,
        function_name: str,
        file_path: str,
    ) -> str:
        """
        Generates OpenCypher statements linking Commit to Function via [:MODIFIED_BY].
        """
        return f"""
        MERGE (c:Commit {{sha: '{commit_sha}'}})
          ON CREATE SET c.author = '{author}', c.timestamp = timestamp()
        MATCH (f:Function {{file_path: '{file_path}'}})
        WHERE f.name = '{function_name}' OR f.qualified_name CONTAINS '{function_name}'
        MERGE (f)-[:MODIFIED_BY]->(c);
        """

    def generate_invalidation_cypher(self, commit_sha: str) -> str:
        """
        Generates OpenCypher applying 70% Bayesian penalty to incoming shortcut edges
        when a commit modifies an underlying AST function.
        """
        return f"""
        MATCH (c:Commit {{sha: '{commit_sha}'}})<-[:MODIFIED_BY]-(f:Function)<-[r:CAUSED_BY_SHORTCUT]-(a:Alert)
        SET r.weight = r.weight * 0.30,
            r.stale = true,
            r.invalidation_reason = 'CODE_MODIFIED_{commit_sha}'
        RETURN f.qualified_name AS invalidated_function, r.weight AS new_penalized_weight;
        """
