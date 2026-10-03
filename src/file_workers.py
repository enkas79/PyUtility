"""
File Workers
============
Thread Qt condivisi dai tool che lavorano su elenchi di file
(File_Lister, Find_Document). La logica vera e propria è in file_lister_core.
"""

import logging
from typing import Callable, List

from PyQt6.QtCore import QThread, pyqtSignal

from file_lister_core import FileEntry, FileListOptions, scan_folder, transfer_files

logger = logging.getLogger(__name__)

BATCH_SIZE = 250  # file inviati alla GUI per ogni segnale (riduce l'overhead)


class ScanWorker(QThread):
    """Esegue la scansione della cartella in background, inviando i risultati a blocchi."""
    batch_found = pyqtSignal(list)    # List[FileEntry]
    finished_scan = pyqtSignal(bool)  # True se annullata
    error = pyqtSignal(str)

    def __init__(self, options: FileListOptions) -> None:
        super().__init__()
        self.options = options
        self._stop = False

    def run(self) -> None:
        batch: List[FileEntry] = []
        try:
            for entry in scan_folder(self.options, should_stop=lambda: self._stop):
                batch.append(entry)
                if len(batch) >= BATCH_SIZE:
                    self.batch_found.emit(batch)
                    batch = []
            if batch:
                self.batch_found.emit(batch)
            self.finished_scan.emit(self._stop)
        except Exception as e:  # noqa: BLE001 - nessun crash del thread
            logger.error("Errore durante la scansione: %s", e, exc_info=True)
            self.error.emit(str(e))

    def stop(self) -> None:
        """Richiede l'interruzione cooperativa della scansione."""
        self._stop = True


class ExportWorker(QThread):
    """Scrive su disco l'elenco dei file in background."""
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, exporter: Callable[[List[FileEntry], str], None],
                 entries: List[FileEntry], dest_path: str) -> None:
        super().__init__()
        self.exporter = exporter
        self.entries = entries
        self.dest_path = dest_path

    def run(self) -> None:
        try:
            self.exporter(self.entries, self.dest_path)
            self.done.emit(self.dest_path)
        except OSError as e:
            logger.error("Errore durante l'esportazione: %s", e, exc_info=True)
            self.error.emit(str(e))


class TransferWorker(QThread):
    """Copia o sposta file in background senza sovrascrivere."""
    progress = pyqtSignal(int, int)           # (file elaborati, totale)
    done = pyqtSignal(int, list, list)        # (riusciti, sorgenti completate, errori)
    error = pyqtSignal(str)

    def __init__(self, sources: List[str], dest_dir: str, mode: str) -> None:
        super().__init__()
        self.sources = sources
        self.dest_dir = dest_dir
        self.mode = mode
        self._stop = False

    def run(self) -> None:
        try:
            result = transfer_files(
                self.sources, self.dest_dir, self.mode,
                should_stop=lambda: self._stop,
                on_progress=self.progress.emit,
            )
            self.done.emit(result.done, result.completed_sources, result.errors)
        except Exception as e:  # noqa: BLE001 - nessun crash del thread
            logger.error("Errore durante il trasferimento: %s", e, exc_info=True)
            self.error.emit(str(e))

    def stop(self) -> None:
        """Interrompe l'operazione dopo il file corrente."""
        self._stop = True
