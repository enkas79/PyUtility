"""Verifica la coerenza tra il registro TOOLS di src/main.py e il workflow PyInstaller."""

import ast
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
WORKFLOW = ROOT / ".github" / "workflows" / "build-installers.yml"


def _tool_modules() -> List[str]:
    """Estrae i nomi dei moduli da TOOLS via AST (senza importare PyQt6)."""
    tree = ast.parse((SRC / "main.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "TOOLS":
            return [ast.literal_eval(elt)[1] for elt in node.value.elts]
    raise AssertionError("TOOLS non trovato in src/main.py")


def test_ogni_tool_esiste_su_disco() -> None:
    for module in _tool_modules():
        assert (SRC / f"{module}.py").is_file(), module


def test_ogni_tool_dichiarato_come_hidden_import() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for module in _tool_modules():
        # Una volta per il job Windows e una per il job Linux
        assert workflow.count(f"--hidden-import {module} ") == 2, module


def test_icone_presenti_e_dichiarate_nel_workflow() -> None:
    for rel in ("icon.ico", "assets/icon.png", "assets/icon.svg"):
        assert (ROOT / rel).is_file(), rel
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "--icon icon.ico" in workflow
    assert '--add-data "assets/icon.png;assets"' in workflow  # Windows
    assert '--add-data "assets/icon.png:assets"' in workflow  # Linux


def test_entry_point_e_versione() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count('assets" src/main.py') == 2  # entry point di PyInstaller
    assert workflow.count("--paths src") == 2
    assert "'version.txt'" in workflow  # trigger della build
    assert (ROOT / "version.txt").read_text(encoding="utf-8").strip().count(".") == 2


def test_build_dipende_dai_test_e_usa_requirements() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "uses: ./.github/workflows/tests.yml" in workflow
    assert workflow.count("needs: tests") == 2
    assert workflow.count("pip install -r requirements.txt") == 2
    assert "pip install PyQt6" not in workflow  # niente versioni libere


def test_checksum_pubblicati_per_ogni_installer() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "_Setup_v${{ env.VERSION }}.exe.sha256" in workflow
    assert "_amd64.deb.sha256" in workflow
    assert "sha256sum" in workflow and "Get-FileHash -Algorithm SHA256" in workflow


def test_requirements_tutte_fissate() -> None:
    lines = [ln.strip() for ln in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()]
    deps = [ln for ln in lines if ln and not ln.startswith("#")]
    assert deps and all("==" in d for d in deps), deps
