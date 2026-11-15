"""Architecture rules enforced as tests.

* The domain imports only the standard library (and itself).
* The application layer imports only the standard library, the domain and itself.
"""

import ast
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
STDLIB = set(sys.stdlib_module_names)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def _violations(layer: str, allowed_prefixes: tuple[str, ...]) -> list[str]:
    problems = []
    for path in sorted((APP / layer).rglob("*.py")):
        for name in _imports(path):
            root = name.split(".")[0]
            if root == "__future__" or root in STDLIB:
                continue
            if not name.startswith(allowed_prefixes):
                problems.append(f"{path.relative_to(APP)} imports {name}")
    return problems


def test_domain_imports_only_the_standard_library() -> None:
    assert _violations("domain", ("app.domain",)) == []


def test_application_depends_only_on_domain() -> None:
    assert _violations("application", ("app.domain", "app.application")) == []


@pytest.mark.parametrize("framework", ["fastapi", "sqlalchemy", "pydantic"])
def test_no_framework_in_core(framework: str) -> None:
    for layer in ("domain", "application"):
        for path in (APP / layer).rglob("*.py"):
            assert not any(n.split(".")[0] == framework for n in _imports(path)), path
