import importlib
import json
import os
import sys
import urllib.request
from typing import Dict, List, Tuple

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QIcon

# Import moduli di base
from base_window import get_app_version, logger, resource_path
from styles import get_style

# --- CONFIGURAZIONE DINAMICA ---
VERSION = get_app_version()
AUTHOR = "Enrico Martini"
REPO_OWNER = "enkas79"
REPO_NAME = "PyUtility"

# Registro dei tool: (etichetta pulsante, modulo, classe finestra).
# I moduli sono importati solo all'apertura: una dipendenza mancante in un tool
# non impedisce più l'uso degli altri (prima un unico try/except li bloccava tutti).
# NB: ogni modulo va dichiarato con --hidden-import nel workflow PyInstaller.
TOOLS: List[Tuple[str, str, str]] = [
    ("🖼️ Image Converter/Resizer", "ConvImage", "ImageResizerApp"),
    ("🧩 Image Merger (Unisci Immagini)", "MergeImage", "ImageMergerApp"),
    ("🎨 Image Watermark", "Image_Watermark", "WatermarkApp"),
    ("🔍 Ricerca/Gestione Documenti", "Find_Document", "FileManagerApp"),
    ("📋 Lista File Cartella", "File_Lister", "FileListerApp"),
    ("📄 PDF Plus (Unione PDF)", "PDF_plus", "PDFPlusPro"),
    ("✂️ PDF Splitter", "PDF_Splitter", "PDFSplitterApp"),
    ("📝 PDF to Word Converter", "PDFtoWord", "ModernConverter"),
]


# ==========================================
# LOGICA AGGIORNAMENTI IN BACKGROUND
# ==========================================
class UpdateWorker(QThread):
    """Thread in background per verificare la presenza di update su GitHub."""
    finished = pyqtSignal(bool, str)  # Invia (ha_aggiornamento, nuova_versione)

    def __init__(self, owner, repo, current_version):
        super().__init__()
        self.owner = owner
        self.repo = repo
        self.current_version = current_version

    def run(self):
        try:
            # Richiesta nativa super leggera senza librerie esterne extra
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    v = data.get('tag_name', '').lstrip('v')
                    # Confronto numerico (non lessicografico) delle versioni
                    self.finished.emit(self._is_newer(v, self.current_version), v)
        except (OSError, ValueError, json.JSONDecodeError):
            pass  # Continua silenziosamente in caso di assenza di rete

    @staticmethod
    def _is_newer(remote_version: str, local_version: str) -> bool:
        """Confronta due versioni semantiche (es. '1.10.0' > '1.9.0')."""
        def to_tuple(v: str) -> tuple:
            parts = []
            for p in v.split('.'):
                try:
                    parts.append(int(p))
                except ValueError:
                    parts.append(0)
            return tuple(parts)

        return to_tuple(remote_version) > to_tuple(local_version)


