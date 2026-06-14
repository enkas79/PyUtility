"""
Image Merger Module
===================
Tool per unire più immagini in un'unica immagine (verticale o orizzontale).
"""

import sys
import os
from typing import Optional, List, Tuple

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QProgressBar, QListWidget, QRadioButton, QButtonGroup,
    QAbstractItemView, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PIL import Image


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
        """Esegue l'elaborazione e la fusione delle immagini."""
        images: List[Image.Image] = []
        try:
            images = [Image.open(p) for p in self.file_paths]
            if not images:
                raise ValueError("Nessuna immagine fornita per l'elaborazione.")

            total_images: int = len(images)

            if self.is_vertical:
                max_width: int = max(img.width for img in images)
                total_height: int = sum(img.height for img in images)
                result: Image.Image = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                y_offset: int = 0
                for i, img in enumerate(images):
                    result.paste(img, (0, y_offset))
                    y_offset += img.height
                    self.progress_signal.emit(int(((i + 1) / total_images) * 100))
            else:
                total_width: int = sum(img.width for img in images)
                max_height: int = max(img.height for img in images)
                result = Image.new('RGB', (total_width, max_height), (255, 255, 255))
                x_offset: int = 0
                for i, img in enumerate(images):
                    result.paste(img, (x_offset, 0))
                    x_offset += img.width
                    self.progress_signal.emit(int(((i + 1) / total_images) * 100))

            result.save(self.output_path, "JPEG", quality=95)
            self.finished_signal.emit(self.output_path)

        except Exception as e:
            self.error_signal.emit(f"Errore durante la fusione: {str(e)}")
        finally:
            # Assicura il rilascio delle risorse (file handlers)
            for img in images:
                img.close()


class ImageMergerApp(QWidget):
    """
    Interfaccia grafica (UI) per l'applicazione di unione delle immagini JPEG.
    
    Attributes:
        file_list (List[str]): Lista dei percorsi delle immagini selezionate.
    """

    def __init__(self) -> None:
        super().__init__()
        self.file_list: List[str] = []
        self.worker: Optional[ImageMergeWorker] = None
        self.init_ui()

    def init_ui(self) -> None:
        """Configura la geometria, lo stile e il layout principale."""
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.20)
        height = int(screen.height() * 0.40)
        min_w, min_h = 450, 550
        self.setMinimumSize(min_w, min_h)
        self.resize(max(width, min_w), max(height, min_h))
        qr = self.frameGeometry()
        qr.moveCenter(screen.center())
        self.move(qr.topLeft())

        self.setWindowTitle('Image Merger (Unione JPEG)')
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QListWidget { background-color: #1e1e1e; border: 1px solid #444; border-radius: 4px; padding: 5px; }
            QPushButton { background-color: #444; padding: 8px; border-radius: 4px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #555; }
            QPushButton#addBtn { background-color: #0078d4; }
            QPushButton#mergeBtn { background-color: #00c853; font-size: 14px; }
            QPushButton#exitBtn { background-color: #d32f2f; } 
            QPushButton#exitBtn:hover { background-color: #ff5252; }
            QPushButton#infoBtn, QPushButton#helpBtn { background-color: #333; color: #aaa; border: 1px solid #555;}
            QPushButton#infoBtn:hover, QPushButton#helpBtn:hover { color: #fff; background-color: #444; }
            QProgressBar { border: 1px solid #444; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #00c853; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Top Bar (Info e Help)
        top_bar = QHBoxLayout()
        btn_info = QPushButton("ℹ️ Info")
        btn_info.setObjectName("infoBtn")
        btn_info.clicked.connect(self.show_info)
        btn_help = QPushButton("📖 Guida")
        btn_help.setObjectName("helpBtn")
        btn_help.clicked.connect(self.show_help)
        top_bar.addWidget(btn_info)
        top_bar.addWidget(btn_help)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Sezione Immagini
        layout.addWidget(QLabel("1. Immagini da unire (Ordine di visualizzazione):"))
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Aggiungi JPEG")
        self.btn_add.setObjectName("addBtn")
        self.btn_add.clicked.connect(self.add_images)
        self.btn_clear = QPushButton("🗑️ Svuota")
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
        dir_frame.setStyleSheet("background-color: #333; border-radius: 6px; padding: 5px;")
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

    def show_info(self) -> None:
        """Mostra la finestra di informazioni sull'applicazione."""
        QMessageBox.about(
            self, "Info Applicazione",
            "<b>Image Merger</b><br>"
            "Versione: 1.2.0<br>"
            "Autore: Enrico Martini"
        )

    def show_help(self) -> None:
        """Mostra la guida all'uso dell'applicazione."""
        QMessageBox.information(
            self, "Guida",
            "<b>Come usare lo strumento:</b><ul>"
            "<li>Usa 'Aggiungi JPEG' per inserire i file.</li>"
            "<li>Trascina i file nella lista per riordinarli. L'ordine della lista sarà l'ordine finale.</li>"
            "<li>Scegli se incollare le immagini in Verticale o Orizzontale.</li>"
            "<li>Premi 'UNISCI IMMAGINI' e scegli dove salvare.</li></ul>"
        )

    def add_images(self) -> None:
        """Aggiunge nuove immagini alla lista e aggiorna la UI."""
        files: List[str] = QFileDialog.getOpenFileNames(
            self, "Seleziona Immagini JPEG", "", "Images (*.jpg *.jpeg)"
        )[0]
        if files:
            for f in files:
                if f not in self.file_list:
                    self.file_list.append(f)
                    self.list_widget.addItem(os.path.basename(f))
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

        # Ricostruisco la lista in base all'ordine visuale nel QListWidget
        ordered_files: List[str] = []
        for index in range(self.list_widget.count()):
            item_name: str = self.list_widget.item(index).text()
            # Trovo il percorso completo corrispondente al nome del file
            for f_path in self.file_list:
                if os.path.basename(f_path) == item_name:
                    ordered_files.append(f_path)
                    break

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
