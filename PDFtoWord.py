"""
PDF to Word Converter Module
============================
Tool per convertire file PDF in documenti Word (.docx) editabili.
"""

import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from pdf2docx import Converter


class ConversionWorker(QThread):
    """
    Thread per eseguire la conversione da PDF a Word in background.
    
    Attributes:
        finished (pyqtSignal): Segnale emesso al completamento con il percorso del file generato.
        error (pyqtSignal): Segnale emesso in caso di errore.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, pdf_path: str, docx_path: str) -> None:
        """
        Inizializza il worker per la conversione.
        
        Args:
            pdf_path (str): Percorso del file PDF da convertire.
            docx_path (str): Percorso di output per il file .docx.
        """
        super().__init__()
        self.pdf_path: str = pdf_path
        self.docx_path: str = docx_path

    def run(self) -> None:
        """Esegue la conversione da PDF a Word."""
        try:
            cv = Converter(self.pdf_path)
            cv.convert(self.docx_path)
            cv.close()
            self.finished.emit(self.docx_path)
        except Exception as e:
            self.error.emit(str(e))


class ModernConverter(QWidget):
    """
    Applicazione per convertire file PDF in Word.
    
    Attributes:
        pdf_path (str): Percorso del file PDF selezionato.
    """

    def __init__(self) -> None:
        """Inizializza l'applicazione ModernConverter."""
        super().__init__()
        self.pdf_path: Optional[str] = None
        self.worker: Optional[ConversionWorker] = None
        self.initUI()

    def initUI(self) -> None:
        """Inizializza l'interfaccia utente."""
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
        
        self.label = QLabel('Pronto per la conversione')
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        
        self.btn_select = QPushButton('📂 Seleziona File PDF')
        self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)
        
        self.btn_convert = QPushButton('⚡ Converti in Word')
        self.btn_convert.setEnabled(False)
        self.btn_convert.clicked.connect(self.start_conversion)
        layout.addWidget(self.btn_convert)
        
        layout.addStretch()
        
        btn_exit = QPushButton('Esci')
        btn_exit.setObjectName("exitBtn")
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)
        
        self.setLayout(layout)

    def select_file(self) -> None:
        """Seleziona un file PDF da convertire."""
        path: Optional[str] = QFileDialog.getOpenFileName(
            self, "Scegli PDF", "", "PDF (*.pdf)"
        )[0]
        if path:
            self.pdf_path = path
            self.label.setText(f"File: {os.path.basename(path)}")
            self.btn_convert.setEnabled(True)

    def start_conversion(self) -> None:
        """Avvia il processo di conversione."""
        if not self.pdf_path:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un file PDF.")
            return
        
        self.btn_convert.setEnabled(False)
        self.btn_select.setEnabled(False)
        self.pbar.setRange(0, 0)  # Modalità indeterminata
        self.label.setText("Conversione in corso...")
        
        # Genera il percorso di output
        output_path: str = self.pdf_path.replace(".pdf", ".docx")
        
        self.worker = ConversionWorker(self.pdf_path, output_path)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, path: str) -> None:
        """
        Slot eseguito al completamento della conversione.
        
        Args:
            path (str): Percorso del file .docx generato.
        """
        self.pbar.setRange(0, 100)
        self.pbar.setValue(100)
        self.btn_convert.setEnabled(True)
        self.btn_select.setEnabled(True)
        self.label.setText(f"File salvato: {os.path.basename(path)}")
        QMessageBox.information(self, "Successo", "File convertito e salvato con successo!")

    def on_error(self, error: str) -> None:
        """
        Slot eseguito in caso di errore durante la conversione.
        
        Args:
            error (str): Messaggio di errore.
        """
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.btn_convert.setEnabled(True)
        self.btn_select.setEnabled(True)
        self.label.setText("Errore durante la conversione")
        QMessageBox.critical(self, "Errore", f"Si è verificato un errore: {error}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModernConverter()
    window.show()
    sys.exit(app.exec())
