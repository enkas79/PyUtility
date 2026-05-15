import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

# --- CONFIGURAZIONE DINAMICA ---
VERSION = "1.1.0"
AUTHOR = "Enrico Martini"

# Import moduli esterni (Assicurati che i file siano nella stessa cartella)
try:
    from ConvImage import ImageResizerApp
    from MergeImage import ImageMergerApp
    from Find_Document import FileManagerApp
    from PDF_plus import PDFPlusPro
    from PDFtoWord import ModernConverter
except ImportError as e:
    print(f"Errore caricamento moduli: {e}")


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

        self.init_ui()
        self.create_menu()

    def init_ui(self) -> None:
        """Configura la geometria, il layout base e i pulsanti della dashboard."""
        # 1. Rilevamento Geometria Schermo
        screen = QApplication.primaryScreen().availableGeometry()
        screen_w = screen.width()
        screen_h = screen.height()

        # 2. Calcolo Dimensioni (20% larghezza, 40% altezza per ospitare i bottoni)
        width = int(screen_w * 0.20)
        height = int(screen_h * 0.40)

        # 3. Impostazione Limite Minimo
        min_w, min_h = 400, 550
        self.setMinimumSize(min_w, min_h)

        # Applichiamo la dimensione calcolata (se maggiore del minimo)
        self.resize(max(width, min_w), max(height, min_h))

        # 4. Centratura della finestra
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