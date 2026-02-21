import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QProgressBar, QListWidget, QComboBox, QFrame,
                             QSpinBox, QDialog)  # Aggiunto QDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PIL import Image


# --- FINESTRA REPORT PERSONALIZZATA ---
class ReportDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 220)  # Dimensioni minime per non essere schiacciata

        # Stile Dialogo
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: white; border: 1px solid #555; }
            QLabel { font-size: 16px; color: #e0e0e0; }
            QLabel#titleMsg { font-size: 22px; font-weight: bold; color: #00c853; margin-bottom: 10px; }
            QPushButton { 
                background-color: #0078d4; color: white; 
                padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #1e90ff; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Titolo (Successo!)
        lbl_title = QLabel("✅ Operazione Completata")
        lbl_title.setObjectName("titleMsg")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Messaggio dettagliato
        lbl_msg = QLabel(message)
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setWordWrap(True)  # Manda a capo se troppo lungo
        layout.addWidget(lbl_msg)

        # Bottone OK
        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)

        # Centrare il bottone
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)


# --- WORKER PER LA CONVERSIONE ---
class ConversionWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, file_list, output_folder, target_format, resize_mode, resize_value):
        super().__init__()
        self.file_list = file_list
        self.output_folder = output_folder
        self.target_format = target_format.upper()
        self.resize_mode = resize_mode
        self.resize_value = resize_value

    def run(self):
        total = len(self.file_list)
        errors = 0

        ext_map = {
            'JPG': 'JPEG', 'JPEG': 'JPEG', 'PNG': 'PNG',
            'WEBP': 'WEBP', 'BMP': 'BMP', 'ICO': 'ICO', 'TIFF': 'TIFF'
        }
        pil_format = ext_map.get(self.target_format, 'PNG')

        for i, file_path in enumerate(self.file_list):
            filename = os.path.basename(file_path)
            self.status_signal.emit(f"Elaborazione: {filename}")

            try:
                with Image.open(file_path) as img:
                    if img.mode == 'P': img = img.convert('RGBA')

                    # Ridimensionamento
                    if self.resize_mode > 0:
                        w, h = img.size
                        new_w, new_h = w, h

                        if self.resize_mode == 1:  # %
                            factor = self.resize_value / 100.0
                            new_w = int(w * factor)
                            new_h = int(h * factor)
                        elif self.resize_mode == 2:  # Width
                            ratio = self.resize_value / float(w)
                            new_w = self.resize_value
                            new_h = int(h * ratio)
                        elif self.resize_mode == 3:  # Height
                            ratio = self.resize_value / float(h)
                            new_h = self.resize_value
                            new_w = int(w * ratio)

                        if new_w > 0 and new_h > 0:
                            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # Salvataggio
                    if pil_format in ['JPEG', 'BMP']:
                        if img.mode in ('RGBA', 'LA'):
                            bg = Image.new('RGB', img.size, (255, 255, 255))
                            bg.paste(img, mask=img.split()[-1])
                            img = bg
                        else:
                            img = img.convert('RGB')
                    else:
                        if img.mode not in ('RGB', 'RGBA', 'L'):
                            img = img.convert('RGBA')

                    name_without_ext = os.path.splitext(filename)[0]
                    new_filename = f"{name_without_ext}.{self.target_format.lower()}"
                    save_path = os.path.join(self.output_folder, new_filename)

                    if pil_format in ['JPEG', 'WEBP']:
                        img.save(save_path, pil_format, quality=90)
                    else:
                        img.save(save_path, pil_format)

            except Exception as e:
                print(f"Errore: {e}")
                errors += 1

            percent = int(((i + 1) / total) * 100)
            self.progress_signal.emit(percent)

        msg = f"Totale file elaborati: {total}\nSuccessi: {total - errors}\nErrori riscontrati: {errors}"
        self.finished_signal.emit(msg)


