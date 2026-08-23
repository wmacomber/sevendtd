import ast
import re
from pathlib import Path

import sevendtd

ROOT = Path(__file__).parents[2]
GUIDE = ROOT / "docs/python.md"
PYTHON_FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[[^]]+]\(([^)]+)\)")


def python_examples() -> list[str]:
    return PYTHON_FENCE.findall(GUIDE.read_text())


def test_python_guide_examples_compile() -> None:
    examples = python_examples()
    assert examples
    for index, source in enumerate(examples, start=1):
        compile(source, f"{GUIDE}#python-{index}", "exec")


def test_python_guide_uses_public_root_imports() -> None:
    imported: set[str] = set()
    for source in python_examples():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "sevendtd":
                imported.update(alias.name for alias in node.names)

    public = set(sevendtd.__all__)
    assert imported
    assert imported <= public
    assert all(hasattr(sevendtd, name) for name in imported)


def test_python_guide_and_readme_local_links_resolve() -> None:
    for document in (GUIDE, ROOT / "README.md"):
        for target in MARKDOWN_LINK.findall(document.read_text()):
            path_text = target.split("#", 1)[0]
            if not path_text or "://" in path_text:
                continue
            assert (document.parent / path_text).resolve().exists(), (
                f"broken local link {target!r} in {document}"
            )
