"""
Image Converter & Resizer Module
==================================
Tool per convertire e ridimensionare immagini in batch.
Supporta formati: JPG, PNG, WEBP, BMP, ICO, TIFF.
"""

import logging
import os
import sys
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QListWidget, QComboBox, QFrame,
    QSpinBox, QDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from base_window import BaseWindow
from image_core import convert_image

logger = logging.getLogger(__name__)


class ReportDialog(QDialog):
    """
    Finestra di dialogo per mostrare un report al completamento di un'operazione.
    
    Args:
        title (str): Titolo della finestra.
        message (str): Messaggio da mostrare.
        parent (QWidget, optional): Widget genitore. Defaults to None.
    """
    def __init__(self, title: str, message: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 220)
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        lbl_title = QLabel("✅ Operazione Completata")
        lbl_title.setObjectName("successTitle")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        lbl_msg = QLabel(message)
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg)
        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.setLayout(layout)


class ConversionWorker(QThread):
    """
    Thread per eseguire la conversione e il ridimensionamento delle immagini in background.
    
    Attributes:
        progress_signal (pyqtSignal): Segnale per aggiornare la barra di progresso (0-100).
        status_signal (pyqtSignal): Segnale per aggiornare lo stato (testo).
        finished_signal (pyqtSignal): Segnale emesso al completamento con il report.
    """
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(
        self,
        file_list: List[str],
        output_folder: str,
        target_format: str,
        resize_mode: int,
        resize_value: int
    ) -> None:
        """
        Inizializza il worker per la conversione delle immagini.
        
        Args:
            file_list (List[str]): Lista dei percorsi delle immagini da elaborare.
            output_folder (str): Cartella di output per i file convertiti.
            target_format (str): Formato di output (es. "JPG", "PNG").
            resize_mode (int): Modalità di ridimensionamento:
                (costanti RESIZE_* di image_core)
                - 0: Mantieni originale
                - 1: Percentuale (%)
                - 2: Larghezza fissa (px)
                - 3: Altezza fissa (px)
            resize_value (int): Valore per il ridimensionamento (dipende da resize_mode).
        """
        super().__init__()
        self.file_list = file_list
        self.output_folder = output_folder
        self.target_format = target_format.upper()
        self.resize_mode = resize_mode
        self.resize_value = resize_value

    def run(self) -> None:
        """Esegue la conversione e il ridimensionamento delle immagini (logica in image_core)."""
        total: int = len(self.file_list)
        errors: int = 0
        for i, file_path in enumerate(self.file_list):
            filename: str = os.path.basename(file_path)
            self.status_signal.emit(f"Elaborazione: {filename}")
            try:
                convert_image(file_path, self.output_folder, self.target_format,
                              self.resize_mode, self.resize_value)
            except Exception as e:  # noqa: BLE001 - confine del thread: nessun crash (es. DecompressionBombError)
                errors += 1
                logger.warning("Conversione fallita per %s: %s", file_path, e)
                self.status_signal.emit(f"Errore in {filename}: {e}")
            self.progress_signal.emit(int(((i + 1) / total) * 100))

        self.finished_signal.emit(
            f"Totale file elaborati: {total}\nSuccessi: {total - errors}\nErrori riscontrati: {errors}\n\n"
            "I file omonimi esistenti non vengono sovrascritti (suffisso ' (1)', ' (2)', ...)."
        )


