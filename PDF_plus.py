import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QProgressBar, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyPDF2 import PdfReader, PdfWriter


# --- THREAD PER L'UNIONE ---
class MergeWorker(QThread):
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_list, dest_path):
        super().__init__()
        self.file_list = file_list
        self.dest_path = dest_path

    def run(self):
        try:
            if not self.file_list:
                self.error.emit("Nessun file selezionato.")
                return

            max_size_bytes = 99 * 1024 * 1024  # Limite 99 MB
            output_file_counter = 1
            current_merger = PdfWriter()
            current_size = 0
            final_files_count = 0

            # Trova il primo nome disponibile
            while os.path.exists(os.path.join(self.dest_path, f"{output_file_counter:02d} - Main.pdf")):
                output_file_counter += 1

            for path in self.file_list:
                self.progress.emit(f"Unendo: {os.path.basename(path)}")
                reader = PdfReader(path)
                file_size = os.path.getsize(path)

                # Controllo dimensione per split 99MB
                if current_size + file_size > max_size_bytes and len(current_merger.pages) > 0:
                    out_name = os.path.join(self.dest_path, f"{output_file_counter:02d} - Main.pdf")
                    with open(out_name, "wb") as f:
                        current_merger.write(f)
                    output_file_counter += 1
                    final_files_count += 1
                    current_merger = PdfWriter()
                    current_size = 0

                for page in reader.pages:
                    current_merger.add_page(page)
                current_size += file_size

            # Salvataggio finale
            if len(current_merger.pages) > 0:
                out_name = os.path.join(self.dest_path, f"{output_file_counter:02d} - Main.pdf")
                with open(out_name, "wb") as f:
                    current_merger.write(f)
                final_files_count += 1

            self.finished.emit(final_files_count)
        except Exception as e:
            self.error.emit(str(e))


# --- INTERFACCIA ---
class PDFPlusPro(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = []  # Lista che contiene i percorsi dei file
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF Plus')
        self.setFixedSize(550, 450)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Segoe UI'; }
            QPushButton { background-color: #0078d4; border-radius: 4px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1e90ff; }
            QPushButton#resetBtn { background-color: #555; }
            QPushButton#exitBtn { background-color: #c62828; }
            QProgressBar { border: 1px solid #444; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #00c853; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Selezione Input
        layout.addWidget(QLabel("1. Aggiungi i file PDF:"))
        input_btns = QHBoxLayout()

        btn_add_files = QPushButton("📄 Seleziona File")
        btn_add_files.clicked.connect(self.add_files)

        btn_add_folder = QPushButton("📂 Intera Cartella")
        btn_add_folder.clicked.connect(self.add_folder)

        btn_reset = QPushButton("🗑️ Reset")
        btn_reset.setObjectName("resetBtn")
        btn_reset.clicked.connect(self.reset_list)

        input_btns.addWidget(btn_add_files)
        input_btns.addWidget(btn_add_folder)
        input_btns.addWidget(btn_reset)
        layout.addLayout(input_btns)

        # Riepilogo file
        self.info_label = QLabel("Nessun file selezionato")
        self.info_label.setStyleSheet("color: #00c853; font-weight: bold;")
        layout.addWidget(self.info_label)

        # Destinazione
        layout.addWidget(QLabel("2. Cartella di destinazione:"))
        dst_lay = QHBoxLayout()
        self.dst_edit = QLineEdit()
        btn_dst = QPushButton("Sfoglia")
        btn_dst.clicked.connect(self.select_dest)
        dst_lay.addWidget(self.dst_edit)
        dst_lay.addWidget(btn_dst)
        layout.addLayout(dst_lay)

        # Progresso
        self.status_label = QLabel("In attesa...")
        layout.addWidget(self.status_label)
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)

        # Azioni Finali
        btn_lay = QHBoxLayout()
        self.btn_run = QPushButton("🚀 UNISCI")
        self.btn_run.setFixedHeight(45)
        self.btn_run.clicked.connect(self.start_merge)

        btn_exit = QPushButton("Esci")
        btn_exit.setObjectName("exitBtn")
        btn_exit.setFixedHeight(45)
        btn_exit.clicked.connect(self.close)

        btn_lay.addWidget(self.btn_run)
        btn_lay.addWidget(btn_exit)
        layout.addLayout(btn_lay)

        self.setLayout(layout)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona PDF", "", "PDF Files (*.pdf)")
        if files:
            self.selected_files.extend(files)
            self.update_info()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleziona Cartella")
        if folder:
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf')]
            self.selected_files.extend(files)
            self.update_info()

    def reset_list(self):
        self.selected_files = []
        self.update_info()
        self.pbar.setValue(0)

    def update_info(self):
        count = len(self.selected_files)
        self.info_label.setText(f"File in coda: {count}")

    def select_dest(self):
        path = QFileDialog.getExistingDirectory(self, "Destinazione")
        if path: self.dst_edit.setText(path)

    def start_merge(self):
        if not self.selected_files or not self.dst_edit.text():
            QMessageBox.warning(self, "Mancano dati", "Seleziona i file e la cartella di destinazione!")
            return

        self.btn_run.setEnabled(False)
        self.pbar.setRange(0, 0)

        self.worker = MergeWorker(self.selected_files, self.dst_edit.text())
        self.worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, count):
        self.pbar.setRange(0, 100)
        self.pbar.setValue(100)
        QMessageBox.information(self, "Fatto!", f"Operazione conclusa.\nCreati {count} file PDF.")
        self.btn_run.setEnabled(True)

    def on_error(self, msg):
        self.pbar.setRange(0, 100)
        QMessageBox.critical(self, "Errore", msg)
        self.btn_run.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFPlusPro()
    ex.show()
    sys.exit(app.exec())