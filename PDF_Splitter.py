"""
PDF Splitter Module
===================
Tool per dividere un file PDF in pagine singole o intervalli personalizzati.
"""

import os
import logging
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QMessageBox, QSpinBox, QComboBox, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyPDF2 import PdfReader, PdfWriter
from base_window import BaseWindow
from styles import get_style

logger = logging.getLogger(__name__)


class SplitWorker(QThread):
    """
    Thread per eseguire lo split del PDF in background.
    
    Attributes:
        progress_signal (pyqtSignal): Segnale per aggiornare la barra di progresso.
        finished_signal (pyqtSignal): Segnale emesso al completamento.
        error_signal (pyqtSignal): Segnale emesso in caso di errore.
    """
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        pdf_path: str,
        output_folder: str,
        split_mode: str,
        start_page: int = 1,
        end_page: int = 1,
        pages_per_file: int = 1
    ) -> None:
        """
        Inizializza il worker per lo split del PDF.
        
        Args:
            pdf_path (str): Percorso del file PDF da dividere.
            output_folder (str): Cartella di output.
            split_mode (str): Modalità di split ("single", "range", "custom").
            start_page (int): Pagina iniziale (per modalità "range" o "custom").
            end_page (int): Pagina finale (per modalità "range" o "custom").
            pages_per_file (int): Numero di pagine per file (per modalità "custom").
        """
        super().__init__()
        self.pdf_path = pdf_path
        self.output_folder = output_folder
        self.split_mode = split_mode
        self.start_page = start_page
        self.end_page = end_page
        self.pages_per_file = pages_per_file

    def run(self) -> None:
        """Esegue lo split del PDF in base alla modalità selezionata."""
        try:
            reader = PdfReader(self.pdf_path)
            total_pages = len(reader.pages)
            
            if self.split_mode == "single":
                # Divide ogni pagina in un file separato
                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)
                    output_path = os.path.join(
                        self.output_folder,
                        f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_pagina_{i+1}.pdf"
                    )
                    with open(output_path, "wb") as f:
                        writer.write(f)
                    self.progress_signal.emit(int(((i + 1) / total_pages) * 100))
                
                self.finished_signal.emit(
                    f"Split completato: {total_pages} pagine divise in file singoli."
                )
            
            elif self.split_mode == "range":
                # Estrae un intervallo di pagine
                start = max(1, self.start_page) - 1
                end = min(self.end_page, total_pages)
                
                if start >= end:
                    self.error_signal.emit("Intervallo di pagine non valido.")
                    return
                
                writer = PdfWriter()
                for i in range(start, end):
                    writer.add_page(reader.pages[i])
                
                output_path = os.path.join(
                    self.output_folder,
                    f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_pagine_{start+1}-{end}.pdf"
                )
                with open(output_path, "wb") as f:
                    writer.write(f)
                
                self.progress_signal.emit(100)
                self.finished_signal.emit(
                    f"Split completato: pagine {start+1}-{end} estratte in un file."
                )
            
            elif self.split_mode == "custom":
                # Divide in file con N pagine ciascuno
                writer = PdfWriter()
                file_count = 1
                
                for i, page in enumerate(reader.pages):
                    writer.add_page(page)
                    
                    if (i + 1) % self.pages_per_file == 0 or i == total_pages - 1:
                        output_path = os.path.join(
                            self.output_folder,
                            f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_parte_{file_count}.pdf"
                        )
                        with open(output_path, "wb") as f:
                            writer.write(f)
                        writer = PdfWriter()
                        file_count += 1
                    
                    self.progress_signal.emit(int(((i + 1) / total_pages) * 100))
                
                self.finished_signal.emit(
                    f"Split completato: {file_count - 1} file creati con {self.pages_per_file} pagine ciascuno."
                )
            
        except Exception as e:
            logger.error(f"Errore durante lo split del PDF: {str(e)}", exc_info=True)
            self.error_signal.emit(f"Errore durante lo split: {str(e)}")


