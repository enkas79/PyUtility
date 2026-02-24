import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QProgressBar, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyPDF2 import PdfReader, PdfWriter

class MergeWorker(QThread):
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_list, dest_path):
        super().__init__()
        self.file_list, self.dest_path = file_list, dest_path

    def run(self):
        try:
            max_size, current_size, counter, merger, count = 99 * 1024 * 1024, 0, 1, PdfWriter(), 0
            while os.path.exists(os.path.join(self.dest_path, f"{counter:02d} - Main.pdf")): counter += 1
            for path in self.file_list:
                self.progress.emit(f"Unendo: {os.path.basename(path)}")
                reader, size = PdfReader(path), os.path.getsize(path)
                if current_size + size > max_size and len(merger.pages) > 0:
                    with open(os.path.join(self.dest_path, f"{counter:02d} - Main.pdf"), "wb") as f: merger.write(f)
                    counter += 1; count += 1; merger = PdfWriter(); current_size = 0
                for page in reader.pages: merger.add_page(page)
                current_size += size
            if len(merger.pages) > 0:
                with open(os.path.join(self.dest_path, f"{counter:02d} - Main.pdf"), "wb") as f: merger.write(f)
                count += 1
            self.finished.emit(count)
        except Exception as e: self.error.emit(str(e))

class PDFPlusPro(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = []
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
        input_btns = QHBoxLayout()
        btn_add = QPushButton("📄 File"); btn_add.clicked.connect(self.add_files)
        btn_fold = QPushButton("📂 Cartella"); btn_fold.clicked.connect(self.add_folder)
        btn_res = QPushButton("🗑️ Reset"); btn_res.setObjectName("resetBtn"); btn_res.clicked.connect(self.reset_list)
        input_btns.addWidget(btn_add); input_btns.addWidget(btn_fold); input_btns.addWidget(btn_res)
        layout.addLayout(input_btns)
        self.info_label = QLabel("Nessun file selezionato")
        layout.addWidget(self.info_label)
        dst_lay = QHBoxLayout(); self.dst_edit = QLineEdit(); btn_dst = QPushButton("Sfoglia"); btn_dst.clicked.connect(self.select_dest)
        dst_lay.addWidget(self.dst_edit); dst_lay.addWidget(btn_dst); layout.addLayout(dst_lay)
        self.status_label = QLabel("In attesa..."); layout.addWidget(self.status_label)
        self.pbar = QProgressBar(); layout.addWidget(self.pbar)
        btn_lay = QHBoxLayout(); self.btn_run = QPushButton("🚀 UNISCI"); self.btn_run.clicked.connect(self.start_merge)
        btn_exit = QPushButton("Esci"); btn_exit.setObjectName("exitBtn"); btn_exit.clicked.connect(self.close)
        btn_lay.addWidget(self.btn_run); btn_lay.addWidget(btn_exit); layout.addLayout(btn_lay)
        self.setLayout(layout)

    def add_files(self):
        f, _ = QFileDialog.getOpenFileNames(self, "Seleziona", "", "PDF (*.pdf)")
        if f: self.selected_files.extend(f); self.update_info()
    def add_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Cartella")
        if d: self.selected_files.extend([os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith('.pdf')]); self.update_info()
    def reset_list(self): self.selected_files = []; self.update_info(); self.pbar.setValue(0)
    def update_info(self): self.info_label.setText(f"File in coda: {len(self.selected_files)}")
    def select_dest(self):
        p = QFileDialog.getExistingDirectory(self, "Destinazione")
        if p: self.dst_edit.setText(p)
    def start_merge(self):
        if not self.selected_files or not self.dst_edit.text(): return
        self.btn_run.setEnabled(False); self.pbar.setRange(0, 0)
        self.worker = MergeWorker(self.selected_files, self.dst_edit.text())
        self.worker.progress.connect(self.status_label.setText); self.worker.finished.connect(self.on_success); self.worker.start()
    def on_success(self, count):
        self.pbar.setRange(0, 100); self.pbar.setValue(100); QMessageBox.information(self, "Fatto!", f"Creati {count} PDF."); self.btn_run.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = PDFPlusPro(); ex.show(); sys.exit(app.exec())