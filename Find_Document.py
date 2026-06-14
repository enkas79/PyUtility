"""
File Manager Module
===================
Tool per la ricerca e gestione di documenti con filtri per estensione e parole chiave.
"""

import sys
import os
import shutil
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt


class SearchWorker(QThread):
    """
    Thread per eseguire la ricerca dei file in background.
    
    Attributes:
        found_signal (pyqtSignal): Segnale emesso quando un file viene trovato.
        finished_signal (pyqtSignal): Segnale emesso al completamento della ricerca.
    """
    found_signal = pyqtSignal(str, str)  # Emette (nome_file, percorso_completo)
    finished_signal = pyqtSignal(int)    # Emette il numero totale di file trovati

    def __init__(self, start_dir: str, extension: str, keyword: str) -> None:
        """
        Inizializza il worker per la ricerca dei file.
        
        Args:
            start_dir (str): Directory di partenza per la ricerca.
            extension (str): Estensione dei file da cercare (es. ".pdf").
            keyword (str): Parola chiave per filtrare i file.
        """
        super().__init__()
        self.start_dir = start_dir
        self.extension = extension.lower()
        self.keyword = keyword.lower()
        self.is_running: bool = True

    def run(self) -> None:
        """Esegue la ricerca ricorsiva dei file."""
        count: int = 0
        for root, _, files in os.walk(self.start_dir):
            if not self.is_running:
                break
            for filename in files:
                if self.extension != "tutte" and not filename.lower().endswith(self.extension):
                    continue
                if self.keyword and self.keyword not in filename.lower():
                    continue
                self.found_signal.emit(filename, os.path.join(root, filename))
                count += 1
        self.finished_signal.emit(count)

    def stop(self) -> None:
        """Ferma la ricerca in corso."""
        self.is_running = False


