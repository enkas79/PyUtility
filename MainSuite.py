import sys
import urllib.request
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QAction, QDesktopServices

# --- CONFIGURAZIONE DINAMICA ---
VERSION = "1.1.0"
AUTHOR = "Enrico Martini"
REPO_OWNER = "enkas79"
REPO_NAME = "PyUtility"

# Import moduli esterni (Assicurati che i file siano nella stessa cartella)
try:
    from ConvImage import ImageResizerApp
    from MergeImage import ImageMergerApp
    from Find_Document import FileManagerApp
    from PDF_plus import PDFPlusPro
    from PDFtoWord import ModernConverter
except ImportError as e:
    print(f"Errore caricamento moduli: {e}")


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
                    v = data.get('tag_name', '').replace('v', '')
                    # Esegue il confronto delle versioni
                    self.finished.emit(v > self.current_version, v)
        except:
            pass  # Continua silenziosamente in caso di assenza di rete


# ==========================================
# HUB PRINCIPALE DELLA SUITE
# ==========================================
class UtilitySuite(QMainWindow):
    """
    Finestra principale che fa da HUB per richiamare tutti i moduli della suite.
    """

    def __init__(self):
        super().__init__()

        # Variabili per gestire le finestre figlie
        self.img_app = None
        self.merge_app = None
        self.find_app = None
        self.pdf_plus_app = None
        self.pdf_word_app = None
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

        min_w, min_h = 400, 550
        self.setMinimumSize(min_w, min_h)
        self.resize(max(width, min_w), max(height, min_h))

        qr = self.frameGeometry()
        cp = screen.center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.setWindowTitle(f'Py Utility Suite - v.{VERSION}')

        # --- STILE CSS ---
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget#centralWidget { background-color: #1e1e1e; }
            QLabel { color: white; font-family: 'Segoe UI'; }
            QLabel#title { font-size: 24px; font-weight: bold; color: #0078d4; margin-bottom: 5px; }
            QLabel#subtitle { font-size: 11px; color: #888; margin-bottom: 15px; }

            QPushButton { 
                background-color: #333; border: 1px solid #555; 
                padding: 15px; border-radius: 8px; font-size: 14px; text-align: left;
                color: white;
            }
            QPushButton:hover { background-color: #444; border-color: #0078d4; }

            QPushButton#exitBtn { background-color: #d32f2f; text-align: center; margin-top: 10px; }
            QPushButton#exitBtn:hover { background-color: #f44336; }

            QMenuBar { background-color: #2d2d2d; color: white; }
            QMenuBar::item:selected { background-color: #0078d4; }
            QMenu { background-color: #2d2d2d; color: white; border: 1px solid #555; }
            QMenu::item:selected { background-color: #0078d4; }

            QMessageBox { background-color: #1e1e1e; }
            QMessageBox QLabel { color: white; font-size: 13px; }
            QMessageBox QPushButton { background-color: #0078d4; color: white; padding: 5px 20px; }
        """)

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

        # Bottoni Utility
        self.add_menu_button(layout, "🖼️ Image Converter/Resizer", self.open_image_app)
        self.add_menu_button(layout, "🧩 Image Merger (Unisci Immagini)", self.open_merge_app)
        self.add_menu_button(layout, "🔍 Ricerca/Gestione Documenti", self.open_find_app)
        self.add_menu_button(layout, "📄 PDF Plus (Unione PDF)", self.open_pdf_plus)
        self.add_menu_button(layout, "📝 PDF to Word Converter", self.open_pdf_word)

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

    # --- Funzioni di apertura applicazioni ---
    def open_image_app(self) -> None:
        self.img_app = ImageResizerApp()
        self.img_app.show()

    def open_merge_app(self) -> None:
        self.merge_app = ImageMergerApp()
        self.merge_app.show()

    def open_find_app(self) -> None:
        self.find_app = FileManagerApp()
        self.find_app.show()

    def open_pdf_plus(self) -> None:
        self.pdf_plus_app = PDFPlusPro()
        self.pdf_plus_app.show()

    def open_pdf_word(self) -> None:
        self.pdf_word_app = ModernConverter()
        self.pdf_word_app.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    suite = UtilitySuite()
    suite.show()
    sys.exit(app.exec())