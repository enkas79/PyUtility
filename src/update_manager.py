"""
Update Manager
==============
Livello Qt dell'autoupdate: thread di verifica/download e dialoghi.
La logica (API, versioni, download) è nel modulo updater.
"""

import logging
import os
import tempfile
from typing import Optional

from PyQt6.QtCore import QObject, Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QWidget

from app_info import FALLBACK_DOWNLOAD_URL, REPO_NAME, REPO_OWNER, get_app_version, user_data_dir
from updater import (
    ReleaseAsset,
    ReleaseInfo,
    UpdateCancelled,
    download_asset,
    fetch_latest_release,
    is_newer,
    launch_installer,
    select_asset,
)

logger = logging.getLogger(__name__)


class UpdateCheckWorker(QThread):
    """Interroga GitHub Releases in background."""
    found = pyqtSignal(object)  # ReleaseInfo
    failed = pyqtSignal(str)

    def __init__(self, owner: str, repo: str) -> None:
        super().__init__()
        self.owner = owner
        self.repo = repo

    def run(self) -> None:
        try:
            self.found.emit(fetch_latest_release(self.owner, self.repo))
        except (OSError, ValueError) as e:
            logger.info("Verifica aggiornamenti non riuscita: %s", e)
            self.failed.emit(str(e))


class DownloadWorker(QThread):
    """Scarica l'installer in background con progresso e annullamento."""
    progress = pyqtSignal(int, int)  # (byte scaricati, totale)
    done = pyqtSignal(str)           # percorso del file
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, asset: ReleaseAsset, dest_dir: str) -> None:
        super().__init__()
        self.asset = asset
        self.dest_dir = dest_dir
        self._stop = False

    def run(self) -> None:
        try:
            path = download_asset(self.asset, self.dest_dir,
                                  on_progress=self.progress.emit,
                                  should_stop=lambda: self._stop)
            self.done.emit(path)
        except UpdateCancelled:
            self.cancelled.emit()
        except (OSError, ValueError) as e:
            logger.error("Download aggiornamento fallito: %s", e, exc_info=True)
            self.failed.emit(str(e))

    def stop(self) -> None:
        """Richiede l'interruzione cooperativa del download."""
        self._stop = True


class UpdateController(QObject):
    """
    Coordina verifica, notifica, download e installazione degli aggiornamenti
    per la finestra 'parent'. Una sola operazione alla volta.
    """

    def __init__(self, parent: QWidget, current_version: Optional[str] = None) -> None:
        super().__init__(parent)
        self._parent = parent
        self.current_version = current_version or get_app_version()
        self._silent = True
        self._check_worker: Optional[UpdateCheckWorker] = None
        self._download_worker: Optional[DownloadWorker] = None
        self._progress: Optional[QProgressDialog] = None

    # ------------------------------------------------------------ stato
    def is_busy(self) -> bool:
        return any(w is not None and w.isRunning()
                   for w in (self._check_worker, self._download_worker))

    # ------------------------------------------------------------ verifica
    def check(self, silent: bool = True) -> None:
        """Avvia la verifica; in modalità silenziosa notifica solo se c'è una nuova versione."""
        if self.is_busy():
            if not silent:
                QMessageBox.information(self._parent, "Aggiornamenti",
                                        "Una verifica o un download è già in corso.")
            return
        self._silent = silent
        self._check_worker = UpdateCheckWorker(REPO_OWNER, REPO_NAME)
        self._check_worker.found.connect(self._on_release_found)
        self._check_worker.failed.connect(self._on_check_failed)
        self._check_worker.start()

    def _on_check_failed(self, error: str) -> None:
        if not self._silent:
            QMessageBox.warning(self._parent, "Aggiornamenti",
                                f"Impossibile verificare gli aggiornamenti.\n\nDettagli: {error}")

    def _on_release_found(self, release: ReleaseInfo) -> None:
        if not is_newer(release.version, self.current_version):
            if not self._silent:
                QMessageBox.information(self._parent, "Nessun Aggiornamento",
                                        f"La suite è già aggiornata (v{self.current_version}).")
            return

        asset = select_asset(release)
        box = QMessageBox(self._parent)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Aggiornamento Disponibile")
        box.setText(f"È disponibile la versione <b>{release.version}</b> "
                    f"(installata: {self.current_version}).")
        if asset is not None:
            box.setInformativeText("Vuoi scaricarla e installarla ora?")
        else:
            box.setInformativeText("Installer non disponibile per questo sistema: "
                                   "vuoi aprire la pagina di download?")
        box.setDetailedText(release.changelog or "Nessuna nota di rilascio.")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.Yes)
        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        if asset is None:
            QDesktopServices.openUrl(QUrl(release.html_url or FALLBACK_DOWNLOAD_URL))
            return
        self._start_download(asset)

    # ------------------------------------------------------------ download
    def _start_download(self, asset: ReleaseAsset) -> None:
        dest_dir = os.path.join(user_data_dir(), "updates")
        if not _is_writable(dest_dir):
            dest_dir = os.path.join(tempfile.gettempdir(), "PyUtilitySuite_updates")

        self._progress = QProgressDialog(f"Download di {asset.name}...", "Annulla", 0, 100, self._parent)
        self._progress.setWindowTitle("Aggiornamento")
        self._progress.setWindowModality(Qt.WindowModality.NonModal)
        self._progress.setMinimumDuration(0)
        self._progress.setAutoClose(False)
        self._progress.setAutoReset(False)

        self._download_worker = DownloadWorker(asset, dest_dir)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.done.connect(self._on_download_done)
        self._download_worker.failed.connect(self._on_download_failed)
        self._download_worker.cancelled.connect(self._close_progress)
        self._progress.canceled.connect(self._download_worker.stop)
        self._download_worker.start()
        self._progress.show()

    def _on_download_progress(self, done: int, total: int) -> None:
        if self._progress is not None and total > 0:
            self._progress.setValue(int(done * 100 / total))

    def _close_progress(self) -> None:
        if self._progress is not None:
            self._progress.close()
            self._progress.deleteLater()
            self._progress = None

    def _on_download_failed(self, error: str) -> None:
        self._close_progress()
        QMessageBox.warning(self._parent, "Aggiornamento",
                            f"Download non riuscito.\n\nDettagli: {error}")

    def _on_download_done(self, path: str) -> None:
        self._close_progress()
        answer = QMessageBox.question(
            self._parent, "Aggiornamento pronto",
            "Download completato.\nL'applicazione verrà chiusa per avviare l'installazione. Procedere?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            QMessageBox.information(self._parent, "Aggiornamento",
                                    f"Installer salvato in:\n{path}")
            return
        try:
            launch_installer(path)
        except OSError as e:
            logger.error("Avvio installer fallito: %s", e, exc_info=True)
            QMessageBox.critical(self._parent, "Aggiornamento",
                                 f"Impossibile avviare l'installer.\nFile: {path}\n\nDettagli: {e}")
            return
        QApplication.quit()

    def shutdown(self) -> None:
        """Interrompe le operazioni in corso (chiusura della finestra)."""
        if self._download_worker is not None and self._download_worker.isRunning():
            self._download_worker.stop()
            self._download_worker.wait(3000)
        if self._check_worker is not None and self._check_worker.isRunning():
            self._check_worker.wait(3000)


def _is_writable(directory: str) -> bool:
    """True se la cartella esiste (o può essere creata) ed è scrivibile."""
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        return False
    return os.access(directory, os.W_OK)
