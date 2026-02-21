import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt

# --- CONFIGURAZIONE SUITE ---
VERSION = "1.0.0"
AUTHOR = "Enrico Martini"

# Importiamo le classi dai tuoi file
from ConvImage import ImageResizerApp
from Find_Document import FileManagerApp
from PDF_plus import PDFPlusPro
from PDFtoWord import ModernConverter


class UtilitySuite(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        # Inizializziamo le variabili per le finestre
        self.img_app = None
        self.find_app = None
        self.pdf_plus_app = None
        self.pdf_word_app = None

    def initUI(self):
        self.setWindowTitle(f'Py Utility Suite - v.{VERSION}')
        self.setFixedSize(400, 580)  # Leggermente più alta per far spazio alle info

        # Stile Moderno
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: white; font-family: 'Segoe UI'; }
            QLabel#title { font-size: 26px; font-weight: bold; color: #0078d4; margin-bottom: 5px; }
            QLabel#subtitle { font-size: 12px; color: #888; margin-bottom: 20px; }

            QPushButton { 
                background-color: #333; border: 1px solid #555; 
                padding: 15px; border-radius: 8px; font-size: 14px; text-align: left;
            }
            QPushButton:hover { background-color: #444; border-color: #0078d4; }

            QFrame#infoBox { 
                background-color: #252525; 
                border-top: 1px solid #444; 
                border-radius: 0px; 
            }
            QLabel#infoText { font-size: 11px; color: #aaa; }

            QPushButton#exitBtn { background-color: #d32f2f; text-align: center; margin-top: 10px; }
            QPushButton#exitBtn:hover { background-color: #f44336; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Rimuoviamo margini esterni per gestire il footer

        # Contenitore Principale
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 10)
        content_layout.setSpacing(12)

        # Titolo e Sottotitolo
        title_lbl = QLabel("Utility Suite")
        title_lbl.setObjectName("title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_lbl)

        subtitle_lbl = QLabel("Gestione rapida documenti e immagini")
        subtitle_lbl.setObjectName("subtitle")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(subtitle_lbl)

        # Bottoni per lanciare i programmi
        self.add_menu_button(content_layout, "🖼️ Image Converter & Resizer", self.open_image_app)
        self.add_menu_button(content_layout, "🔍 Ricerca & Gestione Documenti", self.open_find_app)
        self.add_menu_button(content_layout, "📄 PDF Plus (Unione PDF)", self.open_pdf_plus)
        self.add_menu_button(content_layout, "📝 PDF to Word Converter", self.open_pdf_word)

        content_layout.addStretch()

        # Bottone Esci
        btn_exit = QPushButton("Esci dalla Suite")
        btn_exit.setObjectName("exitBtn")
        btn_exit.clicked.connect(self.close)
        content_layout.addWidget(btn_exit)

        layout.addLayout(content_layout)

        # --- FOOTER INFO (Autore e Versione) ---
        info_frame = QFrame()
        info_frame.setObjectName("infoBox")
        info_frame.setFixedHeight(50)
        info_layout = QHBoxLayout(info_frame)

        author_lbl = QLabel(f"Autore: {AUTHOR}")
        author_lbl.setObjectName("infoText")

        version_lbl = QLabel(f"Versione: {VERSION}")
        version_lbl.setObjectName("infoText")

        info_layout.addWidget(author_lbl)
        info_layout.addStretch()
        info_layout.addWidget(version_lbl)

        layout.addWidget(info_frame)

        self.setLayout(layout)

    def add_menu_button(self, layout, text, function):
        btn = QPushButton(text)
        btn.clicked.connect(function)
        layout.addWidget(btn)

    # Metodi per aprire le finestre
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