"""Verifica la coerenza tra il registro TOOLS di MainSuite e il workflow PyInstaller."""

import ast
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent


def _tool_modules() -> List[str]:
    """Estrae i nomi dei moduli da TOOLS via AST (senza importare PyQt6)."""
    tree = ast.parse((ROOT / "MainSuite.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "TOOLS":
            return [ast.literal_eval(elt)[1] for elt in node.value.elts]
    raise AssertionError("TOOLS non trovato in MainSuite.py")


def test_ogni_tool_esiste_su_disco() -> None:
    for module in _tool_modules():
        assert (ROOT / f"{module}.py").is_file(), module


def test_ogni_tool_dichiarato_come_hidden_import() -> None:
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    for module in _tool_modules():
        # Una volta per il job Windows e una per il job Linux
        assert workflow.count(f"--hidden-import {module} ") == 2, module


def test_icone_presenti_e_dichiarate_nel_workflow() -> None:
    for rel in ("icon.ico", "assets/icon.png", "assets/icon.svg"):
        assert (ROOT / rel).is_file(), rel
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    assert "--icon icon.ico" in workflow
    assert '--add-data "assets/icon.png;assets"' in workflow  # Windows
    assert '--add-data "assets/icon.png:assets"' in workflow  # Linux