class PDFSplitterApp(BaseWindow):
    """
    Applicazione per dividere file PDF in pagine singole o intervalli.
    
    Attributes:
        pdf_path (str): Percorso del file PDF selezionato.
        output_folder (str): Cartella di output selezionata.
    """

    def __init__(self) -> None:
        """Inizializza l'applicazione PDFSplitter."""
        super().__init__("PDF Splitter", min_width=500, min_height=550)
        self.pdf_path: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.worker: Optional[SplitWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Inizializza l'interfaccia utente."""
        layout = self.create_vertical_layout(margins=(20, 20, 20, 20), spacing=15)
        
        # Titolo
        title_label = QLabel("✂️ PDF Splitter")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Dividi un file PDF in pagine singole o intervalli personalizzati")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Sezione selezione file
        layout.addWidget(QLabel("1. Seleziona il file PDF:"))
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Nessun file selezionato")
        self.file_label.setStyleSheet("color: #aaa;")
        btn_select = QPushButton("📂 Seleziona PDF")
        btn_select.setObjectName("primaryBtn")
        btn_select.clicked.connect(self._select_pdf)
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(btn_select)
        layout.addLayout(file_layout)
        
        # Sezione modalità split
        layout.addWidget(QLabel("2. Modalità di divisione:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems([
            "Pagine singole (1 pagina per file)",
            "Intervallo di pagine",
            "N pagine per file"
        ])
        self.combo_mode.currentIndexChanged.connect(self._update_mode_ui)
        layout.addWidget(self.combo_mode)
        
        # Sezione parametri modalità
        self.range_frame = QHBoxLayout()
        self.range_frame.addWidget(QLabel("Da pagina:"))
        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 9999)
        self.spin_start.setValue(1)
        self.range_frame.addWidget(self.spin_start)
        self.range_frame.addWidget(QLabel("a pagina:"))
        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, 9999)
        self.spin_end.setValue(1)
        self.range_frame.addWidget(self.spin_end)
        
        self.custom_frame = QHBoxLayout()
        self.custom_frame.addWidget(QLabel("Pagine per file:"))
        self.spin_pages = QSpinBox()
        self.spin_pages.setRange(1, 9999)
        self.spin_pages.setValue(5)
        self.custom_frame.addWidget(self.spin_pages)
        
        layout.addLayout(self.range_frame)
        layout.addLayout(self.custom_frame)
        self._update_mode_ui(0)  # Nasconde i frame non necessari all'avvio
        
        # Sezione output
        layout.addWidget(QLabel("3. Cartella di output:"))
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Nessuna cartella selezionata")
        self.output_label.setStyleSheet("color: #aaa;")
        btn_output = QPushButton("📂 Seleziona Cartella")
        btn_output.setObjectName("primaryBtn")
        btn_output.clicked.connect(self._select_output_folder)
        output_layout.addWidget(self.output_label, 1)
        output_layout.addWidget(btn_output)
        layout.addLayout(output_layout)
        
        # Barra di progresso e stato
        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        
        # Pulsanti azione
        action_layout = QHBoxLayout()
        self.btn_split = QPushButton("✂️ DIVIDI PDF")
        self.btn_split.setObjectName("successBtn")
        self.btn_split.clicked.connect(self._start_split)
        self.btn_split.setEnabled(False)
        
        btn_exit = QPushButton("Esci")
        btn_exit.setObjectName("dangerBtn")
        btn_exit.clicked.connect(self.close)
        
        action_layout.addWidget(self.btn_split)
        action_layout.addWidget(btn_exit)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)

    def _update_mode_ui(self, index: int) -> None:
        """
        Aggiorna l'interfaccia in base alla modalità di split selezionata.
        
        Args:
            index (int): Indice della modalità selezionata.
        """
        self.range_frame.setParent(None)  # Rimuove dal layout
        self.custom_frame.setParent(None)
        
        if index == 0:  # Pagine singole
            pass  # Non serve nessun parametro aggiuntivo
        elif index == 1:  # Intervallo di pagine
            self._init_ui()  # Re-inizializza per aggiungere il frame
            self.range_frame = QHBoxLayout()
            self.range_frame.addWidget(QLabel("Da pagina:"))
            self.range_frame.addWidget(self.spin_start)
            self.range_frame.addWidget(QLabel("a pagina:"))
            self.range_frame.addWidget(self.spin_end)
            # Inserisce il frame nel layout principale
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and isinstance(item.widget(), QLabel) and "Modalità" in item.widget().text():
                    self.layout().insertLayout(i + 2, self.range_frame)
                    break
        elif index == 2:  # N pagine per file
            self.custom_frame = QHBoxLayout()
            self.custom_frame.addWidget(QLabel("Pagine per file:"))
            self.custom_frame.addWidget(self.spin_pages)
            # Inserisce il frame nel layout principale
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and isinstance(item.widget(), QLabel) and "Modalità" in item.widget().text():
                    self.layout().insertLayout(i + 2, self.custom_frame)
                    break

    def _select_pdf(self) -> None:
        """Seleziona il file PDF da dividere."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona PDF", "", "PDF (*.pdf)"
        )
        if path:
            self.pdf_path = path
            self.file_label.setText(os.path.basename(path))
            self.file_label.setStyleSheet("color: #00c853;")
            self._check_ready()

    def _select_output_folder(self) -> None:
        """Seleziona la cartella di output."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleziona Cartella di Output"
        )
        if folder:
            self.output_folder = folder
            self.output_label.setText(folder)
            self.output_label.setStyleSheet("color: #00c853;")
            self._check_ready()

    def _check_ready(self) -> None:
        """Verifica se tutti i parametri sono pronti per lo split."""
        if self.pdf_path and self.output_folder:
            self.btn_split.setEnabled(True)
        else:
            self.btn_split.setEnabled(False)

    def _start_split(self) -> None:
        """Avvia il processo di split del PDF."""
        if not self.pdf_path or not self.output_folder:
            self.show_error("Seleziona un file PDF e una cartella di output.")
            return
        
        mode = self.combo_mode.currentIndex()
        split_mode = "single" if mode == 0 else "range" if mode == 1 else "custom"
        
        self.btn_split.setEnabled(False)
        self.pbar.setValue(0)
        self.status_label.setText("Split in corso...")
        
        self.worker = SplitWorker(
            pdf_path=self.pdf_path,
            output_folder=self.output_folder,
            split_mode=split_mode,
            start_page=self.spin_start.value() if mode == 1 else 1,
            end_page=self.spin_end.value() if mode == 1 else 1,
            pages_per_file=self.spin_pages.value() if mode == 2 else 1
        )
        
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.error_signal.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, message: str) -> None:
        """Gestisce il completamento dello split."""
        self.pbar.setValue(100)
        self.status_label.setText("Completato.")
        self.btn_split.setEnabled(True)
        self.show_info(message, "Successo")

    def _on_error(self, error: str) -> None:
        """Gestisce gli errori durante lo split."""
        self.status_label.setText("Errore.")
        self.btn_split.setEnabled(True)
        self.show_error(error)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = PDFSplitterApp()
    window.show()
    sys.exit(app.exec())
