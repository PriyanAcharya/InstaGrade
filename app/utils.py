# app/utils.py
import difflib
import ast
import os
from typing import List, Dict


def compare_outputs(student_output: str, expected_output: str) -> bool:
    """
    Basic comparison: strip whitespace differences.
    Could be extended to compare numeric tolerance, unordered outputs etc.
    """
    if student_output is None:
        student_output = ""
    if expected_output is None:
        expected_output = ""
    return student_output.strip() == expected_output.strip()


# --- Plagiarism / similarity helpers ---


def _normalize_python_source(src: str) -> str:
    """
    Normalize Python source using AST: remove comments, normalize variable names structure.
    This reduces false positives from variable renaming / formatting changes.
    """
    try:
        tree = ast.parse(src)
    except Exception:
        # fallback: return raw source
        return src

    class Normalizer(ast.NodeTransformer):
        def __init__(self):
            super().__init__()
            self.counter = 0
            self.mapping = {}

        def _get_name(self, name):
            if name not in self.mapping:
                self.mapping[name] = f"v{self.counter}"
                self.counter += 1
            return self.mapping[name]

        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Load, ast.Del)):
                return ast.copy_location(ast.Name(id=self._get_name(node.id), ctx=node.ctx), node)
            return node

        def visit_arg(self, node):
            return ast.copy_location(ast.arg(arg=self._get_name(node.arg)), node)

    norm = Normalizer()
    try:
        new_tree = norm.visit(tree)
        ast.fix_missing_locations(new_tree)
        normalized = ast.unparse(new_tree) if hasattr(ast, "unparse") else src
        return normalized
    except Exception:
        return src


def similarity_ratio_code(code_a: str, code_b: str, language: str = "python") -> float:
    """
    Returns a 0..1 similarity ratio between two code strings.
    For Python, apply normalization. For other languages we fall back to raw difflib ratio.
    """
    if language == "python":
        a = _normalize_python_source(code_a)
        b = _normalize_python_source(code_b)
    else:
        a = code_a
        b = code_b

    seq = difflib.SequenceMatcher(None, a, b)
    return seq.ratio()


def detect_plagiarism_for_assignment(assignment_id: int, submission_dir: str = None, threshold: float = 0.80) -> List[Dict]:
    """
    Scan all submissions for an assignment (crud should provide files or path).
    This function expects crud.get_submissions_for_assignment to exist; if not,
    the backend should implement a wrapper around this function to supply file contents.

    Returns a list of flagged pairs: {"file_a":..., "file_b":..., "similarity":0.92}
    """

    # This helper tries to import crud. If not present, raise; backend should handle.
    try:
        from . import crud
    except Exception:
        raise RuntimeError("crud module not available: integrate with backend to fetch submission file paths")

    submissions = crud.get_submissions_for_assignment(assignment_id)
    # submissions: list of objects with {id, file_path, language, student_id}
    flagged = []
    n = len(submissions)
    for i in range(n):
        s1 = submissions[i]
        try:
            code1 = open(s1.file_path, "r", encoding="utf8", errors="ignore").read()
        except Exception:
            code1 = ""
        for j in range(i + 1, n):
            s2 = submissions[j]
            try:
                code2 = open(s2.file_path, "r", encoding="utf8", errors="ignore").read()
            except Exception:
                code2 = ""
            lang = s1.language or s2.language or "python"
            sim = similarity_ratio_code(code1, code2, language=lang)
            if sim >= threshold:
                flagged.append({
                    "submission_a": s1.id,
                    "submission_b": s2.id,
                    "student_a": s1.student_id,
                    "student_b": s2.student_id,
                    "similarity": round(sim, 3),
                })
    return flagged
