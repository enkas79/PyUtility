"""Test di copia/spostamento file (logica usata da Find_Document)."""

from pathlib import Path

import pytest

from file_lister_core import transfer_files, unique_destination


def test_unique_destination_libera(tmp_path: Path) -> None:
    assert unique_destination(str(tmp_path), "a.pdf") == str(tmp_path / "a.pdf")


def test_unique_destination_con_collisioni(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_text("1")
    (tmp_path / "a (1).pdf").write_text("2")
    assert unique_destination(str(tmp_path), "a.pdf") == str(tmp_path / "a (2).pdf")


@pytest.fixture()
def sorgenti(tmp_path: Path) -> list:
    src = tmp_path / "src"
    src.mkdir()
    files = []
    for name in ("a.txt", "b.txt"):
        f = src / name
        f.write_text(name)
        files.append(str(f))
    return files


def test_copia_non_sovrascrive(tmp_path: Path, sorgenti: list) -> None:
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "a.txt").write_text("originale")
    result = transfer_files(sorgenti, str(dst), "copy")
    assert result.done == 2 and not result.errors
    assert (dst / "a.txt").read_text() == "originale"
    assert (dst / "a (1).txt").read_text() == "a.txt"
    assert all(Path(p).exists() for p in sorgenti)
    assert result.completed_sources == sorgenti


def test_sposta(tmp_path: Path, sorgenti: list) -> None:
    dst = tmp_path / "dst"
    dst.mkdir()
    progress = []
    result = transfer_files(sorgenti, str(dst), "move", on_progress=lambda i, n: progress.append((i, n)))
    assert result.done == 2
    assert not any(Path(p).exists() for p in sorgenti)
    assert {p.name for p in dst.iterdir()} == {"a.txt", "b.txt"}
    assert progress == [(1, 2), (2, 2)]


def test_errori_raccolti_senza_interrompere(tmp_path: Path, sorgenti: list) -> None:
    dst = tmp_path / "dst"
    dst.mkdir()
    result = transfer_files([str(tmp_path / "manca.txt")] + sorgenti, str(dst), "copy")
    assert result.done == 2
    assert len(result.errors) == 1 and "manca.txt" in result.errors[0]


def test_annullamento(tmp_path: Path, sorgenti: list) -> None:
    dst = tmp_path / "dst"
    dst.mkdir()
    result = transfer_files(sorgenti, str(dst), "copy", should_stop=lambda: True)
    assert result.done == 0 and list(dst.iterdir()) == []


def test_modalita_non_valida(tmp_path: Path, sorgenti: list) -> None:
    with pytest.raises(ValueError):
        transfer_files(sorgenti, str(tmp_path), "delete")


def test_destinazione_inesistente(tmp_path: Path, sorgenti: list) -> None:
    with pytest.raises(NotADirectoryError):
        transfer_files(sorgenti, str(tmp_path / "manca"), "copy")
