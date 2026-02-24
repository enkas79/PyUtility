import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from pdf2docx import Converter

class ConversionWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, pdf_path, docx_path):
        super().__init__()
        self.pdf_path, self.docx_path = pdf_path, docx_path
    def run(self):
        try:
            cv = Converter(self.pdf_path); cv.convert(self.docx_path); cv.close()
            self.finished.emit(self.docx_path)
        except Exception as e: self.error.emit(str(e))

class ModernConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_path = ""
        self.initUI()

    def initUI(self):
        # --- LOGICA DIMENSIONI E CENTRATURA ---
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.20)
        height = int(screen.height() * 0.40)
        min_w, min_h = 400, 500
        self.setMinimumSize(min_w, min_h)
        self.resize(max(width, min_w), max(height, min_h))
        qr = self.frameGeometry()
        qr.moveCenter(screen.center())
        self.move(qr.topLeft())

        self.setWindowTitle('PDF to Word Converter Pro')
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI'; }
            QPushButton { background-color: #0078d4; border: none; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #1e90ff; }
            QPushButton#exitBtn { background-color: #d32f2f; }
            QProgressBar { border: 1px solid #555; border-radius: 5px; text-align: center; height: 25px; background-color: #444; }
            QProgressBar::chunk { background-color: #00c853; border-radius: 4px; }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        self.label = QLabel('Pronto per la conversione'); self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.pbar = QProgressBar(); layout.addWidget(self.pbar)
        self.btn_select = QPushButton('📂 Seleziona File PDF'); self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)
        self.btn_convert = QPushButton('⚡ Converti in Word'); self.btn_convert.setEnabled(False); self.btn_convert.clicked.connect(self.start_conversion)
        layout.addWidget(self.btn_convert)
        layout.addStretch()
        btn_exit = QPushButton('Esci'); btn_exit.setObjectName("exitBtn"); btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)
        self.setLayout(layout)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scegli PDF", "", "PDF (*.pdf)")
        if path: self.pdf_path = path; self.label.setText(f"File: {os.path.basename(path)}"); self.btn_convert.setEnabled(True)
    def start_conversion(self):
        self.btn_convert.setEnabled(False); self.pbar.setRange(0, 0); self.label.setText("Conversione...")
        self.worker = ConversionWorker(self.pdf_path, self.pdf_path.replace(".pdf", ".docx"))
        self.worker.finished.connect(self.on_finished); self.worker.start()
    def on_finished(self, path):
        self.pbar.setRange(0, 100); self.pbar.setValue(100); QMessageBox.information(self, "Successo", "File salvato!"); self.btn_select.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv); window = ModernConverter(); window.show(); sys.exit(app.exec())