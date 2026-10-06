"""Test della logica PDF (unione, divisione, percorso docx) senza Qt."""

from pathlib import Path
from typing import List

import pytest
from PyPDF2 import PdfReader, PdfWriter

from pdf_core import (
    docx_output_path,
    merge_pdfs,
    split_every,
    split_range,
    split_single,
)


def _pdf(path: Path, pages: int, password: str = "") -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=100, height=100)
    if password:
        writer.encrypt(password)
    with open(path, "wb") as f:
        writer.write(f)
    return path


def _pages(path: str) -> int:
    return len(PdfReader(path).pages)


# ------------------------------------------------------------ unione
def test_merge_pdfs_unico_file(tmp_path: Path) -> None:
    files = [str(_pdf(tmp_path / f"{i}.pdf", i + 1)) for i in range(3)]
    out = tmp_path / "out"
    out.mkdir()
    created = merge_pdfs(files, str(out))
    assert [Path(p).name for p in created] == ["01 - Main.pdf"]
    assert _pages(created[0]) == 6


def test_merge_pdfs_split_per_dimensione(tmp_path: Path) -> None:
    files = [str(_pdf(tmp_path / f"{i}.pdf", 1)) for i in range(3)]
    out = tmp_path / "out"
    out.mkdir()
    one_file = Path(files[0]).stat().st_size
    created = merge_pdfs(files, str(out), max_size=one_file + 1)
    assert len(created) == 3
    assert all(_pages(p) == 1 for p in created)


def test_merge_pdfs_non_sovrascrive_numerazione_esistente(tmp_path: Path) -> None:
    # Bug v1.5.0: con '02 - Main.pdf' già presente, il secondo blocco lo sovrascriveva
    out = tmp_path / "out"
    out.mkdir()
    (out / "02 - Main.pdf").write_bytes(b"esistente")
    files = [str(_pdf(tmp_path / f"{i}.pdf", 1)) for i in range(2)]
    created = merge_pdfs(files, str(out), max_size=1)
    assert [Path(p).name for p in created] == ["01 - Main.pdf", "03 - Main.pdf"]
    assert (out / "02 - Main.pdf").read_bytes() == b"esistente"


def test_merge_pdfs_protetto_da_password(tmp_path: Path) -> None:
    files = [str(_pdf(tmp_path / "p.pdf", 1, password="segreta"))]
    with pytest.raises(ValueError, match="password"):
        merge_pdfs(files, str(tmp_path))


def test_merge_pdfs_lista_vuota(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        merge_pdfs([], str(tmp_path))


# ------------------------------------------------------------ divisione
def test_split_single(tmp_path: Path) -> None:
    src = _pdf(tmp_path / "doc.pdf", 3)
    progress: List[int] = []
    created = split_single(str(src), str(tmp_path), on_progress=lambda d, t: progress.append(d))
    assert [Path(p).name for p in created] == [f"doc_pagina_{i}.pdf" for i in (1, 2, 3)]
    assert progress == [1, 2, 3]


def test_split_single_non_sovrascrive(tmp_path: Path) -> None:
    src = _pdf(tmp_path / "doc.pdf", 1)
    first = split_single(str(src), str(tmp_path))
    second = split_single(str(src), str(tmp_path))
    assert first != second
    assert Path(second[0]).name == "doc_pagina_1 (1).pdf"


@pytest.mark.parametrize("start, end, expected_pages, name", [
    (2, 4, 3, "doc_pagine_2-4.pdf"),
    (3, 3, 1, "doc_pagine_3-3.pdf"),
    (4, 99, 2, "doc_pagine_4-5.pdf"),  # fine oltre il totale: troncata
])
def test_split_range(tmp_path: Path, start: int, end: int, expected_pages: int, name: str) -> None:
    src = _pdf(tmp_path / "doc.pdf", 5)
    created = split_range(str(src), str(tmp_path), start, end)
    assert Path(created).name == name
    assert _pages(created) == expected_pages


@pytest.mark.parametrize("start, end", [(4, 2), (6, 8), (0, 0)])
def test_split_range_non_valido(tmp_path: Path, start: int, end: int) -> None:
    src = _pdf(tmp_path / "doc.pdf", 5)
    with pytest.raises(ValueError):
        split_range(str(src), str(tmp_path), start, end)


def test_split_every(tmp_path: Path) -> None:
    src = _pdf(tmp_path / "doc.pdf", 5)
    created = split_every(str(src), str(tmp_path), 2)
    assert [_pages(p) for p in created] == [2, 2, 1]
    assert Path(created[-1]).name == "doc_parte_3.pdf"


def test_split_every_n_non_valido(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        split_every(str(_pdf(tmp_path / "doc.pdf", 2)), str(tmp_path), 0)


# ------------------------------------------------------------ PDF -> Word
@pytest.mark.parametrize("name, expected", [
    ("Doc.PDF", "Doc.docx"),
    ("cartella.pdf.vecchia.pdf", "cartella.pdf.vecchia.docx"),
])
def test_docx_output_path(tmp_path: Path, name: str, expected: str) -> None:
    assert Path(docx_output_path(str(tmp_path / name))).name == expected


def test_docx_output_path_non_sovrascrive(tmp_path: Path) -> None:
    (tmp_path / "Doc.docx").write_bytes(b"esistente")
    assert Path(docx_output_path(str(tmp_path / "Doc.pdf"))).name == "Doc (1).docx"
