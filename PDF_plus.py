"""
PDF Plus Module
==============
Tool per unire più file PDF in un unico file, con supporto per split automatico se >99MB.
"""

import sys
import os
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QProgressBar, QLineEdit
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyPDF2 import PdfReader, PdfWriter


class MergeWorker(QThread):
    """
    Thread per eseguire il merge dei PDF in background.
    
    Attributes:
        finished (pyqtSignal): Segnale emesso al completamento con il numero di file creati.
        error (pyqtSignal): Segnale emesso in caso di errore.
        progress (pyqtSignal): Segnale per aggiornare lo stato.
    """
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_list: List[str], dest_path: str) -> None:
        """
        Inizializza il worker per il merge dei PDF.
        
        Args:
            file_list (List[str]): Lista dei percorsi dei file PDF da unire.
            dest_path (str): Cartella di destinazione per i file uniti.
        """
        super().__init__()
        self.file_list: List[str] = file_list
        self.dest_path: str = dest_path

    def run(self) -> None:
        """Esegue il merge dei PDF con split automatico se >99MB."""
        try:
            max_size: int = 99 * 1024 * 1024  # 99MB
            current_size: int = 0
            counter: int = 1
            merger: PdfWriter = PdfWriter()
            count: int = 0
            
            # Trova il primo nome file disponibile
            while os.path.exists(os.path.join(self.dest_path, f"{counter:02d} - Main.pdf")):
                counter += 1
            
            for path in self.file_list:
                self.progress.emit(f"Unendo: {os.path.basename(path)}")
                reader: PdfReader = PdfReader(path)
                size: int = os.path.getsize(path)
                
                # Se supera il limite, salva il file corrente e ne inizia uno nuovo
                if current_size + size > max_size and len(merger.pages) > 0:
                    with open(os.path.join(self.dest_path, f"{counter:02d} - Main.pdf"), "wb") as f:
                        merger.write(f)
                    counter += 1
                    count += 1
                    merger = PdfWriter()
                    current_size = 0
                
                # Aggiungi le pagine del file corrente
                for page in reader.pages:
                    merger.add_page(page)
                current_size += size
            
            # Salva l'ultimo file se ci sono pagine
            if len(merger.pages) > 0:
                with open(os.path.join(self.dest_path, f"{counter:02d} - Main.pdf"), "wb") as f:
                    merger.write(f)
                count += 1
            
            self.finished.emit(count)
            
        except Exception as e:
            self.error.emit(str(e))


class PDFPlusPro(QWidget):
    """
    Applicazione per unire file PDF.
    
    Attributes:
        selected_files (List[str]): Lista dei file PDF selezionati.
    """

    def __init__(self) -> None:
        """Inizializza l'applicazione PDFPlusPro."""
        super().__init__()
        self.selected_files: List[str] = []
        self.worker: Optional[MergeWorker] = None
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

        self.setWindowTitle('PDF Plus')
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Segoe UI'; }
            QPushButton { background-color: #0078d4; border-radius: 4px; padding: 8px; font-weight: bold; }
            QPushButton#resetBtn { background-color: #555; }
            QPushButton#exitBtn { background-color: #c62828; }
            QProgressBar { border: 1px solid #444; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #00c853; }
        """)
        
        layout = QVBoxLayout()
        
        # Pulsanti per aggiungere file/cartelle
        input_btns = QHBoxLayout()
        btn_add = QPushButton("📄 File")
        btn_add.clicked.connect(self.add_files)
        btn_fold = QPushButton("📂 Cartella")
        btn_fold.clicked.connect(self.add_folder)
        btn_res = QPushButton("🗑️ Reset")
        btn_res.setObjectName("resetBtn")
        btn_res.clicked.connect(self.reset_list)
        input_btns.addWidget(btn_add)
        input_btns.addWidget(btn_fold)
        input_btns.addWidget(btn_res)
        layout.addLayout(input_btns)
        
        # Label informativo
        self.info_label = QLabel("Nessun file selezionato")
        layout.addWidget(self.info_label)
        
        # Sezione cartella di output
        dst_lay = QHBoxLayout()
        self.dst_edit = QLineEdit()
        btn_dst = QPushButton("Sfoglia")
        btn_dst.clicked.connect(self.select_dest)
        dst_lay.addWidget(self.dst_edit)
        dst_lay.addWidget(btn_dst)
        layout.addLayout(dst_lay)
        
        # Barra di stato e progresso
        self.status_label = QLabel("In attesa...")
        layout.addWidget(self.status_label)
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        
        # Pulsanti azione
        btn_lay = QHBoxLayout()
        self.btn_run = QPushButton("🚀 UNISCI")
        self.btn_run.clicked.connect(self.start_merge)
        btn_exit = QPushButton("Esci")
        btn_exit.setObjectName("exitBtn")
        btn_exit.clicked.connect(self.close)
        btn_lay.addWidget(self.btn_run)
        btn_lay.addWidget(btn_exit)
        layout.addLayout(btn_lay)
        
        self.setLayout(layout)

    def add_files(self) -> None:
        """Aggiunge file PDF singoli alla lista."""
        files: List[str] = QFileDialog.getOpenFileNames(
            self, "Seleziona", "", "PDF (*.pdf)"
        )[0]
        if files:
            self.selected_files.extend(files)
            self.update_info()

    def add_folder(self) -> None:
        """Aggiunge tutti i PDF da una cartella alla lista."""
        directory: Optional[str] = QFileDialog.getExistingDirectory(self, "Cartella")
        if directory:
            self.selected_files.extend([
                os.path.join(directory, f) 
                for f in os.listdir(directory) 
                if f.lower().endswith('.pdf')
            ])
            self.update_info()

    def reset_list(self) -> None:
        """Svuota la lista dei file selezionati."""
        self.selected_files: List[str] = []
        self.update_info()
        self.pbar.setValue(0)

    def update_info(self) -> None:
        """Aggiorna la label con il numero di file selezionati."""
        self.info_label.setText(f"File in coda: {len(self.selected_files)}")

    def select_dest(self) -> None:
        """Seleziona la cartella di destinazione per i file uniti."""
        path: Optional[str] = QFileDialog.getExistingDirectory(self, "Destinazione")
        if path:
            self.dst_edit.setText(path)

    def start_merge(self) -> None:
        """Avvia il processo di merge dei PDF."""
        if not self.selected_files or not self.dst_edit.text():
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un file PDF e una cartella di destinazione.")
            return
        
        self.btn_run.setEnabled(False)
        self.pbar.setRange(0, 0)  # Modalità indeterminata
        
        self.worker = MergeWorker(self.selected_files, self.dst_edit.text())
        self.worker.progress.connect(self.status_label.setText)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, count: int) -> None:
        """
        Slot eseguito al completamento del merge.
        
        Args:
            count (int): Numero di file PDF creati.
        """
        self.pbar.setRange(0, 100)
        self.pbar.setValue(100)
        QMessageBox.information(self, "Fatto!", f"Creati {count} PDF.")
        self.btn_run.setEnabled(True)

    def on_error(self, error: str) -> None:
        """
        Slot eseguito in caso di errore durante il merge.
        
        Args:
            error (str): Messaggio di errore.
        """
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        QMessageBox.critical(self, "Errore", f"Si è verificato un errore: {error}")
        self.btn_run.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFPlusPro()
    ex.show()
    sys.exit(app.exec())
