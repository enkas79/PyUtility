"""
Image Watermark Module
======================
Tool per aggiungere watermark (testo o immagine) alle immagini.
"""

import os
import logging
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QMessageBox, QLineEdit, QComboBox, QSpinBox, 
    QProgressBar, QListWidget, QAbstractItemView, QFrame, QColorDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont
from PIL import Image, ImageDraw, ImageFont
from base_window import BaseWindow
from styles import get_style

logger = logging.getLogger(__name__)


class WatermarkWorker(QThread):
    """
    Thread per applicare il watermark alle immagini in background.
    
    Attributes:
        progress_signal (pyqtSignal): Segnale per aggiornare la barra di progresso.
        finished_signal (pyqtSignal): Segnale emesso al completamento.
        error_signal (pyqtSignal): Segnale emesso in caso di errore.
    """
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        file_list: List[str],
        output_folder: str,
        watermark_type: str,
        watermark_text: str = "",
        watermark_image: str = "",
        position: str = "center",
        opacity: int = 50,
        font_size: int = 36,
        font_color: Tuple[int, int, int] = (255, 255, 255),
        rotation: int = 0
    ) -> None:
        """
        Inizializza il worker per l'applicazione del watermark.
        
        Args:
            file_list (List[str]): Lista dei percorsi delle immagini.
            output_folder (str): Cartella di output.
            watermark_type (str): Tipo di watermark ("text" o "image").
            watermark_text (str): Testo del watermark (se watermark_type == "text").
            watermark_image (str): Percorso dell'immagine watermark (se watermark_type == "image").
            position (str): Posizione del watermark ("center", "top_left", "top_right", etc.).
            opacity (int): Opacità del watermark (0-100).
            font_size (int): Dimensione del font (per watermark di testo).
            font_color (Tuple[int, int, int]): Colore del font (RGB).
            rotation (int): Rotazione del watermark in gradi.
        """
        super().__init__()
        self.file_list = file_list
        self.output_folder = output_folder
        self.watermark_type = watermark_type
        self.watermark_text = watermark_text
        self.watermark_image = watermark_image
        self.position = position
        self.opacity = opacity
        self.font_size = font_size
        self.font_color = font_color
        self.rotation = rotation

    def run(self) -> None:
        """Applica il watermark a tutte le immagini."""
        try:
            total = len(self.file_list)
            errors = 0
            
            for i, file_path in enumerate(self.file_list):
                try:
                    with Image.open(file_path) as img:
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        elif img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        
                        watermarked = self._apply_watermark(img)
                        
                        # Salva l'immagine con watermark
                        output_path = os.path.join(
                            self.output_folder,
                            f"watermarked_{os.path.basename(file_path)}"
                        )
                        watermarked.save(output_path, "PNG")
                        
                except Exception as e:
                    logger.error(f"Errore elaborazione {file_path}: {str(e)}", exc_info=True)
                    errors += 1
                
                self.progress_signal.emit(int(((i + 1) / total) * 100))
            
            self.finished_signal.emit(
                f"Watermark applicato a {total - errors}/{total} immagini."
            )
            
        except Exception as e:
            logger.error(f"Errore durante l'applicazione del watermark: {str(e)}", exc_info=True)
            self.error_signal.emit(f"Errore: {str(e)}")

    def _apply_watermark(self, img: Image.Image) -> Image.Image:
        """
        Applica il watermark a un'immagine.
        
        Args:
            img (Image.Image): Immagine di origine.
        
        Returns:
            Image.Image: Immagine con watermark applicato.
        """
        watermarked = img.copy()
        draw = ImageDraw.Draw(watermarked)
        width, height = img.size
        
        if self.watermark_type == "text":
            # Applica watermark di testo
            try:
                font = ImageFont.truetype("arial.ttf", self.font_size)
            except:
                font = ImageFont.load_default()
            
            # Calcola la posizione del testo
            text_width, text_height = draw.textsize(self.watermark_text, font=font)
            x, y = self._get_position(width, height, text_width, text_height)
            
            # Applica il testo con opacità
            alpha = int(255 * (self.opacity / 100))
            color = (*self.font_color, alpha)
            draw.text((x, y), self.watermark_text, font=font, fill=color)
            
        elif self.watermark_type == "image" and self.watermark_image:
            # Applica watermark immagine
            with Image.open(self.watermark_image) as wm_img:
                if wm_img.mode != 'RGBA':
                    wm_img = wm_img.convert('RGBA')
                
                # Ridimensiona il watermark in base all'immagine originale
                wm_width, wm_height = wm_img.size
                max_wm_size = min(width, height) // 3
                scale = min(max_wm_size / wm_width, max_wm_size / wm_height)
                new_wm_size = (int(wm_width * scale), int(wm_height * scale))
                wm_img = wm_img.resize(new_wm_size, Image.Resampling.LANCZOS)
                
                # Applica opacità
                alpha = int(255 * (self.opacity / 100))
                wm_img.putalpha(wm_img.split()[3].point(lambda p: min(p, alpha)))
                
                # Calcola la posizione
                x, y = self._get_position(width, height, new_wm_size[0], new_wm_size[1])
                
                # Incolla il watermark
                watermarked.paste(wm_img, (x, y), wm_img)
        
        return watermarked

    def _get_position(
        self, img_width: int, img_height: int, wm_width: int, wm_height: int
    ) -> Tuple[int, int]:
        """
        Calcola la posizione (x, y) del watermark in base alla posizione selezionata.
        
        Args:
            img_width (int): Larghezza dell'immagine.
            img_height (int): Altezza dell'immagine.
            wm_width (int): Larghezza del watermark.
            wm_height (int): Altezza del watermark.
        
        Returns:
            Tuple[int, int]: Coordinate (x, y) per il watermark.
        """
        positions = {
            "center": (img_width // 2 - wm_width // 2, img_height // 2 - wm_height // 2),
            "top_left": (10, 10),
            "top_right": (img_width - wm_width - 10, 10),
            "bottom_left": (10, img_height - wm_height - 10),
            "bottom_right": (img_width - wm_width - 10, img_height - wm_height - 10),
            "top_center": (img_width // 2 - wm_width // 2, 10),
            "bottom_center": (img_width // 2 - wm_width // 2, img_height - wm_height - 10),
            "left_center": (10, img_height // 2 - wm_height // 2),
            "right_center": (img_width - wm_width - 10, img_height // 2 - wm_height // 2),
        }
        return positions.get(self.position, (img_width // 2 - wm_width // 2, img_height // 2 - wm_height // 2))


class WatermarkApp(BaseWindow):
    """
    Applicazione per aggiungere watermark alle immagini.
    
    Attributes:
        file_list (List[str]): Lista dei percorsi delle immagini selezionate.
        watermark_image (str): Percorso dell'immagine watermark (opzionale).
        output_folder (str): Cartella di output selezionata.
    """

    def __init__(self) -> None:
        """Inizializza l'applicazione Watermark."""
        super().__init__("Image Watermark", min_width=600, min_height=650)
        self.file_list: List[str] = []
        self.watermark_image: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.worker: Optional[WatermarkWorker] = None
        self.font_color: QColor = QColor(255, 255, 255)
        self._init_ui()

    def _init_ui(self) -> None:
        """Inizializza l'interfaccia utente."""
        layout = self.create_vertical_layout(margins=(20, 20, 20, 20), spacing=15)
        
        # Titolo
        title_label = QLabel("🎨 Image Watermark")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Aggiungi watermark (testo o immagine) alle tue foto")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Sezione immagini
        layout.addWidget(QLabel("1. Immagini da elaborare:"))
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Aggiungi Immagini")
        btn_add.setObjectName("primaryBtn")
        btn_add.clicked.connect(self._add_images)
        self.btn_clear = QPushButton("🗑️ Svuota")
        self.btn_clear.setObjectName("dangerBtn")
        self.btn_clear.clicked.connect(self._clear_list)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget)
        
        # Sezione tipo watermark
        layout.addWidget(QLabel("2. Tipo di Watermark:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Testo", "Immagine"])
        self.combo_type.currentIndexChanged.connect(self._update_watermark_ui)
        layout.addWidget(self.combo_type)
        
        # Sezione parametri watermark (testo)
        self.text_frame = QFrame()
        text_layout = QVBoxLayout(self.text_frame)
        text_layout.setContentsMargins(10, 10, 10, 10)
        text_layout.setSpacing(10)
        
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Inserisci il testo del watermark...")
        text_layout.addWidget(self.text_edit)
        
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Dimensione font:"))
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 200)
        self.spin_font_size.setValue(36)
        font_layout.addWidget(self.spin_font_size)
        text_layout.addLayout(font_layout)
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Colore:"))
        self.btn_color = QPushButton("Seleziona Colore")
        self.btn_color.setObjectName("infoBtn")
        self.btn_color.clicked.connect(self._select_color)
        self.color_label = QLabel()
        self.color_label.setStyleSheet("background-color: white; width: 30px; height: 20px; border: 1px solid #555;")
        color_layout.addWidget(self.btn_color)
        color_layout.addWidget(self.color_label)
        text_layout.addLayout(color_layout)
        
        layout.addWidget(self.text_frame)
        
        # Sezione parametri watermark (immagine)
        self.image_frame = QFrame()
        image_layout = QVBoxLayout(self.image_frame)
        image_layout.setContentsMargins(10, 10, 10, 10)
        image_layout.setSpacing(10)
        
        image_layout.addWidget(QLabel("Seleziona immagine watermark:"))
        self.wm_image_label = QLabel("Nessuna immagine selezionata")
        self.wm_image_label.setStyleSheet("color: #aaa;")
        btn_wm_image = QPushButton("📂 Seleziona Immagine Watermark")
        btn_wm_image.setObjectName("primaryBtn")
        btn_wm_image.clicked.connect(self._select_watermark_image)
        image_layout.addWidget(self.wm_image_label)
        image_layout.addWidget(btn_wm_image)
        
        layout.addWidget(self.image_frame)
        self.image_frame.hide()  # Nasconde inizialmente
        
        # Sezione posizione e opacità
        layout.addWidget(QLabel("3. Posizione e Opacità:"))
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Posizione:"))
        self.combo_position = QComboBox()
        self.combo_position.addItems([
            "Centro", "In alto a sinistra", "In alto a destra", 
            "In basso a sinistra", "In basso a destra", 
            "In alto al centro", "In basso al centro", 
            "Al centro a sinistra", "Al centro a destra"
        ])
        pos_layout.addWidget(self.combo_position, 1)
        layout.addLayout(pos_layout)
        
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacità (%):"))
        self.spin_opacity = QSpinBox()
        self.spin_opacity.setRange(1, 100)
        self.spin_opacity.setValue(50)
        opacity_layout.addWidget(self.spin_opacity)
        layout.addLayout(opacity_layout)
        
        # Sezione output
        layout.addWidget(QLabel("4. Cartella di output:"))
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Nessuna cartella selezionata")
        self.output_label.setStyleSheet("color: #aaa;")
        btn_output = QPushButton("📂 Seleziona Cartella")
        btn_output.setObjectName("primaryBtn")
        btn_output.clicked.connect(self._select_output_folder)
        output_layout.addWidget(self.output_label, 1)
        output_layout.addWidget(btn_output)
        layout.addLayout(output_layout)
        
        # Barra di progresso e stato
        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        
        # Pulsanti azione
        action_layout = QHBoxLayout()
        self.btn_apply = QPushButton("✨ APPLICA WATERMARK")
        self.btn_apply.setObjectName("successBtn")
        self.btn_apply.clicked.connect(self._start_watermark)
        self.btn_apply.setEnabled(False)
        
        btn_exit = QPushButton("Esci")
        btn_exit.setObjectName("dangerBtn")
        btn_exit.clicked.connect(self.close)
        
        action_layout.addWidget(self.btn_apply)
        action_layout.addWidget(btn_exit)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)

    def _update_watermark_ui(self, index: int) -> None:
        """
        Aggiorna l'interfaccia in base al tipo di watermark selezionato.
        
        Args:
            index (int): Indice del tipo di watermark (0 = Testo, 1 = Immagine).
        """
        if index == 0:  # Testo
            self.text_frame.show()
            self.image_frame.hide()
        else:  # Immagine
            self.text_frame.hide()
            self.image_frame.show()

    def _select_color(self) -> None:
        """Apre il dialog per selezionare il colore del testo."""
        color = QColorDialog.getColor(
            self.font_color, self, "Seleziona Colore"
        )
        if color.isValid():
            self.font_color = color
            self.color_label.setStyleSheet(
                f"background-color: {color.name()}; width: 30px; height: 20px; border: 1px solid #555;"
            )

    def _add_images(self) -> None:
        """Aggiunge immagini alla lista."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleziona Immagini", "", 
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            for f in files:
                if f not in self.file_list:
                    self.file_list.append(f)
                    self.list_widget.addItem(os.path.basename(f))
            self.status_label.setText(f"{len(self.file_list)} immagini in lista.")
            self._check_ready()

    def _clear_list(self) -> None:
        """Svuota la lista delle immagini."""
        self.file_list.clear()
        self.list_widget.clear()
        self.status_label.setText("Lista vuota.")
        self._check_ready()

    def _select_watermark_image(self) -> None:
        """Seleziona l'immagine per il watermark."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Immagine Watermark", "", 
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self.watermark_image = path
            self.wm_image_label.setText(os.path.basename(path))
            self.wm_image_label.setStyleSheet("color: #00c853;")

    def _select_output_folder(self) -> None:
        """Seleziona la cartella di output."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleziona Cartella di Output"
        )
        if folder:
            self.output_folder = folder
            self.output_label.setText(folder)
            self.output_label.setStyleSheet("color: #00c853;")
            self._check_ready()

    def _check_ready(self) -> None:
        """Verifica se tutti i parametri sono pronti per applicare il watermark."""
        if (len(self.file_list) > 0 and self.output_folder and 
            (self.combo_type.currentIndex() == 0 or self.watermark_image)):
            self.btn_apply.setEnabled(True)
        else:
            self.btn_apply.setEnabled(False)

    def _start_watermark(self) -> None:
        """Avvia il processo di applicazione del watermark."""
        if len(self.file_list) == 0:
            self.show_error("Aggiungi almeno un'immagine.")
            return
        if not self.output_folder:
            self.show_error("Seleziona una cartella di output.")
            return
        if self.combo_type.currentIndex() == 1 and not self.watermark_image:
            self.show_error("Seleziona un'immagine per il watermark.")
            return
        
        # Mappa le posizioni
        position_map = {
            "Centro": "center",
            "In alto a sinistra": "top_left",
            "In alto a destra": "top_right",
            "In basso a sinistra": "bottom_left",
            "In basso a destra": "bottom_right",
            "In alto al centro": "top_center",
            "In basso al centro": "bottom_center",
            "Al centro a sinistra": "left_center",
            "Al centro a destra": "right_center"
        }
        
        self.btn_apply.setEnabled(False)
        self.pbar.setValue(0)
        self.status_label.setText("Applicazione watermark in corso...")
        
        self.worker = WatermarkWorker(
            file_list=self.file_list,
            output_folder=self.output_folder,
            watermark_type="text" if self.combo_type.currentIndex() == 0 else "image",
            watermark_text=self.text_edit.text(),
            watermark_image=self.watermark_image,
            position=position_map.get(self.combo_position.currentText(), "center"),
            opacity=self.spin_opacity.value(),
            font_size=self.spin_font_size.value(),
            font_color=(self.font_color.red(), self.font_color.green(), self.font_color.blue()),
            rotation=0
        )
        
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.error_signal.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, message: str) -> None:
        """Gestisce il completamento dell'applicazione del watermark."""
        self.pbar.setValue(100)
        self.status_label.setText("Completato.")
        self.btn_apply.setEnabled(True)
        self.show_info(message, "Successo")

    def _on_error(self, error: str) -> None:
        """Gestisce gli errori durante l'applicazione del watermark."""
        self.status_label.setText("Errore.")
        self.btn_apply.setEnabled(True)
        self.show_error(error)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = WatermarkApp()
    window.show()
    sys.exit(app.exec())
