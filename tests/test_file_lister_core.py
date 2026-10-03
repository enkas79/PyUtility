"""Test della logica di business del modulo File Lister (nessuna dipendenza Qt)."""

import csv
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from file_lister_core import (  # noqa: E402
    FileEntry,
    FileListOptions,
    export_csv,
    export_txt,
    format_size,
    parse_extensions,
    parse_size,
    scan_folder,
)


def _crea_file(path: Path, size: int) -> Path:
    """Crea un file di test con la dimensione indicata in byte."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


@pytest.fixture()
def albero(tmp_path: Path) -> Path:
    """Struttura di prova: file in root e in una sottocartella."""
    _crea_file(tmp_path / "a.pdf", 100)
    _crea_file(tmp_path / "b.PDF", 2048)
    _crea_file(tmp_path / "c.txt", 10)
    _crea_file(tmp_path / "noext", 5)
    _crea_file(tmp_path / "sub" / "d.pdf", 5000)
    _crea_file(tmp_path / "sub" / "e.jpg", 300)
    return tmp_path


# ---------- parse_extensions ----------

@pytest.mark.parametrize("raw, atteso", [
    ("", frozenset()),
    ("   ", frozenset()),
    ("*", frozenset()),
    ("pdf", frozenset({".pdf"})),
    (".PDF, docx ; *.Txt", frozenset({".pdf", ".docx", ".txt"})),
    ("pdf pdf", frozenset({".pdf"})),
])
def test_parse_extensions(raw: str, atteso: frozenset) -> None:
    assert parse_extensions(raw) == atteso


# ---------- parse_size / format_size ----------

@pytest.mark.parametrize("raw, atteso", [
    ("", None),
    ("0", 0),
    ("1024", 1024),
    ("1 KB", 1024),
    ("1.5k", 1536),
    ("2MB", 2 * 1024 ** 2),
    ("1,5 mb", int(1.5 * 1024 ** 2)),
    ("1g", 1024 ** 3),
    ("3 B", 3),
])
def test_parse_size(raw: str, atteso: object) -> None:
    assert parse_size(raw) == atteso


@pytest.mark.parametrize("raw", ["abc", "-1", "10 XB", "1..2"])
def test_parse_size_invalido(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_size(raw)


@pytest.mark.parametrize("size, atteso", [
    (0, "0 B"),
    (512, "512 B"),
    (1024, "1.00 KB"),
    (1536, "1.50 KB"),
    (5 * 1024 ** 3, "5.00 GB"),
])
def test_format_size(size: int, atteso: str) -> None:
    assert format_size(size) == atteso


# ---------- FileListOptions ----------

def test_options_range_size_invalido() -> None:
    with pytest.raises(ValueError):
        FileListOptions(folder=".", min_size=100, max_size=10)


# ---------- scan_folder ----------

def _nomi(entries: list) -> set:
    return {e.name for e in entries}


def test_scan_ricorsivo_senza_filtri(albero: Path) -> None:
    entries = list(scan_folder(FileListOptions(folder=str(albero))))
    assert _nomi(entries) == {"a.pdf", "b.PDF", "c.txt", "noext", "d.pdf", "e.jpg"}


def test_scan_non_ricorsivo(albero: Path) -> None:
    entries = list(scan_folder(FileListOptions(folder=str(albero), recursive=False)))
    assert _nomi(entries) == {"a.pdf", "b.PDF", "c.txt", "noext"}


def test_scan_filtro_estensione_case_insensitive(albero: Path) -> None:
    opts = FileListOptions(folder=str(albero), extensions=parse_extensions("pdf"))
    assert _nomi(scan_folder(opts)) == {"a.pdf", "b.PDF", "d.pdf"}


def test_scan_filtro_size(albero: Path) -> None:
    opts = FileListOptions(folder=str(albero), min_size=100, max_size=2048)
    assert _nomi(scan_folder(opts)) == {"a.pdf", "b.PDF", "e.jpg"}


def test_scan_filtri_combinati(albero: Path) -> None:
    opts = FileListOptions(
        folder=str(albero), extensions=frozenset({".pdf"}), min_size=1000
    )
    assert _nomi(scan_folder(opts)) == {"b.PDF", "d.pdf"}


def test_scan_popola_metadati(albero: Path) -> None:
    opts = FileListOptions(folder=str(albero), extensions=frozenset({".jpg"}))
    (entry,) = list(scan_folder(opts))
    assert entry.size == 300
    assert entry.extension == ".jpg"
    assert entry.relative_path == os.path.join("sub", "e.jpg")
    assert os.path.isabs(entry.path)
    assert entry.modified > 0


def test_scan_annullamento(albero: Path) -> None:
    entries = list(scan_folder(FileListOptions(folder=str(albero)), should_stop=lambda: True))
    assert entries == []


def test_scan_cartella_inesistente(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        list(scan_folder(FileListOptions(folder=str(tmp_path / "manca"))))


# ---------- export ----------

def _entries_di_prova() -> list:
    return [
        FileEntry("a.pdf", "/x/a.pdf", "a.pdf", ".pdf", 100, 1_700_000_000.0),
        FileEntry("b;c.txt", "/x/s/b;c.txt", "s/b;c.txt", ".txt", 2048, 1_700_000_000.0),
    ]


def test_export_csv(tmp_path: Path) -> None:
    out = tmp_path / "lista.csv"
    export_csv(_entries_di_prova(), str(out))
    with open(out, encoding="utf-8-sig", newline="") as f:
        righe = list(csv.reader(f, delimiter=";"))
    assert righe[0] == ["Nome", "Estensione", "Dimensione (byte)", "Dimensione",
                        "Ultima modifica", "Percorso relativo", "Percorso completo"]
    assert righe[1][0] == "a.pdf"
    assert righe[2][0] == "b;c.txt"  # il separatore nel nome viene quotato correttamente
    assert righe[2][2] == "2048"
    assert len(righe) == 3


def test_export_txt(tmp_path: Path) -> None:
    out = tmp_path / "lista.txt"
    export_txt(_entries_di_prova(), str(out))
    righe = out.read_text(encoding="utf-8").splitlines()
    assert righe == ["/x/a.pdf", "/x/s/b;c.txt"]
