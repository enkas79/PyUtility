import sys
import os
import shutil
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QLineEdit, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt


# --- 1. WORKER PER LA RICERCA (Processo in Background) ---
class SearchWorker(QThread):
    found_signal = pyqtSignal(str, str)  # Segnale: (nome_file, percorso_completo)
    finished_signal = pyqtSignal(int)  # Segnale: totale trovati

    def __init__(self, start_dir, extension, keyword):
        super().__init__()
        self.start_dir = start_dir
        self.extension = extension.lower()
        self.keyword = keyword.lower()
        self.is_running = True

    def run(self):
        count = 0
        for root, _, files in os.walk(self.start_dir):
            if not self.is_running: break

            for filename in files:
                # Filtro Estensione
                if self.extension != "tutte" and not filename.lower().endswith(self.extension):
                    continue
                # Filtro Parola Chiave
                if self.keyword and self.keyword not in filename.lower():
                    continue

                # File Trovato
                full_path = os.path.join(root, filename)
                self.found_signal.emit(filename, full_path)
                count += 1

        self.finished_signal.emit(count)

    def stop(self):
        self.is_running = False


# --- 2. INTERFACCIA GRAFICA ---
class FileManagerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Gestore File Avanzato')
        self.resize(1000, 700)  # Finestra bella grande

        # --- DEFINIZIONE STILE (CSS) ---
        # Qui definiamo i colori. Nota la sezione specifica per #exitBtn
        self.setStyleSheet("""
            QWidget { 
                background-color: #2b2b2b; 
                color: #ffffff; 
                font-family: 'Segoe UI', sans-serif; 
            }
            QLineEdit, QComboBox { 
                padding: 6px; 
                border-radius: 4px; 
                background-color: #404040; 
                border: 1px solid #555; 
                color: white; 
            }
            QTableWidget { 
                background-color: #1e1e1e; 
                gridline-color: #444; 
                border: 1px solid #555; 
            }
            QHeaderView::section { 
                background-color: #333; 
                padding: 4px; 
                border: 1px solid #444; 
                color: #ccc; 
            }
            QTableWidget::item:selected { 
                background-color: #0078d4; 
            }

            /* Stile Base Bottoni */
            QPushButton { 
                background-color: #444; 
                color: white;
                padding: 8px 15px; 
                border-radius: 4px; 
                font-weight: bold; 
                border: 1px solid #555; 
            }
            QPushButton:hover { 
                background-color: #555; 
            }

            /* Bottoni Specifici */
            QPushButton#searchBtn { background-color: #0078d4; border: none; }
            QPushButton#searchBtn:hover { background-color: #1e90ff; }

            QPushButton#moveBtn { background-color: #d81b60; border: none; } 
            QPushButton#copyBtn { background-color: #00c853; border: none; }

            /* --- PULSANTE ESCI ROSSO --- */
            QPushButton#exitBtn { 
                background-color: #D32F2F; 
                border: 1px solid #B71C1C;
                font-size: 13px;
            }
            QPushButton#exitBtn:hover { 
                background-color: #FF5252; 
            }
        """)

        # Layout Principale Verticale
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ---------------------------------------------------------
        # PARTE ALTA: BARRA DI RICERCA
        # ---------------------------------------------------------
        search_layout = QHBoxLayout()

        self.src_edit = QLineEdit(os.path.expanduser("~\\Documents"))
        btn_src = QPushButton("📂 Cerca in...")
        btn_src.clicked.connect(lambda: self.select_folder(self.src_edit))

        self.combo_ext = QComboBox()
        self.combo_ext.addItems(["Tutte", ".pdf", ".docx", ".xlsx", ".txt", ".jpg", ".png"])

        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Parola chiave (opzionale)")

        self.btn_search = QPushButton("🔍 Cerca")
        self.btn_search.setObjectName("searchBtn")  # ID per il colore Blu
        self.btn_search.clicked.connect(self.start_search)

        # Aggiunta widget alla barra di ricerca
        search_layout.addWidget(self.src_edit, 2)  # Il 2 indica che prende più spazio
        search_layout.addWidget(btn_src)
        search_layout.addWidget(self.combo_ext)
        search_layout.addWidget(self.keyword_edit, 1)
        search_layout.addWidget(self.btn_search)

        main_layout.addLayout(search_layout)

        # ---------------------------------------------------------
        # PARTE CENTRALE: TABELLA RISULTATI
        # ---------------------------------------------------------
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Nome File", "Percorso Completo (Location)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Seleziona tutta la riga
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)  # Selezione multipla
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Sola lettura

        main_layout.addWidget(self.table)

        self.status_label = QLabel("Pronto. Imposta i filtri e cerca.")
        main_layout.addWidget(self.status_label)

        # ---------------------------------------------------------
        # PARTE BASSA: AZIONI E PULSANTE ESCI
        # ---------------------------------------------------------
        # Creiamo un contenitore grigio scuro per i comandi in basso
        action_box = QFrame()
        action_box.setStyleSheet("background-color: #383838; border-radius: 8px;")
        action_layout = QHBoxLayout(action_box)
        action_layout.setContentsMargins(10, 10, 10, 10)

        # 1. Selezione destinazione
        action_layout.addWidget(QLabel("Destinazione:"))
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText("Cartella dove spostare/copiare...")
        action_layout.addWidget(self.dst_edit)

        btn_dst = QPushButton("📂 Sfoglia")
        btn_dst.clicked.connect(lambda: self.select_folder(self.dst_edit))
        action_layout.addWidget(btn_dst)

        # 2. Pulsanti Azione (Sposta/Copia)
        self.btn_move = QPushButton("✂️ SPOSTA")
        self.btn_move.setObjectName("moveBtn")  # Magenta
        self.btn_move.clicked.connect(lambda: self.execute_action("move"))
        action_layout.addWidget(self.btn_move)

        self.btn_copy = QPushButton("📑 COPIA")
        self.btn_copy.setObjectName("copyBtn")  # Verde
        self.btn_copy.clicked.connect(lambda: self.execute_action("copy"))
        action_layout.addWidget(self.btn_copy)

        # 3. Spaziatore (spinge il tasto Esci tutto a destra)
        action_layout.addStretch()

        # 4. Pulsante ESCI (Rosso)
        self.btn_exit = QPushButton("Esci")
        self.btn_exit.setObjectName("exitBtn")  # ID CRUCIALE PER IL COLORE ROSSO
        self.btn_exit.setFixedWidth(100)
        self.btn_exit.clicked.connect(self.close)
        action_layout.addWidget(self.btn_exit)

        main_layout.addWidget(action_box)

        self.setLayout(main_layout)

    # --- LOGICA APPLICAZIONE ---

    def select_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Seleziona Cartella")
        if folder: line_edit.setText(folder)

    def start_search(self):
        src = self.src_edit.text()
        if not os.path.exists(src):
            QMessageBox.warning(self, "Errore", "Seleziona una cartella di ricerca valida.")
            return

        self.table.setRowCount(0)  # Pulisce la tabella
        self.btn_search.setEnabled(False)
        self.status_label.setText("⏳ Ricerca in corso...")

        self.worker = SearchWorker(src, self.combo_ext.currentText(), self.keyword_edit.text())
        self.worker.found_signal.connect(self.add_table_row)
        self.worker.finished_signal.connect(self.on_search_finished)
        self.worker.start()

    def add_table_row(self, name, path):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(path))

    def on_search_finished(self, count):
        self.status_label.setText(f"✅ Ricerca completata. Trovati {count} file.")
        self.btn_search.setEnabled(True)

    def execute_action(self, mode):
        dest_dir = self.dst_edit.text()
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)

        if not selected_rows:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un file dalla lista!")
            return
        if not dest_dir or not os.path.exists(dest_dir):
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella di destinazione valida!")
            return

        action_name = "SPOSTARE" if mode == "move" else "COPIARE"
        confirm = QMessageBox.question(self, "Conferma",
                                       f"Vuoi davvero {action_name} {len(selected_rows)} file?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            success_count = 0
            errors = 0

            for row in selected_rows:
                file_name = self.table.item(row, 0).text()
                src_path = self.table.item(row, 1).text()
                dest_path = os.path.join(dest_dir, file_name)

                try:
                    if mode == "move":
                        shutil.move(src_path, dest_path)
                        self.table.removeRow(row)  # Rimuovi dalla tabella se spostato
                    else:
                        shutil.copy2(src_path, dest_path)
                    success_count += 1
                except Exception as e:
                    errors += 1
                    print(f"Errore: {e}")

            QMessageBox.information(self, "Finito",
                                    f"Operazione completata.\nSuccessi: {success_count}\nErrori: {errors}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileManagerApp()
    ex.show()
    sys.exit(app.exec())