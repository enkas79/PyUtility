"""
Py Utility Suite - entry point
==============================
Hub principale: apre i singoli tool e gestisce l'autoupdate.
Avvio: python src/main.py
"""

import importlib
import os
import sys
from typing import Callable, Dict, List, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QLabel, QMainWindow, QMessageBox,
                             QPushButton, QVBoxLayout, QWidget)

from app_info import APP_NAME, get_app_version, resource_path
from base_window import add_help_menu, logger, show_about
from styles import get_style
from update_manager import UpdateController

VERSION = get_app_version()

# Registro dei tool: (etichetta pulsante, modulo, classe finestra).
# I moduli sono importati solo all'apertura: una dipendenza mancante in un tool
# non impedisce più l'uso degli altri (prima un unico try/except li bloccava tutti).
# NB: ogni modulo va dichiarato con --hidden-import nel workflow build-installers.yml.
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
# HUB PRINCIPALE DELLA SUITE
# ==========================================
class UtilitySuite(QMainWindow):
    """
    Finestra principale che fa da HUB per richiamare tutti i moduli della suite.
    """

    GUIDE_TEXT = (
        "Scegli una delle utility dal menu centrale per aprire lo strumento dedicato.<br><br>"
        "Ogni strumento ha il proprio menu <b>Aiuto &gt; Guida</b> (F1) con le istruzioni.<br>"
        "Tutti i processi pesanti sono eseguiti in background per non bloccare l'interfaccia.<br><br>"
        "All'avvio la suite verifica in background la presenza di aggiornamenti; "
        "puoi farlo anche manualmente da <b>Aiuto &gt; Controlla Aggiornamenti</b>."
    )

    def __init__(self) -> None:
        super().__init__()

        # Riferimenti alle finestre figlie aperte (evita la garbage collection)
        self.tool_windows: Dict[str, QWidget] = {}
        self.updater = UpdateController(self, VERSION)

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

        self.setWindowTitle(f'{APP_NAME} - v.{VERSION}')

        # --- STILE CSS ---
        self.setStyleSheet(get_style("main"))

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(32, 32, 32, 32)
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
        """Crea la barra dei menu con il menu 'Aiuto' standard."""
        add_help_menu(self.menuBar(), self, self.show_help_dialog,
                      lambda: self.controlla_aggiornamenti(silent=False),
                      self.show_about_dialog)

    def show_about_dialog(self) -> None:
        """Mostra la finestra di info (Autore e Versione)."""
        show_about(self)

    def show_help_dialog(self) -> None:
        """Mostra la finestra di guida all'uso."""
        QMessageBox.information(self, "Guida Rapida", self.GUIDE_TEXT)

    def controlla_aggiornamenti(self, silent: bool = True) -> None:
        """Verifica in background la presenza di aggiornamenti (vedi update_manager)."""
        self.updater.check(silent=silent)

    def closeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        """Interrompe eventuali download di aggiornamenti prima di uscire."""
        self.updater.shutdown()
        super().closeEvent(event)

    def add_menu_button(self, layout: QVBoxLayout, text: str, function: Callable[[], None]) -> None:
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