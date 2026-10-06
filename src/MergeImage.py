"""
Image Merger Module
===================
Tool per unire più immagini in un'unica immagine (verticale o orizzontale).
"""

import sys
import os
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QProgressBar, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QAbstractItemView, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from base_window import BaseWindow
from image_core import merge_images


class ImageMergeWorker(QThread):
    """
    Thread dedicato alla logica di business per unire le immagini.
    Mantiene la logica separata dalla UI per evitare blocchi dell'interfaccia.
    
    Attributes:
        progress_signal (pyqtSignal): Segnale per aggiornare la barra di progresso.
        finished_signal (pyqtSignal): Segnale emesso al completamento con il percorso del file generato.
        error_signal (pyqtSignal): Segnale emesso in caso di errore.
    """
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, file_paths: List[str], output_path: str, is_vertical: bool) -> None:
        """
        Inizializza il worker per l'unione delle immagini.

        Args:
            file_paths (List[str]): Lista dei percorsi delle immagini da unire.
            output_path (str): Percorso di salvataggio del file generato.
            is_vertical (bool): True per unione verticale, False per orizzontale.
        """
        super().__init__()
        self.file_paths: List[str] = file_paths
        self.output_path: str = output_path
        self.is_vertical: bool = is_vertical

    def run(self) -> None:
        """Esegue la fusione delle immagini (logica in image_core)."""
        try:
            merge_images(self.file_paths, self.output_path, self.is_vertical,
                         on_progress=lambda done, total: self.progress_signal.emit(int(done * 100 / total)))
            self.finished_signal.emit(self.output_path)
        except Exception as e:  # noqa: BLE001 - confine del thread: nessun crash (es. DecompressionBombError)
            self.error_signal.emit(f"Errore durante la fusione: {e}")


class ImageMergerApp(BaseWindow):
    """
    Interfaccia grafica (UI) per l'applicazione di unione delle immagini JPEG.
    
    Attributes:
        file_list (List[str]): Lista dei percorsi delle immagini selezionate.
    """

    GUIDE_TEXT = (
        "<b>Come usare lo strumento:</b><ul>"
        "<li>Usa 'Aggiungi JPEG' per inserire i file.</li>"
        "<li>Trascina i file nella lista per riordinarli. L'ordine della lista sarà l'ordine finale.</li>"
        "<li>Scegli se incollare le immagini in Verticale o Orizzontale.</li>"
        "<li>Premi 'UNISCI IMMAGINI' e scegli dove salvare.</li></ul>"
    )

    def __init__(self) -> None:
        super().__init__('Image Merger (Unione JPEG)', min_width=448, min_height=552)
        self.file_list: List[str] = []
        self.worker: Optional[ImageMergeWorker] = None
        self.init_ui()

    def init_ui(self) -> None:
        """Configura la geometria, lo stile e il layout principale."""
        layout = self.create_vertical_layout(margins=(16, 8, 16, 16), spacing=12)
        layout.setMenuBar(self.create_menu_bar())

        # Sezione Immagini
        layout.addWidget(QLabel("1. Immagini da unire (Ordine di visualizzazione):"))
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Aggiungi JPEG")
        self.btn_add.setObjectName("addBtn")
        self.btn_add.clicked.connect(self.add_images)
        self.btn_clear = QPushButton("🗑️ Svuota")
        self.btn_clear.setObjectName("clearBtn")
        self.btn_clear.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        layout.addWidget(self.list_widget)

        # Direzione Unione
        dir_frame = QFrame()
        dir_layout = QHBoxLayout(dir_frame)
        dir_layout.addWidget(QLabel("Direzione:"))
        self.radio_vert = QRadioButton("Verticale (Dall'alto al basso)")
        self.radio_horiz = QRadioButton("Orizzontale (Da sx a dx)")
        self.radio_vert.setChecked(True)
        self.bg_dir = QButtonGroup(self)
        self.bg_dir.addButton(self.radio_vert)
        self.bg_dir.addButton(self.radio_horiz)
        dir_layout.addWidget(self.radio_vert)
        dir_layout.addWidget(self.radio_horiz)
        layout.addWidget(dir_frame)

        # Status e Progresso
        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)

        # Azioni Finali
        act_layout = QHBoxLayout()
        self.btn_merge = QPushButton("⚡ UNISCI IMMAGINI")
        self.btn_merge.setObjectName("mergeBtn")
        self.btn_merge.clicked.connect(self.start_merge)

        self.btn_exit = QPushButton("Esci")
        self.btn_exit.setObjectName("exitBtn")
        self.btn_exit.setFixedWidth(100)
        self.btn_exit.clicked.connect(self.close)

        act_layout.addWidget(self.btn_merge)
        act_layout.addWidget(self.btn_exit)
        layout.addLayout(act_layout)

        self.setLayout(layout)

    def add_images(self) -> None:
        """Aggiunge nuove immagini alla lista e aggiorna la UI."""
        files: List[str] = QFileDialog.getOpenFileNames(
            self, "Seleziona Immagini JPEG", "", "Images (*.jpg *.jpeg)"
        )[0]
        if files:
            for f in files:
                if f not in self.file_list:
                    self.file_list.append(f)
                    item = QListWidgetItem(os.path.basename(f))
                    item.setData(Qt.ItemDataRole.UserRole, f)
                    item.setToolTip(f)
                    self.list_widget.addItem(item)
            self.status_label.setText(f"{len(self.file_list)} immagini in lista.")

    def clear_list(self) -> None:
        """Svuota la lista delle immagini."""
        self.file_list.clear()
        self.list_widget.clear()
        self.status_label.setText("Lista vuota.")

    def start_merge(self) -> None:
        """Avvia il processo di unione richiedendo la destinazione ed eseguendo il worker."""
        if len(self.file_list) < 2:
            QMessageBox.warning(self, "Attenzione", "Devi aggiungere almeno due immagini per unirle!")
            return

        out_file: Optional[str] = QFileDialog.getSaveFileName(
            self, "Salva come", "ImmagineUnita.jpg", "JPEG (*.jpg)"
        )[0]
        if not out_file:
            return

        # Ordine visuale del QListWidget (il percorso completo è nei dati dell'item)
        ordered_files: List[str] = [
            self.list_widget.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.list_widget.count())
        ]

        self.btn_merge.setEnabled(False)
        self.btn_add.setEnabled(False)
        self.pbar.setValue(0)
        self.status_label.setText("Unione in corso...")

        self.worker = ImageMergeWorker(ordered_files, out_file, self.radio_vert.isChecked())
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_finished(self, out_path: str) -> None:
        """
        Slot eseguito al termine positivo del processo.
        
        Args:
            out_path (str): Percorso del file generato.
        """
        self.pbar.setValue(100)
        self.status_label.setText("Completato.")
        self.btn_merge.setEnabled(True)
        self.btn_add.setEnabled(True)
        QMessageBox.information(
            self, "Successo", 
            f"Immagini unite salvate con successo in:\n{out_path}"
        )

    def on_error(self, error_msg: str) -> None:
        """
        Slot eseguito in caso di eccezione lato logica.
        
        Args:
            error_msg (str): Messaggio di errore.
        """
        self.status_label.setText("Errore durante l'unione.")
        self.btn_merge.setEnabled(True)
        self.btn_add.setEnabled(True)
        QMessageBox.critical(self, "Errore", error_msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageMergerApp()
    ex.show()
    sys.exit(app.exec())
