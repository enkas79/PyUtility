"""
PDF to Word Converter Module
============================
Tool per convertire file PDF in documenti Word (.docx) editabili.
"""

import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from base_window import BaseWindow
from pdf_core import convert_pdf_to_docx, docx_output_path


class ConversionWorker(QThread):
    """
    Thread per eseguire la conversione da PDF a Word in background.
    
    Attributes:
        done (pyqtSignal): Segnale emesso al completamento con il percorso del file generato
            (nome diverso da QThread.finished per non oscurarlo).
        error (pyqtSignal): Segnale emesso in caso di errore.
    """
    done = pyqtSignal(str)
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
        """Esegue la conversione da PDF a Word (logica in pdf_core)."""
        try:
            self.done.emit(convert_pdf_to_docx(self.pdf_path, self.docx_path))
        except Exception as e:  # noqa: BLE001 - pdf2docx/PyMuPDF sollevano tipi eterogenei
            self.error.emit(str(e))


class ModernConverter(BaseWindow):
    """
    Applicazione per convertire file PDF in Word.
    
    Attributes:
        pdf_path (str): Percorso del file PDF selezionato.
    """

    GUIDE_TEXT = (
        "1. Premi 'Seleziona File PDF' e scegli il documento.\n"
        "2. Premi 'Converti in Word'.\n\n"
        "Il file .docx viene salvato nella stessa cartella del PDF, con lo stesso nome. "
        "La fedeltà della conversione dipende dalla struttura del PDF "
        "(i PDF scansionati non contengono testo modificabile)."
    )

    def __init__(self) -> None:
        """Inizializza l'applicazione ModernConverter."""
        super().__init__('PDF to Word Converter Pro', min_width=400, min_height=500)
        self.pdf_path: Optional[str] = None
        self.worker: Optional[ConversionWorker] = None
        self.initUI()

    def initUI(self) -> None:
        """Inizializza l'interfaccia utente."""
        layout = self.create_vertical_layout(margins=(32, 16, 32, 32), spacing=12)
        layout.setMenuBar(self.create_menu_bar())

        title = QLabel("📝 PDF to Word")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.label = QLabel('Pronto per la conversione')
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        
        self.btn_select = QPushButton('📂 Seleziona File PDF')
        self.btn_select.setObjectName("primaryBtn")
        self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)
        
        self.btn_convert = QPushButton('⚡ Converti in Word')
        self.btn_convert.setObjectName("successBtn")
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
        
        # Percorso .docx libero accanto al PDF (nessuna sovrascrittura)
        output_path: str = docx_output_path(self.pdf_path)
        
        self.worker = ConversionWorker(self.pdf_path, output_path)
        self.worker.done.connect(self.on_finished)
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
