import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

# --- CONFIGURAZIONE DINAMICA ---
VERSION = "1.0.0"
AUTHOR = "Enrico Martini"

# Import moduli esterni (Assicurati che i file siano nella stessa cartella)
try:
    from ConvImage import ImageResizerApp
    from Find_Document import FileManagerApp
    from PDF_plus import PDFPlusPro
    from PDFtoWord import ModernConverter
except ImportError as e:
    print(f"Errore caricamento moduli: {e}")


class UtilitySuite(QMainWindow):
    def __init__(self):
        super().__init__()

        # Variabili per gestire le finestre figlie
        self.img_app = None
        self.find_app = None
        self.pdf_plus_app = None
        self.pdf_word_app = None

        self.initUI()
        self.create_menu()

    def initUI(self):
        # 1. Rilevamento Geometria Schermo
        screen = QApplication.primaryScreen().availableGeometry()
        screen_w = screen.width()
        screen_h = screen.height()

        # 2. Calcolo Dimensioni (20% larghezza, 40% altezza per ospitare i bottoni)
        width = int(screen_w * 0.20)
        height = int(screen_h * 0.40)

        # 3. Impostazione Limite Minimo (per non rendere il testo illeggibile)
        min_w, min_h = 400, 500
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
        self.add_menu_button(layout, "🔍 Ricerca/Gestione Documenti", self.open_find_app)
        self.add_menu_button(layout, "📄 PDF Plus (Unione PDF)", self.open_pdf_plus)
        self.add_menu_button(layout, "📝 PDF to Word Converter", self.open_pdf_word)

        layout.addStretch()

        # Bottone Esci
        btn_exit = QPushButton("Esci dalla Suite")
        btn_exit.setObjectName("exitBtn")
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

    def create_menu(self):
        menubar = self.menuBar()
        info_menu = menubar.addMenu('&Info')
        about_action = QAction('Informazioni su...', self)
        about_action.triggered.connect(self.show_about_dialog)
        info_menu.addAction(about_action)

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "Info Suite",
            f"<b>Py Utility Suite</b><br><br>"
            f"Versione: {VERSION}<br>"
            f"Autore: {AUTHOR}<br><br>"
            f"Tutti i moduli sono aggiornati."
        )

    def add_menu_button(self, layout, text, function):
        btn = QPushButton(text)
        btn.clicked.connect(function)
        layout.addWidget(btn)

    # Funzioni di apertura applicazioni
    def open_image_app(self):
        self.img_app = ImageResizerApp()
        self.img_app.show()

    def open_find_app(self):
        self.find_app = FileManagerApp()
        self.find_app.show()

    def open_pdf_plus(self):
        self.pdf_plus_app = PDFPlusPro()
        self.pdf_plus_app.show()

    def open_pdf_word(self):
        self.pdf_word_app = ModernConverter()
        self.pdf_word_app.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    suite = UtilitySuite()
    suite.show()
    sys.exit(app.exec())