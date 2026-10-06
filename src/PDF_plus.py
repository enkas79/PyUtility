"""
PDF Plus Module
==============
Tool per unire più file PDF in un unico file, con supporto per split automatico se >99MB.
"""

import sys
import os
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QProgressBar, QLineEdit
)
from PyQt6.QtCore import QThread, Qt, pyqtSignal

from base_window import BaseWindow
from pdf_core import merge_pdfs


class MergeWorker(QThread):
    """
    Thread per eseguire il merge dei PDF in background (logica in pdf_core).

    Attributes:
        done (pyqtSignal): Emesso al completamento con la lista dei file creati.
        error (pyqtSignal): Segnale emesso in caso di errore.
        progress (pyqtSignal): Segnale per aggiornare lo stato.
    """
    done = pyqtSignal(list)
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
            created = merge_pdfs(
                self.file_list, self.dest_path,
                on_progress=lambda n, total: self.progress.emit(f"Uniti {n} di {total} file..."),
            )
            self.done.emit(created)
        except Exception as e:  # noqa: BLE001 - confine del thread: nessun crash (es. DecompressionBombError)
            self.error.emit(str(e))


class PDFPlusPro(BaseWindow):
    """
    Applicazione per unire file PDF.
    
    Attributes:
        selected_files (List[str]): Lista dei file PDF selezionati.
    """

    GUIDE_TEXT = (
        "1. Aggiungi i PDF da unire con 'File' (selezione multipla) o 'Cartella' "
        "(tutti i PDF contenuti).\n"
        "2. Scegli la cartella di destinazione con 'Sfoglia'.\n"
        "3. Premi 'UNISCI'.\n\n"
        "Se il PDF risultante supera i 99 MB viene diviso automaticamente in più file "
        "(stima sulla dimensione dei sorgenti: un singolo PDF oltre i 99 MB resta intero).\n"
        "I file creati si chiamano '01 - Main.pdf', '02 - Main.pdf', ... senza sovrascrivere quelli esistenti.\n"
        "'Reset' svuota la coda dei file."
    )

    def __init__(self) -> None:
        """Inizializza l'applicazione PDFPlusPro."""
        super().__init__('PDF Plus', min_width=400, min_height=500)
        self.selected_files: List[str] = []
        self.worker: Optional[MergeWorker] = None
        self.initUI()

    def initUI(self) -> None:
        """Inizializza l'interfaccia utente."""
        layout = self.create_vertical_layout(margins=(16, 8, 16, 16), spacing=12)
        layout.setMenuBar(self.create_menu_bar())

        title = QLabel("📄 PDF Plus")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        subtitle = QLabel("Unisci più PDF in un unico documento")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Pulsanti per aggiungere file/cartelle
        input_btns = QHBoxLayout()
        btn_add = QPushButton("📄 File")
        btn_add.setObjectName("primaryBtn")
        btn_add.clicked.connect(self.add_files)
        btn_fold = QPushButton("📂 Cartella")
        btn_fold.setObjectName("primaryBtn")
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
        layout.addStretch()

        # Pulsanti azione
        btn_lay = QHBoxLayout()
        self.btn_run = QPushButton("🚀 UNISCI")
        self.btn_run.setObjectName("successBtn")
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
        self.worker.done.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, created: List[str]) -> None:
        """
        Slot eseguito al completamento del merge.

        Args:
            created (List[str]): Percorsi dei file PDF creati.
        """
        self.pbar.setRange(0, 100)
        self.pbar.setValue(100)
        self.status_label.setText(f"Completato: {len(created)} file creati.")
        names = "\n".join(f"• {os.path.basename(p)}" for p in created)
        QMessageBox.information(
            self, "Fatto!",
            f"Creati {len(created)} PDF in:\n{self.dst_edit.text()}\n\n{names}")
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