class FileManagerApp(QWidget):
    """
    Applicazione per la ricerca e gestione dei file.
    
    Attributes:
        worker (SearchWorker): Thread per la ricerca dei file.
    """

    def __init__(self) -> None:
        """Inizializza l'applicazione FileManager."""
        super().__init__()
        self.worker: Optional[SearchWorker] = None
        self.initUI()

    def initUI(self) -> None:
        """Inizializza l'interfaccia utente."""
        # --- LOGICA DIMENSIONI E CENTRATURA ---
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.20)
        height = int(screen.height() * 0.40)
        min_w, min_h = 500, 600
        self.setMinimumSize(min_w, min_h)
        self.resize(max(width, min_w), max(height, min_h))
        qr = self.frameGeometry()
        qr.moveCenter(screen.center())
        self.move(qr.topLeft())

        self.setWindowTitle('Gestore File Avanzato')
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QLineEdit, QComboBox { padding: 6px; border-radius: 4px; background-color: #404040; border: 1px solid #555; color: white; }
            QTableWidget { background-color: #1e1e1e; gridline-color: #444; border: 1px solid #555; }
            QHeaderView::section { background-color: #333; padding: 4px; border: 1px solid #444; color: #ccc; }
            QTableWidget::item:selected { background-color: #0078d4; }
            QPushButton { background-color: #444; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold; border: 1px solid #555; }
            QPushButton:hover { background-color: #555; }
            QPushButton#searchBtn { background-color: #0078d4; border: none; }
            QPushButton#moveBtn { background-color: #d81b60; border: none; } 
            QPushButton#copyBtn { background-color: #00c853; border: none; }
            QPushButton#exitBtn { background-color: #D32F2F; border: 1px solid #B71C1C; font-size: 13px; }
            QPushButton#exitBtn:hover { background-color: #FF5252; }
        """)

        main_layout = QVBoxLayout()
        
        # Sezione ricerca
        search_layout = QHBoxLayout()
        self.src_edit = QLineEdit(os.path.expanduser("~\\Documents"))
        btn_src = QPushButton("📂 Cerca in...")
        btn_src.clicked.connect(lambda: self.select_folder(self.src_edit))
        
        self.combo_ext = QComboBox()
        self.combo_ext.addItems(["Tutte", ".pdf", ".docx", ".xlsx", ".txt", ".jpg", ".png"])
        
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Parola chiave (opzionale)")
        
        self.btn_search = QPushButton("🔍 Cerca")
        self.btn_search.setObjectName("searchBtn")
        self.btn_search.clicked.connect(self.start_search)
        
        search_layout.addWidget(self.src_edit, 2)
        search_layout.addWidget(btn_src)
        search_layout.addWidget(self.combo_ext)
        search_layout.addWidget(self.keyword_edit, 1)
        search_layout.addWidget(self.btn_search)
        main_layout.addLayout(search_layout)
        
        # Tabella risultati
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Nome File", "Percorso Completo"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table)
        
        # Barra di stato
        self.status_label = QLabel("Pronto.")
        main_layout.addWidget(self.status_label)
        
        # Sezione azioni (copia/sposta)
        action_box = QFrame()
        action_box.setStyleSheet("background-color: #383838; border-radius: 8px;")
        action_layout = QHBoxLayout(action_box)
        
        self.dst_edit = QLineEdit()
        btn_dst = QPushButton("📂 Sfoglia")
        btn_dst.clicked.connect(lambda: self.select_folder(self.dst_edit))
        
        self.btn_move = QPushButton("✂️ SPOSTA")
        self.btn_move.setObjectName("moveBtn")
        self.btn_move.clicked.connect(lambda: self.execute_action("move"))
        
        self.btn_copy = QPushButton("📑 COPIA")
        self.btn_copy.setObjectName("copyBtn")
        self.btn_copy.clicked.connect(lambda: self.execute_action("copy"))
        
        action_layout.addWidget(self.dst_edit)
        action_layout.addWidget(btn_dst)
        action_layout.addWidget(self.btn_move)
        action_layout.addWidget(self.btn_copy)
        action_layout.addStretch()
        
        # Pulsante Esci
        self.btn_exit = QPushButton("Esci")
        self.btn_exit.setObjectName("exitBtn")
        self.btn_exit.setFixedWidth(100)
        self.btn_exit.clicked.connect(self.close)
        action_layout.addWidget(self.btn_exit)
        
        main_layout.addWidget(action_box)
        self.setLayout(main_layout)

    def select_folder(self, line_edit: QLineEdit) -> None:
        """
        Apre la dialog per selezionare una cartella e aggiorna il QLineEdit.
        
        Args:
            line_edit (QLineEdit): Campo di testo da aggiornare con il percorso selezionato.
        """
        folder: Optional[str] = QFileDialog.getExistingDirectory(self, "Seleziona")
        if folder:
            line_edit.setText(folder)

    def start_search(self) -> None:
        """Avvia la ricerca dei file in background."""
        if not os.path.exists(self.src_edit.text()):
            QMessageBox.warning(self, "Attenzione", "La directory di ricerca non esiste.")
            return
        
        self.table.setRowCount(0)
        self.btn_search.setEnabled(False)
        self.status_label.setText("⏳ Ricerca...")
        
        self.worker = SearchWorker(
            self.src_edit.text(),
            self.combo_ext.currentText(),
            self.keyword_edit.text()
        )
        self.worker.found_signal.connect(self.add_table_row)
        self.worker.finished_signal.connect(self.on_search_finished)
        self.worker.start()

    def add_table_row(self, name: str, path: str) -> None:
        """
        Aggiunge una riga alla tabella con il nome e il percorso del file trovato.
        
        Args:
            name (str): Nome del file.
            path (str): Percorso completo del file.
        """
        row: int = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(path))

    def on_search_finished(self, count: int) -> None:
        """
        Slot eseguito al completamento della ricerca.
        
        Args:
            count (int): Numero di file trovati.
        """
        self.status_label.setText(f"✅ Trovati {count} file.")
        self.btn_search.setEnabled(True)

    def execute_action(self, mode: str) -> None:
        """
        Esegue l'azione di copia o spostamento sui file selezionati.
        
        Args:
            mode (str): Modalità di azione ("copy" o "move").
        """
        dest_dir: str = self.dst_edit.text()
        rows: List[int] = sorted(
            set(index.row() for index in self.table.selectedIndexes()),
            reverse=True
        )
        
        if not rows or not os.path.exists(dest_dir):
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un file e una cartella di destinazione valida.")
            return
        
        if QMessageBox.question(
            self, "Conferma",
            f"Eseguire operazione su {len(rows)} file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            
            for r in rows:
                path: str = self.table.item(r, 1).text()
                try:
                    if mode == "move":
                        shutil.move(path, os.path.join(dest_dir, self.table.item(r, 0).text()))
                        self.table.removeRow(r)
                    else:  # copy
                        shutil.copy2(path, dest_dir)
                except Exception as e:
                    QMessageBox.warning(self, "Errore", f"Errore durante l'operazione su {path}: {str(e)}")
            
            QMessageBox.information(self, "Finito", "Operazione completata.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileManagerApp()
    ex.show()
    sys.exit(app.exec())
