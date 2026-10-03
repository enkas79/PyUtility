"""
File Lister Core
================
Logica di business (senza dipendenze Qt) per generare l'elenco dei file
contenuti in una cartella, con filtri per estensione, dimensione e parola
chiave, esportazione in CSV/TXT e copia/spostamento sicuro dei file.
"""

import csv
import os
import re
import shutil
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
        keyword: Testo che deve comparire nel nome file (case-insensitive, vuoto = tutti).
    """
    folder: str
    extensions: FrozenSet[str] = field(default_factory=frozenset)
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    recursive: bool = True
    include_hidden: bool = False
    keyword: str = ""

    def __post_init__(self) -> None:
        # Normalizzazione una sola volta (dataclass frozen: si usa object.__setattr__)
        object.__setattr__(self, "keyword", self.keyword.strip().lower())
        if (self.min_size is not None and self.max_size is not None
                and self.min_size > self.max_size):
            raise ValueError("La dimensione minima supera quella massima.")

    def matches_name(self, name: str, extension: str) -> bool:
        """Filtri che non richiedono stat(): parola chiave ed estensione."""
        if self.keyword and self.keyword not in name.lower():
            return False
        return not self.extensions or extension in self.extensions

    def matches_size(self, size: int) -> bool:
        """Filtro sulla dimensione (limiti inclusivi)."""
        if self.min_size is not None and size < self.min_size:
            return False
        return self.max_size is None or size <= self.max_size

    def matches(self, extension: str, size: int, name: str = "") -> bool:
        """Verifica se un file rispetta tutti i filtri."""
        return self.matches_name(name, extension) and self.matches_size(size)

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
                # Filtri sul nome prima di stat(): evita syscall per i file scartati
                extension = os.path.splitext(entry.name)[1].lower()
                if not options.matches_name(entry.name, extension):
                    continue
                stat = entry.stat()
            except OSError:
                continue

            if not options.matches_size(stat.st_size):
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


@dataclass
class TransferResult:
    """Esito di un'operazione di copia/spostamento."""
    done: int = 0
    errors: List[str] = field(default_factory=list)
    completed_sources: List[str] = field(default_factory=list)


def unique_destination(dest_dir: str, name: str) -> str:
    """
    Restituisce un percorso libero in dest_dir per il file 'name',
    aggiungendo un suffisso ' (n)' in caso di omonimia (nessuna sovrascrittura).
    """
    candidate = os.path.join(dest_dir, name)
    stem, ext = os.path.splitext(name)
    n = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_dir, f"{stem} ({n}){ext}")
        n += 1
    return candidate


def transfer_files(
    sources: Iterable[str],
    dest_dir: str,
    mode: str,
    should_stop: Callable[[], bool] = lambda: False,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> TransferResult:
    """
    Copia ('copy') o sposta ('move') i file in dest_dir senza sovrascrivere.
    Gli errori sui singoli file vengono raccolti senza interrompere l'operazione.

    Raises:
        ValueError: modalità non valida.
        NotADirectoryError: cartella di destinazione inesistente.
    """
    if mode not in ("copy", "move"):
        raise ValueError(f"Modalità non valida: '{mode}'")
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Cartella di destinazione non trovata: {dest_dir}")

    sources = list(sources)
    result = TransferResult()
    for index, src in enumerate(sources, start=1):
        if should_stop():
            break
        try:
            dest = unique_destination(dest_dir, os.path.basename(src))
            if mode == "move":
                shutil.move(src, dest)
            else:
                shutil.copy2(src, dest)
            result.done += 1
            result.completed_sources.append(src)
        except (OSError, shutil.Error) as e:
            result.errors.append(f"{src}: {e}")
        if on_progress is not None:
            on_progress(index, len(sources))
    return result
