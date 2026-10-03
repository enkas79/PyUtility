"""
File Manager Module
===================
Tool per la ricerca e gestione di documenti con filtri per estensione e parole chiave.
Scansione e copia/spostamento avvengono in background (file_workers) usando
la logica condivisa di file_lister_core.
"""

import os
import sys
from typing import List, Optional, Set

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QFileDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QProgressBar, QPushButton, QTableWidget, QTableWidgetItem,
)

from base_window import BaseWindow, SortableTableItem
from file_lister_core import FileEntry, FileListOptions, format_size, parse_extensions
from file_workers import ScanWorker, TransferWorker

# Voci predefinite del filtro estensione (il campo è comunque editabile)
EXTENSION_CHOICES = ["Tutte", ".pdf", ".docx", ".xlsx", ".txt", ".jpg", ".png"]
PATH_ROLE = Qt.ItemDataRole.UserRole  # percorso completo salvato nella cella "Nome"


class FileManagerApp(BaseWindow):
    """Ricerca file per estensione/parola chiave e copia o sposta i risultati."""

    COLUMNS = ["Nome File", "Dimensione", "Percorso Completo"]
    GUIDE_TEXT = (
        "1. Scegli la cartella in cui cercare.\n"
        "2. Scegli o digita le estensioni (es. 'pdf, docx'; 'Tutte' = nessun filtro) "
        "e, se vuoi, una parola chiave contenuta nel nome.\n"
        "3. Premi 'Cerca' (o Invio nel campo parola chiave).\n"
        "4. Seleziona i file nella tabella, indica la destinazione e premi COPIA o SPOSTA.\n\n"
        "I file omonimi nella destinazione non vengono sovrascritti: "
        "viene aggiunto un suffisso ' (1)', ' (2)', ..."
    )

    def __init__(self) -> None:
        super().__init__("Gestore File Avanzato", min_width=720, min_height=600)
        self.scan_worker: Optional[ScanWorker] = None
        self.transfer_worker: Optional[TransferWorker] = None
        self.found_count: int = 0
        self._init_ui()
        self._update_buttons()

    # ---------------------------------------------------------------- UI
    def _init_ui(self) -> None:
        layout = self.create_vertical_layout(margins=(16, 8, 16, 16), spacing=12)
        layout.setMenuBar(self.create_menu_bar())

        title = QLabel("🔍 Ricerca/Gestione Documenti")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Sezione ricerca
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        default_dir = os.path.join(os.path.expanduser("~"), "Documents")
        self.src_edit = QLineEdit(default_dir if os.path.isdir(default_dir) else os.path.expanduser("~"))
        btn_src = QPushButton("📂 Cerca in...")
        btn_src.clicked.connect(lambda: self._select_folder(self.src_edit))
        search_row.addWidget(self.src_edit, 1)
        search_row.addWidget(btn_src)
        layout.addLayout(search_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        self.combo_ext = QComboBox()
        self.combo_ext.setEditable(True)  # consente estensioni libere (es. "pdf, odt")
        self.combo_ext.addItems(EXTENSION_CHOICES)
        self.combo_ext.setToolTip("Scegli o digita una o più estensioni separate da virgola")
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Parola chiave nel nome (opzionale)")
        self.keyword_edit.returnPressed.connect(self._start_search)
        self.chk_recursive = QCheckBox("Sottocartelle")
        self.chk_recursive.setChecked(True)
        self.btn_search = QPushButton("🔍 Cerca")
        self.btn_search.setObjectName("primaryBtn")
        self.btn_search.clicked.connect(self._start_search)
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("dangerBtn")
        self.btn_stop.clicked.connect(self._stop_all)
        filter_row.addWidget(self.combo_ext)
        filter_row.addWidget(self.keyword_edit, 1)
        filter_row.addWidget(self.chk_recursive)
        filter_row.addWidget(self.btn_search)
        filter_row.addWidget(self.btn_stop)
        layout.addLayout(filter_row)

        # Tabella risultati
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        layout.addWidget(self.table, 1)

        self.status_label = QLabel("Pronto.")
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Sezione azioni (copia/sposta)
        action_box = QFrame()
        action_layout = QHBoxLayout(action_box)
        action_layout.setContentsMargins(8, 8, 8, 8)
        action_layout.setSpacing(8)
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText("Cartella di destinazione")
        btn_dst = QPushButton("📂 Sfoglia")
        btn_dst.clicked.connect(lambda: self._select_folder(self.dst_edit))
        self.btn_move = QPushButton("✂️ SPOSTA")
        self.btn_move.setObjectName("moveBtn")
        self.btn_move.clicked.connect(lambda: self._start_transfer("move"))
        self.btn_copy = QPushButton("📑 COPIA")
        self.btn_copy.setObjectName("copyBtn")
        self.btn_copy.clicked.connect(lambda: self._start_transfer("copy"))
        btn_exit = QPushButton("Esci")
        btn_exit.setObjectName("exitBtn")
        btn_exit.clicked.connect(self.close)
        action_layout.addWidget(self.dst_edit, 1)
        action_layout.addWidget(btn_dst)
        action_layout.addWidget(self.btn_move)
        action_layout.addWidget(self.btn_copy)
        action_layout.addWidget(btn_exit)
        layout.addWidget(action_box)

        self.setLayout(layout)

    def _select_folder(self, line_edit: QLineEdit) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleziona cartella", line_edit.text())
        if folder:
            line_edit.setText(folder)

    def _is_busy(self) -> bool:
        return any(w is not None and w.isRunning() for w in (self.scan_worker, self.transfer_worker))

    def _update_buttons(self) -> None:
        """Abilita/disabilita i comandi in base allo stato corrente."""
        busy = self._is_busy()
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.btn_search.setEnabled(not busy)
        self.btn_stop.setEnabled(busy)
        self.btn_move.setEnabled(has_selection and not busy)
        self.btn_copy.setEnabled(has_selection and not busy)

    # --------------------------------------------------------- ricerca
    def _start_search(self) -> None:
        if self._is_busy():
            return
        folder = self.src_edit.text().strip()
        if not os.path.isdir(folder):
            self.show_warning("La directory di ricerca non esiste.")
            return
        ext_text = self.combo_ext.currentText()
        options = FileListOptions(
            folder=folder,
            extensions=frozenset() if ext_text.lower() == "tutte" else parse_extensions(ext_text),
            keyword=self.keyword_edit.text(),
            recursive=self.chk_recursive.isChecked(),
        )

        self.table.setRowCount(0)
        self.found_count = 0
        self.status_label.setText("⏳ Ricerca...")
        self.scan_worker = ScanWorker(options)
        self.scan_worker.batch_found.connect(self._add_batch)
        self.scan_worker.finished_scan.connect(self._on_search_finished)
        self.scan_worker.error.connect(self.show_error)
        self.scan_worker.finished.connect(self._update_buttons)
        self.scan_worker.start()
        self._update_buttons()

    def _add_batch(self, batch: List[FileEntry]) -> None:
        """Aggiunge un blocco di risultati alla tabella."""
        self.table.setSortingEnabled(False)  # evita riordini a ogni inserimento
        row = self.table.rowCount()
        self.table.setRowCount(row + len(batch))
        for entry in batch:
            name_item = QTableWidgetItem(entry.name)
            name_item.setData(PATH_ROLE, entry.path)
            self.table.setItem(row, 0, name_item)
            size_item = SortableTableItem(format_size(entry.size), entry.size)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)
            self.table.setItem(row, 2, QTableWidgetItem(entry.path))
            row += 1
        self.table.setSortingEnabled(True)
        self.found_count += len(batch)
        self.status_label.setText(f"⏳ {self.found_count} file trovati...")

    def _on_search_finished(self, cancelled: bool) -> None:
        prefix = "⏹ Ricerca interrotta" if cancelled else "✅ Trovati"
        self.status_label.setText(f"{prefix}: {self.found_count} file.")

    # --------------------------------------------------- copia/sposta
    def _selected_paths(self) -> List[str]:
        return [self.table.item(idx.row(), 0).data(PATH_ROLE)
                for idx in self.table.selectionModel().selectedRows()]

    def _start_transfer(self, mode: str) -> None:
        sources = self._selected_paths()
        dest_dir = self.dst_edit.text().strip()
        if not sources or not os.path.isdir(dest_dir):
            self.show_warning("Seleziona almeno un file e una cartella di destinazione valida.")
            return
        verbo = "Spostare" if mode == "move" else "Copiare"
        if QMessageBox.question(
            self, "Conferma", f"{verbo} {len(sources)} file in:\n{dest_dir}?\n\n"
            "I file omonimi già presenti non verranno sovrascritti.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return

        self.progress.setRange(0, len(sources))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.transfer_worker = TransferWorker(sources, dest_dir, mode)
        self.transfer_worker.progress.connect(lambda i, _n: self.progress.setValue(i))
        self.transfer_worker.done.connect(
            lambda n, completed, errors: self._on_transfer_done(mode, n, completed, errors))
        self.transfer_worker.error.connect(self.show_error)
        self.transfer_worker.finished.connect(self._update_buttons)
        self.transfer_worker.start()
        self._update_buttons()

    def _on_transfer_done(self, mode: str, done: int, completed: List[str], errors: List[str]) -> None:
        self.progress.setVisible(False)
        if mode == "move":
            self._remove_rows(set(completed))
        self.status_label.setText(f"✅ {done} file {'spostati' if mode == 'move' else 'copiati'}.")
        if errors:
            dettagli = "\n".join(errors[:10]) + (f"\n... e altri {len(errors) - 10}" if len(errors) > 10 else "")
            self.show_warning(f"{len(errors)} file non elaborati:\n\n{dettagli}", "Operazione parziale")
        else:
            self.show_info("Operazione completata.", "Finito")

    def _remove_rows(self, paths: Set[str]) -> None:
        """Rimuove dalla tabella le righe dei file spostati."""
        for row in range(self.table.rowCount() - 1, -1, -1):
            if self.table.item(row, 0).data(PATH_ROLE) in paths:
                self.table.removeRow(row)
        self.found_count = self.table.rowCount()

    # ------------------------------------------------------------ varie
    def _stop_all(self) -> None:
        for worker in (self.scan_worker, self.transfer_worker):
            if worker is not None and worker.isRunning():
                worker.stop()

    def closeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        """Ferma i thread in corso prima di chiudere la finestra."""
        self._stop_all()
        for worker in (self.scan_worker, self.transfer_worker):
            if worker is not None:
                worker.wait(3000)
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileManagerApp()
    ex.show()
    sys.exit(app.exec())
