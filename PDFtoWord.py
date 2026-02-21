import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from pdf2docx import Converter


# --- LOGICA DI CONVERSIONE (Thread separato) ---
class ConversionWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, pdf_path, docx_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.docx_path = docx_path

    def run(self):
        try:
            cv = Converter(self.pdf_path)
            cv.convert(self.docx_path, start=0, end=None)
            cv.close()
            self.finished.emit(self.docx_path)
        except Exception as e:
            self.error.emit(str(e))


# --- INTERFACCIA GRAFICA ---
class ModernConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF to Word Converter Pro')
        self.setFixedSize(450, 300)  # Dimensione fissa per un look pulito

        # Applichiamo lo stile CSS (QSS)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                font-size: 14px;
                margin-bottom: 10px;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1e90ff;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
            QPushButton#exitBtn {
                background-color: #d32f2f;
            }
            QPushButton#exitBtn:hover {
                background-color: #f44336;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #444;
            }
            QProgressBar::chunk {
                background-color: #00c853;
                border-radius: 4px;
            }
        """)

        # Layout Principale
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        # Titolo e Stato
        self.label = QLabel('Pronto per la conversione')
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.label)

        # Barra di caricamento
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        main_layout.addWidget(self.pbar)

        # Contenitore bottoni Azione
        action_layout = QVBoxLayout()

        self.btn_select = QPushButton('📂 Seleziona File PDF')
        self.btn_select.clicked.connect(self.select_file)
        action_layout.addWidget(self.btn_select)

        self.btn_convert = QPushButton('⚡ Converti in Word')
        self.btn_convert.setEnabled(False)
        self.btn_convert.clicked.connect(self.start_conversion)
        action_layout.addWidget(self.btn_convert)

        main_layout.addLayout(action_layout)

        # Spazio flessibile
        main_layout.addStretch()

        # Bottone Esci (in basso)
        self.btn_exit = QPushButton('Esci')
        self.btn_exit.setObjectName("exitBtn")  # Usiamo l'ID per lo stile rosso
        self.btn_exit.clicked.connect(self.close)
        main_layout.addWidget(self.btn_exit)

        self.setLayout(main_layout)
        self.pdf_path = ""

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scegli PDF", "", "PDF (*.pdf)")
        if path:
            self.pdf_path = path
            self.label.setText(f"Selezionato: {os.path.basename(path)}")
            self.btn_convert.setEnabled(True)
            self.pbar.setRange(0, 100)
            self.pbar.setValue(0)

    def start_conversion(self):
        docx_path = self.pdf_path.replace(".pdf", ".docx")

        self.btn_convert.setEnabled(False)
        self.btn_select.setEnabled(False)
        self.pbar.setRange(0, 0)  # Animazione "caricamento"
        self.label.setText("Conversione in corso...")

        self.worker = ConversionWorker(self.pdf_path, docx_path)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, path):
        self.pbar.setRange(0, 100)
        self.pbar.setValue(100)
        self.label.setText("Conversione completata!")
        QMessageBox.information(self, "Successo", f"File salvato correttamente!")
        self.reset_ui()

    def on_error(self, message):
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        QMessageBox.critical(self, "Errore", f"Si è verificato un errore: {message}")
        self.reset_ui()

    def reset_ui(self):
        self.btn_select.setEnabled(True)
        self.btn_convert.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModernConverter()
    window.show()
    sys.exit(app.exec())