# --- INTERFACCIA ---
class ImageResizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.file_list = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Converter & Resizer')
        self.resize(650, 600)

        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QListWidget { background-color: #1e1e1e; border: 1px solid #444; border-radius: 4px; padding: 5px; }
            QComboBox, QSpinBox { padding: 6px; background-color: #404040; border: 1px solid #555; border-radius: 4px; color: white; }

            QPushButton { background-color: #444; padding: 8px; border-radius: 4px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #555; }

            QPushButton#addBtn { background-color: #0078d4; }
            QPushButton#convertBtn { background-color: #00c853; font-size: 14px; }
            QPushButton#exitBtn { background-color: #d32f2f; } 
            QPushButton#exitBtn:hover { background-color: #ff5252; }

            QFrame { background-color: #333; border-radius: 6px; }
            QLabel#sectionTitle { font-weight: bold; color: #ccc; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Input
        layout.addWidget(QLabel("1. Immagini:", objectName="sectionTitle"))
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Aggiungi")
        self.btn_add.setObjectName("addBtn")
        self.btn_add.clicked.connect(self.add_images)
        self.btn_clear = QPushButton("🗑️ Svuota")
        self.btn_clear.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget)

        # 2. Impostazioni
        settings_frame = QFrame()
        s_layout = QVBoxLayout(settings_frame)
        s_layout.setSpacing(10)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Formato Output:"))
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["JPG", "PNG", "WEBP", "BMP", "ICO", "TIFF"])
        fmt_row.addWidget(self.combo_fmt, 1)
        s_layout.addLayout(fmt_row)

        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Ridimensiona:"))
        self.combo_resize = QComboBox()
        self.combo_resize.addItems(
            ["Mantieni Originale", "Percentuale %", "Larghezza Fissa (px)", "Altezza Fissa (px)"])
        self.combo_resize.currentIndexChanged.connect(self.toggle_spinbox)

        self.spin_val = QSpinBox()
        self.spin_val.setRange(1, 10000)
        self.spin_val.setValue(100)
        self.spin_val.setEnabled(False)
        self.spin_val.setSuffix(" %")

        res_row.addWidget(self.combo_resize, 1)
        res_row.addWidget(self.spin_val, 1)
        s_layout.addLayout(res_row)
        layout.addWidget(settings_frame)

        # 3. Status
        self.status_label = QLabel("Pronto.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)

        # 4. Azioni
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

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if files:
            for f in files:
                if f not in self.file_list:
                    self.file_list.append(f)
                    self.list_widget.addItem(os.path.basename(f))
            self.status_label.setText(f"{len(self.file_list)} immagini in lista.")

    def clear_list(self):
        self.file_list = []
        self.list_widget.clear()
        self.status_label.setText("Lista vuota.")

    def toggle_spinbox(self, index):
        if index == 0:
            self.spin_val.setEnabled(False)
            self.spin_val.setSuffix("")
        else:
            self.spin_val.setEnabled(True)
            if index == 1:
                self.spin_val.setSuffix(" %")
                self.spin_val.setValue(50)
            else:
                self.spin_val.setSuffix(" px")
                self.spin_val.setValue(1080)

    def start_conversion(self):
        if not self.file_list:
            # Anche qui usiamo il nuovo ReportDialog per coerenza, se vuoi
            ReportDialog("Attenzione", "Devi aggiungere almeno un'immagine prima di convertire!", self).exec()
            return

        out_dir = QFileDialog.getExistingDirectory(self, "Dove salvare?")
        if not out_dir: return

        self.pbar.setValue(0)
        self.btn_convert.setEnabled(False)
        self.btn_add.setEnabled(False)

        fmt = self.combo_fmt.currentText()
        res_mode = self.combo_resize.currentIndex()
        res_val = self.spin_val.value()

        self.worker = ConversionWorker(self.file_list, out_dir, fmt, res_mode, res_val)
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, msg):
        self.pbar.setValue(100)
        self.status_label.setText("Completato.")
        self.btn_convert.setEnabled(True)
        self.btn_add.setEnabled(True)

        # --- QUI CHIAMIAMO LA NOSTRA FINESTRA PERSONALIZZATA ---
        report = ReportDialog("Riepilogo Conversione", msg, self)
        report.exec()  # Blocca l'interfaccia finché non chiudi il report


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageResizerApp()
    ex.show()
    sys.exit(app.exec())