"""
File Lister Module
==================
Tool per creare l'elenco dei file contenuti in una cartella, con filtri
per estensione e dimensione, ed esportazione in CSV/TXT.
La logica di scansione/esportazione risiede in file_lister_core.py.
"""

import os
import sys
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFileDialog, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMenuBar, QPushButton, QTableWidget, QTableWidgetItem,
)

from base_window import BaseWindow, SortableTableItem
from file_lister_core import (
    FileEntry, FileListOptions, export_csv, export_txt, format_size,
    parse_extensions, parse_size,
)
from file_workers import ExportWorker, ScanWorker

# Preset rapidi per il filtro estensioni
EXTENSION_PRESETS = {
    "Tutte le estensioni": "",
    "Documenti": "pdf docx doc odt rtf txt xlsx xls ods csv pptx",
    "Immagini": "jpg jpeg png gif bmp webp tiff svg ico",
    "Audio/Video": "mp3 wav flac aac ogg mp4 mkv avi mov wmv",
    "Archivi": "zip rar 7z tar gz bz2",
}
SIZE_UNITS = ["B", "KB", "MB", "GB"]


class FileListerApp(BaseWindow):
    """Finestra per generare, filtrare ed esportare l'elenco dei file di una cartella."""

    COLUMNS = ["Nome", "Estensione", "Dimensione", "Ultima modifica", "Percorso relativo"]
    GUIDE_TEXT = (
        "1. Scegli la cartella da analizzare.\n"
        "2. (Opzionale) Indica le estensioni separate da spazio, virgola o punto e virgola, "
        "oppure scegli un preset. Vuoto = tutte.\n"
        "3. (Opzionale) Imposta dimensione minima e/o massima: 0 = nessun limite. "
        "I limiti sono inclusivi.\n"
        "4. Premi 'Crea lista'. Puoi interrompere la scansione in qualsiasi momento.\n"
        "5. Clicca sulle intestazioni per ordinare, poi esporta in CSV (apribile con Excel) "
        "o TXT, oppure copia i percorsi negli appunti."
    )

    def __init__(self) -> None:
        super().__init__("Lista File Cartella", min_width=820, min_height=600)
        self.entries: List[FileEntry] = []
        self.total_size: int = 0
        self.scan_worker: Optional[ScanWorker] = None
        self.export_worker: Optional[ExportWorker] = None
        self._init_ui()
        self._update_buttons()

    # ---------------------------------------------------------------- UI
    def _init_ui(self) -> None:
        layout = self.create_vertical_layout(margins=(16, 8, 16, 16), spacing=12)
        layout.setMenuBar(self.create_menu_bar())

        title = QLabel("📋 Lista File Cartella")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Crea l'elenco dei file di una cartella filtrando per estensione e dimensione")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        # Riga 0: cartella
        grid.addWidget(QLabel("Cartella:"), 0, 0)
        self.folder_edit = QLineEdit(os.path.expanduser("~"))
        grid.addWidget(self.folder_edit, 0, 1, 1, 4)
        btn_browse = QPushButton("📂 Sfoglia")
        btn_browse.clicked.connect(self._select_folder)
        grid.addWidget(btn_browse, 0, 5)

        # Riga 1: estensioni
        grid.addWidget(QLabel("Estensioni:"), 1, 0)
        self.ext_edit = QLineEdit()
        self.ext_edit.setPlaceholderText("es. pdf, docx, jpg  (vuoto = tutte)")
        grid.addWidget(self.ext_edit, 1, 1, 1, 3)
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(list(EXTENSION_PRESETS))
        self.combo_preset.currentTextChanged.connect(
            lambda name: self.ext_edit.setText(EXTENSION_PRESETS[name]))
        grid.addWidget(self.combo_preset, 1, 4, 1, 2)

        # Riga 2: dimensione minima / massima (0 = nessun limite)
        grid.addWidget(QLabel("Dim. minima:"), 2, 0)
        self.min_spin, self.min_unit = self._size_inputs(grid, 2, 1, "KB")
        grid.addWidget(QLabel("Dim. massima:"), 2, 3, alignment=Qt.AlignmentFlag.AlignRight)
        self.max_spin, self.max_unit = self._size_inputs(grid, 2, 4, "MB")

        # Riga 3: opzioni
        self.chk_recursive = QCheckBox("Includi sottocartelle")
        self.chk_recursive.setChecked(True)
        self.chk_hidden = QCheckBox("Includi file nascosti")
        grid.addWidget(self.chk_recursive, 3, 1)
        grid.addWidget(self.chk_hidden, 3, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(4, 1)
        layout.addLayout(grid)

        # Pulsanti scansione
        scan_row = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 Crea lista")
        self.btn_scan.setObjectName("primaryBtn")
        self.btn_scan.clicked.connect(self._start_scan)
        self.btn_stop = QPushButton("⏹ Interrompi")
        self.btn_stop.setObjectName("dangerBtn")
        self.btn_stop.clicked.connect(self._stop_scan)
        scan_row.addWidget(self.btn_scan, 1)
        scan_row.addWidget(self.btn_stop)
        layout.addLayout(scan_row)

        # Tabella risultati
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        header = self.table.horizontalHeader()
        for col in range(len(self.COLUMNS) - 1):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(len(self.COLUMNS) - 1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header.setSortIndicator(0, Qt.SortOrder.AscendingOrder)  # default: nome A→Z
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        self.status_label = QLabel("Pronto.")
        layout.addWidget(self.status_label)

        # Pulsanti esportazione
        export_row = QHBoxLayout()
        self.btn_csv = QPushButton("💾 Esporta CSV")
        self.btn_csv.setObjectName("successBtn")
        self.btn_csv.clicked.connect(lambda: self._export("csv"))
        self.btn_txt = QPushButton("📝 Esporta TXT")
        self.btn_txt.clicked.connect(lambda: self._export("txt"))
        self.btn_copy = QPushButton("📑 Copia percorsi")
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        btn_exit = QPushButton("Esci")
        btn_exit.setObjectName("exitBtn")
        btn_exit.clicked.connect(self.close)
        for btn in (self.btn_csv, self.btn_txt, self.btn_copy):
            export_row.addWidget(btn)
        export_row.addStretch()
        export_row.addWidget(btn_exit)
        layout.addLayout(export_row)

        self.setLayout(layout)

    def add_custom_menus(self, menubar: QMenuBar) -> None:
        """Menu File (esportazioni); il menu Aiuto è aggiunto da BaseWindow."""
        file_menu = menubar.addMenu("&File")
        self.act_csv = QAction("Esporta CSV...", self)
        self.act_csv.triggered.connect(lambda: self._export("csv"))
        self.act_txt = QAction("Esporta TXT...", self)
        self.act_txt.triggered.connect(lambda: self._export("txt"))
        act_close = QAction("Chiudi", self)
        act_close.triggered.connect(self.close)
        file_menu.addActions([self.act_csv, self.act_txt])
        file_menu.addSeparator()
        file_menu.addAction(act_close)

    @staticmethod
    def _size_inputs(grid: QGridLayout, row: int, col: int,
                     default_unit: str) -> "tuple[QDoubleSpinBox, QComboBox]":
        """Crea la coppia valore/unità per un filtro di dimensione."""
        spin = QDoubleSpinBox()
        spin.setRange(0, 1_000_000)
        spin.setDecimals(2)
        spin.setSpecialValueText("Nessun limite")  # mostrato quando il valore è 0
        unit = QComboBox()
        unit.addItems(SIZE_UNITS)
        unit.setCurrentText(default_unit)
        grid.addWidget(spin, row, col)
        grid.addWidget(unit, row, col + 1)
        return spin, unit

    # ------------------------------------------------------- scansione
    def _select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleziona cartella", self.folder_edit.text())
        if folder:
            self.folder_edit.setText(folder)

    @staticmethod
    def _read_size(spin: QDoubleSpinBox, unit: QComboBox) -> Optional[int]:
        """Valore del filtro in byte, None se 0 (nessun limite)."""
        if spin.value() <= 0:
            return None
        return parse_size(f"{spin.value()} {unit.currentText()}")

    def _build_options(self) -> Optional[FileListOptions]:
        """Legge i filtri dalla UI; mostra un avviso e restituisce None se non validi."""
        folder = self.folder_edit.text().strip()
        if not os.path.isdir(folder):
            self.show_warning("La cartella indicata non esiste.")
            return None
        try:
            return FileListOptions(
                folder=folder,
                extensions=parse_extensions(self.ext_edit.text()),
                min_size=self._read_size(self.min_spin, self.min_unit),
                max_size=self._read_size(self.max_spin, self.max_unit),
                recursive=self.chk_recursive.isChecked(),
                include_hidden=self.chk_hidden.isChecked(),
            )
        except ValueError as e:
            self.show_warning(str(e))
            return None

    def _start_scan(self) -> None:
        options = self._build_options()
        if options is None:
            return
        self.entries = []
        self.total_size = 0
        self.table.setRowCount(0)
        self.status_label.setText("⏳ Scansione in corso...")

        self.scan_worker = ScanWorker(options)
        self.scan_worker.batch_found.connect(self._add_batch)
        self.scan_worker.finished_scan.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.finished.connect(self._update_buttons)
        self.scan_worker.start()
        self._update_buttons()

    def _stop_scan(self) -> None:
        if self.scan_worker is not None:
            self.scan_worker.stop()

    def _add_batch(self, batch: List[FileEntry]) -> None:
        """Aggiunge un blocco di risultati alla tabella."""
        self.table.setSortingEnabled(False)  # evita riordini a ogni inserimento
        row = self.table.rowCount()
        self.table.setRowCount(row + len(batch))
        for entry in batch:
            self.table.setItem(row, 0, QTableWidgetItem(entry.name))
            self.table.setItem(row, 1, QTableWidgetItem(entry.extension))
            size_item = SortableTableItem(format_size(entry.size), entry.size)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, size_item)
            self.table.setItem(row, 3, SortableTableItem(entry.modified_str, entry.modified))
            path_item = QTableWidgetItem(entry.relative_path)
            path_item.setToolTip(entry.path)
            self.table.setItem(row, 4, path_item)
            row += 1
        self.table.setSortingEnabled(True)

        self.entries.extend(batch)
        self.total_size += sum(e.size for e in batch)
        self.status_label.setText(f"⏳ {len(self.entries)} file trovati...")

    def _on_scan_finished(self, cancelled: bool) -> None:
        prefix = "⏹ Interrotta" if cancelled else "✅ Completata"
        self.status_label.setText(
            f"{prefix}: {len(self.entries)} file — totale {format_size(self.total_size)}")

    def _on_scan_error(self, message: str) -> None:
        self.status_label.setText("❌ Errore durante la scansione.")
        self.show_error(message)

    def _update_buttons(self) -> None:
        """Abilita/disabilita i comandi in base allo stato corrente."""
        scanning = self.scan_worker is not None and self.scan_worker.isRunning()
        exporting = self.export_worker is not None and self.export_worker.isRunning()
        can_export = bool(self.entries) and not scanning and not exporting
        self.btn_scan.setEnabled(not scanning)
        self.btn_stop.setEnabled(scanning)
        for widget in (self.btn_csv, self.btn_txt, self.btn_copy, self.act_csv, self.act_txt):
            widget.setEnabled(can_export)

    # ---------------------------------------------------- esportazione
    def _export(self, fmt: str) -> None:
        if not self.entries:
            return
        exporter, filtro = (export_csv, "CSV (*.csv)") if fmt == "csv" else (export_txt, "Testo (*.txt)")
        folder_name = os.path.basename(os.path.normpath(self.folder_edit.text())) or "lista"
        suggested = os.path.join(os.path.expanduser("~"), f"lista_file_{folder_name}.{fmt}")
        dest, _ = QFileDialog.getSaveFileName(self, "Salva elenco", suggested, filtro)
        if not dest:
            return
        if not dest.lower().endswith(f".{fmt}"):
            dest += f".{fmt}"

        self.export_worker = ExportWorker(exporter, list(self.entries), dest)
        self.export_worker.done.connect(
            lambda path: self.show_info(f"Elenco salvato in:\n{path}", "Esportazione completata"))
        self.export_worker.error.connect(
            lambda msg: self.show_error(f"Impossibile salvare il file:\n{msg}"))
        self.export_worker.finished.connect(self._update_buttons)
        self.export_worker.start()
        self._update_buttons()

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText("\n".join(e.path for e in self.entries))
        self.status_label.setText(f"📑 {len(self.entries)} percorsi copiati negli appunti.")

    def closeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        """Interrompe la scansione in corso prima di chiudere la finestra."""
        if self.scan_worker is not None and self.scan_worker.isRunning():
            self.scan_worker.stop()
            self.scan_worker.wait(2000)
        if self.export_worker is not None and self.export_worker.isRunning():
            self.export_worker.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileListerApp()
    window.show()
    sys.exit(app.exec())
