"""
PDF Core
========
Logica di business dei tool PDF (nessuna dipendenza Qt):
unione con divisione per dimensione (PDF_plus), divisione (PDF_Splitter)
e conversione in Word (PDFtoWord).
Nessuna funzione sovrascrive file esistenti.
"""

import os
from typing import Callable, List, Optional, Tuple

from PyPDF2 import PdfReader, PdfWriter

from file_lister_core import unique_destination

DEFAULT_MAX_SIZE = 99 * 1024 * 1024  # 99 MB

ProgressCallback = Callable[[int, int], None]  # (elementi elaborati, totale)


def open_pdf(path: str) -> PdfReader:
    """
    Apre un PDF; quelli cifrati senza password utente vengono sbloccati,
    gli altri generano un errore chiaro.

    Raises:
        ValueError: PDF protetto da password o non valido.
    """
    try:
        reader = PdfReader(path)
        locked = reader.is_encrypted and not reader.decrypt("")
    except Exception as e:  # noqa: BLE001 - PyPDF2 solleva tipi eterogenei
        raise ValueError(f"'{os.path.basename(path)}' non è un PDF valido: {e}") from e
    if locked:
        raise ValueError(f"'{os.path.basename(path)}' è protetto da password.")
    return reader


def _write(writer: PdfWriter, path: str) -> str:
    with open(path, "wb") as f:
        writer.write(f)
    return path


def _stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


# ------------------------------------------------------------ unione
def _next_main_path(dest_dir: str, counter: int) -> Tuple[str, int]:
    """Primo 'NN - Main.pdf' libero a partire da counter."""
    while os.path.exists(os.path.join(dest_dir, f"{counter:02d} - Main.pdf")):
        counter += 1
    return os.path.join(dest_dir, f"{counter:02d} - Main.pdf"), counter


def merge_pdfs(files: List[str], dest_dir: str, max_size: int = DEFAULT_MAX_SIZE,
               on_progress: Optional[ProgressCallback] = None) -> List[str]:
    """
    Unisce i PDF in 'NN - Main.pdf'; si passa a un nuovo file quando la somma
    delle dimensioni dei sorgenti supera max_size. È una stima: un singolo
    sorgente più grande del limite produce comunque un file più grande.

    Returns:
        List[str]: Percorsi dei file creati.
    """
    if not files:
        raise ValueError("Nessun PDF da unire.")
    created: List[str] = []
    writer = PdfWriter()
    current_size = 0
    counter = 1

    for n, path in enumerate(files, start=1):
        reader = open_pdf(path)
        size = os.path.getsize(path)
        if current_size + size > max_size and len(writer.pages) > 0:
            out, counter = _next_main_path(dest_dir, counter)
            created.append(_write(writer, out))
            writer = PdfWriter()
            current_size = 0
        for page in reader.pages:
            writer.add_page(page)
        current_size += size
        if on_progress is not None:
            on_progress(n, len(files))

    if len(writer.pages) > 0:
        out, counter = _next_main_path(dest_dir, counter)
        created.append(_write(writer, out))
    return created


# ------------------------------------------------------------ divisione
def split_single(pdf_path: str, out_dir: str,
                 on_progress: Optional[ProgressCallback] = None) -> List[str]:
    """Un file per ogni pagina: '<nome>_pagina_N.pdf'."""
    reader = open_pdf(pdf_path)
    total = len(reader.pages)
    created: List[str] = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        created.append(_write(writer, unique_destination(out_dir, f"{_stem(pdf_path)}_pagina_{i}.pdf")))
        if on_progress is not None:
            on_progress(i, total)
    return created


def split_range(pdf_path: str, out_dir: str, start: int, end: int) -> str:
    """
    Estrae le pagine start..end (1-based, inclusive) in un unico file;
    una fine oltre il totale viene troncata.

    Raises:
        ValueError: intervallo non valido.
    """
    reader = open_pdf(pdf_path)
    total = len(reader.pages)
    end = min(end, total)
    if start < 1 or start > end:
        raise ValueError(f"Intervallo di pagine non valido (il documento ha {total} pagine).")
    writer = PdfWriter()
    for i in range(start - 1, end):
        writer.add_page(reader.pages[i])
    return _write(writer, unique_destination(out_dir, f"{_stem(pdf_path)}_pagine_{start}-{end}.pdf"))


def split_every(pdf_path: str, out_dir: str, pages_per_file: int,
                on_progress: Optional[ProgressCallback] = None) -> List[str]:
    """Blocchi di N pagine: '<nome>_parte_K.pdf' (l'ultimo può essere più corto)."""
    if pages_per_file < 1:
        raise ValueError("Il numero di pagine per file deve essere almeno 1.")
    reader = open_pdf(pdf_path)
    total = len(reader.pages)
    created: List[str] = []
    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        writer.add_page(page)
        if i % pages_per_file == 0 or i == total:
            name = f"{_stem(pdf_path)}_parte_{len(created) + 1}.pdf"
            created.append(_write(writer, unique_destination(out_dir, name)))
            writer = PdfWriter()
        if on_progress is not None:
            on_progress(i, total)
    return created


# ------------------------------------------------------------ PDF -> Word
def docx_output_path(pdf_path: str) -> str:
    """Percorso .docx libero accanto al PDF (gestisce '.PDF' e non sovrascrive)."""
    return unique_destination(os.path.dirname(pdf_path), _stem(pdf_path) + ".docx")


def convert_pdf_to_docx(pdf_path: str, docx_path: str) -> str:
    """Converte il PDF in .docx; il convertitore viene chiuso anche in caso di errore."""
    from pdf2docx import Converter  # import lazy: dipendenza pesante (PyMuPDF)

    converter = Converter(pdf_path)
    try:
        converter.convert(docx_path)
    finally:
        converter.close()
    return docx_path