class ImageResizerApp(BaseWindow):
    """
    Applicazione principale per la conversione e il ridimensionamento delle immagini.
    
    Attributes:
        file_list (List[str]): Lista dei percorsi delle immagini selezionate.
    """

    GUIDE_TEXT = (
        "1. Premi 'Aggiungi' per inserire le immagini (JPG, PNG, WEBP, BMP).\n"
        "2. Scegli il formato di output (JPG, PNG, WEBP, BMP, ICO, TIFF).\n"
        "3. (Opzionale) Scegli il ridimensionamento: percentuale, larghezza o altezza fissa; "
        "le proporzioni vengono sempre mantenute.\n"
        "4. Premi 'AVVIA PROCESSO' e scegli la cartella di destinazione.\n\n"
        "Le immagini originali non vengono modificate."
    )

    def __init__(self) -> None:
        """Inizializza l'applicazione ImageResizer."""
        super().__init__('Image Converter & Resizer', min_width=400, min_height=500)
        self.file_list: List[str] = []
        self.initUI()

    def initUI(self) -> None:
        """Inizializza l'interfaccia utente."""
        layout = self.create_vertical_layout(margins=(16, 8, 16, 16), spacing=12)
        layout.setMenuBar(self.create_menu_bar())
        layout.addWidget(QLabel("1. Immagini:", objectName="sectionTitle"))
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Aggiungi")
        self.btn_add.setObjectName("addBtn")
        self.btn_add.clicked.connect(self.add_images)
        self.btn_clear = QPushButton("🗑️ Svuota")
        self.btn_clear.setObjectName("clearBtn")
        self.btn_clear.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        settings_frame = QFrame()
        s_layout = QVBoxLayout(settings_frame)
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Formato Output:"))
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["JPG", "PNG", "WEBP", "BMP", "ICO", "TIFF"])
        fmt_row.addWidget(self.combo_fmt, 1)
        s_layout.addLayout(fmt_row)
        
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Ridimensiona:"))
        self.combo_resize = QComboBox()
        self.combo_resize.addItems([
            "Mantieni Originale", 
            "Percentuale %", 
            "Larghezza Fissa (px)", 
            "Altezza Fissa (px)"
        ])
        self.combo_resize.currentIndexChanged.connect(self.toggle_spinbox)
        self.spin_val = QSpinBox()
        self.spin_val.setRange(1, 10000)
        self.spin_val.setValue(100)
        self.spin_val.setEnabled(False)
        res_row.addWidget(self.combo_resize, 1)
        res_row.addWidget(self.spin_val, 1)
        s_layout.addLayout(res_row)
        layout.addWidget(settings_frame)
        
        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        
        act_layout = QHBoxLayout()
        self.btn_convert = QPushButton("⚡ AVVIA PROCESSO")
        self.btn_convert.setObjectName("convertBtn")
        self.btn_convert.clicked.connect(self.start_conversion)
        self.btn_exit = QPushButton("Esci")
        self.btn_exit.setObjectName("exitBtn")
        self.btn_exit.setFixedWidth(100)
        self.btn_exit.clicked.connect(self.close)
        act_layout.addWidget(self.btn_convert)
        act_layout.addWidget(self.btn_exit)
        layout.addLayout(act_layout)
        
        self.setLayout(layout)

    def add_images(self) -> None:
        """Aggiunge immagini alla lista dalla dialog di selezione file."""
        files: List[str] = QFileDialog.getOpenFileNames(
            self, "Seleziona", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )[0]
        if files:
            for f in files:
                if f not in self.file_list:
                    self.file_list.append(f)
                    self.list_widget.addItem(os.path.basename(f))
            self.status_label.setText(f"{len(self.file_list)} immagini in lista.")

    def clear_list(self) -> None:
        """Svuota la lista delle immagini."""
        self.file_list: List[str] = []
        self.list_widget.clear()
        self.status_label.setText("Lista vuota.")

    def toggle_spinbox(self, index: int) -> None:
        """
        Abilita/disabilita il QSpinBox in base alla modalità di ridimensionamento selezionata.
        
        Args:
            index (int): Indice della modalità selezionata.
        """
        self.spin_val.setEnabled(index != 0)
        if index == 1:
            self.spin_val.setSuffix(" %")
            self.spin_val.setValue(50)
        elif index > 1:
            self.spin_val.setSuffix(" px")
            self.spin_val.setValue(1080)
        else:
            self.spin_val.setSuffix("")

    def start_conversion(self) -> None:
        """Avvia il processo di conversione dopo aver selezionato la cartella di output."""
        if not self.file_list:
            self.show_warning("Devi aggiungere almeno un'immagine prima di convertire!")
            return
        
        out_dir: Optional[str] = QFileDialog.getExistingDirectory(self, "Dove salvare?")
        if not out_dir:
            return
        
        self.btn_convert.setEnabled(False)
        self.btn_add.setEnabled(False)
        
        self.worker = ConversionWorker(
            self.file_list,
            out_dir,
            self.combo_fmt.currentText(),
            self.combo_resize.currentIndex(),
            self.spin_val.value()
        )
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, msg: str) -> None:
        """
        Slot eseguito al completamento della conversione.
        
        Args:
            msg (str): Messaggio di riepilogo.
        """
        self.pbar.setValue(100)
        self.status_label.setText("Completato.")
        self.btn_convert.setEnabled(True)
        self.btn_add.setEnabled(True)
        ReportDialog("Riepilogo Conversione", msg, self).exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageResizerApp()
    ex.show()
    sys.exit(app.exec())
