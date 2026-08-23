import ast
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).parents[2] / "src" / "sevendtd"


def test_core_modules_do_not_import_cli_modules() -> None:
    violations: list[str] = []
    for path in PACKAGE.rglob("*.py"):
        if "cli" in path.relative_to(PACKAGE).parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names = [node.module]
            absolute_cli = any(
                name == "sevendtd.cli" or name.startswith("sevendtd.cli.") for name in names
            )
            relative_cli = (
                isinstance(node, ast.ImportFrom)
                and node.level > 0
                and any(name == "cli" or name.startswith("cli.") for name in names)
            )
            if absolute_cli or relative_cli:
                violations.append(str(path.relative_to(PACKAGE)))
    assert violations == []


def test_core_import_does_not_load_cli_or_optional_packages() -> None:
    script = """
import sys
import sevendtd

forbidden = ("sevendtd.cli", "typer", "rich", "PIL", "fastapi", "sqlalchemy")
assert not {name for name in forbidden if name in sys.modules}
"""
    subprocess.run([sys.executable, "-c", script], check=True)
