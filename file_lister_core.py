"""
File Lister Core
================
Logica di business (senza dipendenze Qt) per generare l'elenco dei file
contenuti in una cartella, con filtri per estensione e dimensione,
ed esportazione in CSV o TXT.
"""

import csv
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, FrozenSet, Iterable, Iterator, List, Optional

# Moltiplicatori (base 1024) accettati da parse_size
_SIZE_UNITS = {
    "": 1, "b": 1,
    "k": 1024, "kb": 1024,
    "m": 1024 ** 2, "mb": 1024 ** 2,
    "g": 1024 ** 3, "gb": 1024 ** 3,
    "t": 1024 ** 4, "tb": 1024 ** 4,
}
_SIZE_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]*)\s*$")

CSV_HEADER = [
    "Nome", "Estensione", "Dimensione (byte)", "Dimensione",
    "Ultima modifica", "Percorso relativo", "Percorso completo",
]


@dataclass(frozen=True)
class FileEntry:
    """Singolo file trovato durante la scansione."""
    name: str
    path: str
    relative_path: str
    extension: str
    size: int
    modified: float

    @property
    def modified_str(self) -> str:
        """Data di ultima modifica in formato leggibile."""
        return datetime.fromtimestamp(self.modified).strftime("%Y-%m-%d %H:%M")


@dataclass(frozen=True)
class FileListOptions:
    """
    Parametri della scansione.

    Attributes:
        folder: Cartella da analizzare.
        extensions: Estensioni ammesse in minuscolo con punto (vuoto = tutte).
        min_size: Dimensione minima in byte (inclusa), None = nessun limite.
        max_size: Dimensione massima in byte (inclusa), None = nessun limite.
        recursive: Se True include le sottocartelle.
        include_hidden: Se True include file e cartelle nascosti (prefisso '.').
    """
    folder: str
    extensions: FrozenSet[str] = field(default_factory=frozenset)
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    recursive: bool = True
    include_hidden: bool = False

    def __post_init__(self) -> None:
        if (self.min_size is not None and self.max_size is not None
                and self.min_size > self.max_size):
            raise ValueError("La dimensione minima supera quella massima.")

    def matches(self, extension: str, size: int) -> bool:
        """Verifica se un file rispetta i filtri di estensione e dimensione."""
        if self.extensions and extension not in self.extensions:
            return False
        if self.min_size is not None and size < self.min_size:
            return False
        if self.max_size is not None and size > self.max_size:
            return False
        return True


def parse_extensions(raw: str) -> FrozenSet[str]:
    """
    Converte un testo libero (es. "pdf, .DOCX; *.txt") in un set normalizzato
    di estensioni {".pdf", ".docx", ".txt"}. Vuoto o "*" = nessun filtro.
    """
    result = set()
    for token in re.split(r"[\s,;]+", raw.strip()):
        token = token.lstrip("*").strip().lower()
        if not token or token == ".":
            continue
        result.add(token if token.startswith(".") else f".{token}")
    return frozenset(result)


def parse_size(raw: str) -> Optional[int]:
    """
    Converte una dimensione testuale (es. "1.5 MB", "200k", "1024") in byte.
    Restituisce None per stringa vuota. Solleva ValueError se non valida.
    """
    if not raw or not raw.strip():
        return None
    match = _SIZE_RE.match(raw)
    if not match:
        raise ValueError(f"Dimensione non valida: '{raw}'")
    number, unit = match.groups()
    multiplier = _SIZE_UNITS.get(unit.lower())
    if multiplier is None:
        raise ValueError(f"Unità di misura non riconosciuta: '{unit}'")
    return int(float(number.replace(",", ".")) * multiplier)


def format_size(size: int) -> str:
    """Formatta una dimensione in byte in forma leggibile (B, KB, MB, GB, TB)."""
    if size < 1024:
        return f"{size} B"
    value = float(size)
    for unit in ("KB", "MB", "GB", "TB"):
        value /= 1024
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"
    return f"{size} B"  # irraggiungibile, per il type checker


def scan_folder(
    options: FileListOptions,
    should_stop: Callable[[], bool] = lambda: False,
) -> Iterator[FileEntry]:
    """
    Scansiona la cartella con os.scandir (una sola stat per file) e restituisce
    i file che rispettano i filtri. Le cartelle non accessibili vengono saltate.

    Raises:
        NotADirectoryError: se options.folder non è una cartella esistente.
    """
    root = os.path.abspath(options.folder)
    if not os.path.isdir(root):
        raise NotADirectoryError(f"Cartella non trovata: {options.folder}")

    stack: List[str] = [root]
    while stack:
        if should_stop():
            return
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                entries = sorted(it, key=lambda e: e.name.lower())
        except OSError:
            continue  # permessi negati o cartella rimossa durante la scansione

        subdirs: List[str] = []
        for entry in entries:
            if should_stop():
                return
            if not options.include_hidden and entry.name.startswith("."):
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    if options.recursive:
                        subdirs.append(entry.path)
                    continue
                if not entry.is_file():
                    continue
                stat = entry.stat()
            except OSError:
                continue

            extension = os.path.splitext(entry.name)[1].lower()
            if not options.matches(extension, stat.st_size):
                continue
            yield FileEntry(
                name=entry.name,
                path=entry.path,
                relative_path=os.path.relpath(entry.path, root),
                extension=extension,
                size=stat.st_size,
                modified=stat.st_mtime,
            )
        # Ordine inverso così le sottocartelle vengono visitate in ordine alfabetico
        stack.extend(reversed(subdirs))


def export_csv(entries: Iterable[FileEntry], dest_path: str) -> None:
    """Esporta l'elenco in CSV (separatore ';', UTF-8 con BOM per Excel)."""
    with open(dest_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(CSV_HEADER)
        for e in entries:
            writer.writerow([
                e.name, e.extension, e.size, format_size(e.size),
                e.modified_str, e.relative_path, e.path,
            ])


def export_txt(entries: Iterable[FileEntry], dest_path: str) -> None:
    """Esporta l'elenco in TXT: un percorso completo per riga."""
    with open(dest_path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(f"{e.path}\n")