# ==========================================
# HUB PRINCIPALE DELLA SUITE
# ==========================================
class UtilitySuite(QMainWindow):
    """
    Finestra principale che fa da HUB per richiamare tutti i moduli della suite.
    """

    def __init__(self):
        super().__init__()

        # Riferimenti alle finestre figlie aperte (evita la garbage collection)
        self.tool_windows: Dict[str, QWidget] = {}
        self.update_thread = None

        self.init_ui()
        self.create_menu()

        # Avvia il controllo automatico silenzioso all'apertura dell'applicazione
        self.controlla_aggiornamenti(silent=True)

    def init_ui(self) -> None:
        """Configura la geometria, il layout base e i pulsanti della dashboard."""
        screen = QApplication.primaryScreen().availableGeometry()
        screen_w = screen.width()
        screen_h = screen.height()

        width = int(screen_w * 0.20)
        height = int(screen_h * 0.40)

        min_w, min_h = 400, 600
        self.setMinimumSize(min_w, min_h)
        self.resize(max(width, min_w), max(height, min_h))

        qr = self.frameGeometry()
        cp = screen.center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.setWindowTitle(f'Py Utility Suite - v.{VERSION}')

        # --- STILE CSS ---
        self.setStyleSheet(get_style("main"))

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        # Intestazione
        title_lbl = QLabel("Utility Suite")
        title_lbl.setObjectName("title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel("Gestione rapida documenti e immagini")
        subtitle_lbl.setObjectName("subtitle")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_lbl)

        # Bottoni Utility generati dal registro TOOLS
        for label, module_name, class_name in TOOLS:
            self.add_menu_button(
                layout, label,
                lambda _=False, m=module_name, c=class_name: self.open_tool(m, c)
            )

        layout.addStretch()

        # Bottone Esci
        btn_exit = QPushButton("Esci dalla Suite")
        btn_exit.setObjectName("exitBtn")
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

    def create_menu(self) -> None:
        """Crea la barra dei menu."""
        menubar = self.menuBar()
        info_menu = menubar.addMenu('&Info')

        # NUOVO: Voce per controllare gli aggiornamenti manualmente
        update_action = QAction('Controlla Aggiornamenti', self)
        update_action.triggered.connect(lambda: self.controlla_aggiornamenti(silent=False))
        info_menu.addAction(update_action)

        about_action = QAction('Informazioni su...', self)
        about_action.triggered.connect(self.show_about_dialog)
        info_menu.addAction(about_action)

        help_menu = menubar.addMenu('&Guida')
        help_action = QAction('Aiuto Suite', self)
        help_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(help_action)

    def show_about_dialog(self) -> None:
        """Mostra la finestra di info (Autore e Versione)."""
        QMessageBox.about(
            self,
            "Info Suite",
            f"<b>Py Utility Suite</b><br><br>"
            f"Versione: {VERSION}<br>"
            f"Autore: {AUTHOR}<br><br>"
            f"Tutti i moduli sono aggiornati."
        )

    def show_help_dialog(self) -> None:
        """Mostra la finestra di guida all'uso."""
        QMessageBox.information(
            self,
            "Guida Rapida",
            "Scegli una delle utility dal menu centrale per aprire lo strumento dedicato.<br><br>"
            "Tutti i processi pesanti sono eseguiti in background per non bloccare l'interfaccia."
        )

    # --- NUOVO: FUNZIONI GESTIONE AUTOUPDATE ---
    def controlla_aggiornamenti(self, silent=True) -> None:
        """Istanzia e avvia il thread in background per la ricerca degli aggiornamenti."""
        self.update_thread = UpdateWorker(REPO_OWNER, REPO_NAME, VERSION)
        self.update_thread.finished.connect(lambda ha_upd, v_new: self._elabora_risultato_update(ha_upd, v_new, silent))
        self.update_thread.start()

    def _elabora_risultato_update(self, ha_update, v_nuova, silent) -> None:
        """Riceve la risposta dal thread e decide se reindirizzare l'utente sul sito."""
        if ha_update:
            risposta = QMessageBox.question(
                self,
                "Aggiornamento Disponibile",
                f"È stata rilasciata una nuova versione della suite (v{v_nuova}).\nVuoi andare alla pagina di download?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if risposta == QMessageBox.StandardButton.Yes:
                # Reindirizzamento diretto alla tua nuova area download protetta
                sito_download = "https://mindnetwork.vip/download.php"
                QDesktopServices.openUrl(QUrl(sito_download))
        elif not silent:
            QMessageBox.information(self, "Nessun Aggiornamento", "La suite è già aggiornata all'ultima versione.")

    def add_menu_button(self, layout: QVBoxLayout, text: str, function: callable) -> None:
        """Aggiunge un pulsante al layout specificato agganciandolo a uno slot."""
        btn = QPushButton(text)
        btn.clicked.connect(function)
        layout.addWidget(btn)

    def open_tool(self, module_name: str, class_name: str) -> None:
        """Importa il modulo del tool e ne apre la finestra, gestendo gli errori di caricamento."""
        try:
            window_cls = getattr(importlib.import_module(module_name), class_name)
            window = window_cls()
        except Exception as e:  # noqa: BLE001 - un tool difettoso non deve chiudere la suite
            logger.error("Impossibile aprire %s.%s: %s", module_name, class_name, e, exc_info=True)
            QMessageBox.critical(
                self, "Errore modulo",
                f"Impossibile avviare il tool '{module_name}'.\n\nDettagli: {e}"
            )
            return
        self.tool_windows[class_name] = window
        window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Icona globale: ereditata da tutte le finestre dei tool
    app.setWindowIcon(QIcon(resource_path(os.path.join("assets", "icon.png"))))
    suite = UtilitySuite()
    suite.show()
    sys.exit(app.exec())