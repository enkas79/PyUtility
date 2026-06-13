"""
BaseWindow Module
=================
Classe base per tutte le finestre della suite PyUtility.
Fornisce funzionalità comuni come centratura, stile CSS, gestione errori e logging.
"""

import os
import logging
from typing import Optional, List
from PyQt6.QtWidgets import QWidget, QMessageBox, QVBoxLayout
from PyQt6.QtCore import QApplication, Qt
from PyQt6.QtGui import QFont


# Configura il logging globale per l'applicazione
logging.basicConfig(
    filename='utility.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


class BaseWindow(QWidget):
    """
    Classe base per tutte le finestre della suite PyUtility.
    
    Fornisce metodi comuni per:
    - Centrare la finestra sullo schermo.
    - Applicare uno stile CSS predefinito.
    - Mostrare messaggi di errore/informazione standardizzati.
    - Validare percorsi file/directory.
    
    Args:
        title (str): Titolo della finestra.
        min_width (int): Larghezza minima (default: 400).
        min_height (int): Altezza minima (default: 500).
        parent (QWidget, optional): Widget genitore (default: None).
    """

    def __init__(
        self,
        title: str,
        min_width: int = 400,
        min_height: int = 500,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(min_width, min_height)
        self._center_window()
        self._apply_default_style()

    def _center_window(self) -> None:
        """Centra la finestra sullo schermo principale."""
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.20)
        height = int(screen.height() * 0.40)
        self.resize(max(width, self.minimumWidth()), max(height, self.minimumHeight()))
        
        qr = self.frameGeometry()
        cp = screen.center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _apply_default_style(self) -> None:
        """Applica lo stile CSS predefinito per la suite."""
        self.setStyleSheet("""
            QWidget { 
                background-color: #2b2b2b; 
                color: #ffffff; 
                font-family: 'Segoe UI', sans-serif; 
            }
            QLabel { 
                color: #e0e0e0; 
                font-size: 14px; 
            }
            QLabel#title { 
                font-size: 24px; 
                font-weight: bold; 
                color: #0078d4; 
                margin-bottom: 5px; 
            }
            QLabel#subtitle { 
                font-size: 11px; 
                color: #888; 
                margin-bottom: 15px; 
            }
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
            QPushButton:disabled { 
                background-color: #333; 
                color: #888; 
            }
            QPushButton#primaryBtn { 
                background-color: #0078d4; 
                border: none; 
            }
            QPushButton#primaryBtn:hover { 
                background-color: #1e90ff; 
            }
            QPushButton#successBtn { 
                background-color: #00c853; 
                border: none; 
            }
            QPushButton#successBtn:hover { 
                background-color: #4caf50; 
            }
            QPushButton#dangerBtn { 
                background-color: #d32f2f; 
                border: none; 
            }
            QPushButton#dangerBtn:hover { 
                background-color: #ff5252; 
            }
            QPushButton#infoBtn, QPushButton#helpBtn { 
                background-color: #333; 
                color: #aaa; 
                border: 1px solid #555; 
            }
            QPushButton#infoBtn:hover, QPushButton#helpBtn:hover { 
                color: #fff; 
                background-color: #444; 
            }
            QLineEdit, QComboBox, QSpinBox { 
                padding: 6px; 
                background-color: #404040; 
                border: 1px solid #555; 
                border-radius: 4px; 
                color: white; 
            }
            QProgressBar { 
                border: 1px solid #444; 
                border-radius: 5px; 
                text-align: center; 
                background-color: #333; 
            }
            QProgressBar::chunk { 
                background-color: #00c853; 
                border-radius: 4px; 
            }
            QListWidget { 
                background-color: #1e1e1e; 
                border: 1px solid #444; 
                border-radius: 4px; 
                padding: 5px; 
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
            QFrame { 
                background-color: #333; 
                border-radius: 6px; 
            }
            QMessageBox { 
                background-color: #1e1e1e; 
            }
            QMessageBox QLabel { 
                color: white; 
                font-size: 13px; 
            }
            QMessageBox QPushButton { 
                background-color: #0078d4; 
                color: white; 
                padding: 5px 20px; 
            }
        """)

    def show_error(self, message: str, title: str = "Errore") -> None:
        """
        Mostra un messaggio di errore standardizzato.
        
        Args:
            message (str): Messaggio di errore da mostrare.
            title (str): Titolo della finestra di errore (default: "Errore").
        """
        logger.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)

    def show_info(self, message: str, title: str = "Informazione") -> None:
        """
        Mostra un messaggio informativo standardizzato.
        
        Args:
            message (str): Messaggio da mostrare.
            title (str): Titolo della finestra (default: "Informazione").
        """
        logger.info(f"{title}: {message}")
        QMessageBox.information(self, title, message)

    def show_warning(self, message: str, title: str = "Attenzione") -> None:
        """
        Mostra un messaggio di avviso standardizzato.
        
        Args:
            message (str): Messaggio di avviso da mostrare.
            title (str): Titolo della finestra (default: "Attenzione").
        """
        logger.warning(f"{title}: {message}")
        QMessageBox.warning(self, title, message)

    @staticmethod
    def is_safe_path(path: str, base_dir: Optional[str] = None) -> bool:
        """
        Verifica che il percorso sia sicuro (esiste e non esce dalla directory base).
        
        Args:
            path (str): Percorso da validare.
            base_dir (str, optional): Directory base di riferimento (default: None).
        
        Returns:
            bool: True se il percorso è sicuro, False altrimenti.
        """
        if not path or not os.path.exists(path):
            return False
        
        if base_dir:
            from pathlib import Path
            base_path = Path(base_dir).resolve()
            target_path = Path(path).resolve()
            return base_path in target_path.parents or target_path == base_path
        
        return True

    @staticmethod
    def get_absolute_path(path: str) -> Optional[str]:
        """
        Converte un percorso in un percorso assoluto valido.
        
        Args:
            path (str): Percorso da convertire.
        
        Returns:
            Optional[str]: Percorso assoluto se valido, None altrimenti.
        """
        if not path:
            return None
        
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
        return None

    def create_vertical_layout(self, margins: tuple = (20, 20, 20, 20), spacing: int = 12) -> QVBoxLayout:
        """
        Crea un layout verticale con margini e spaziatura predefiniti.
        
        Args:
            margins (tuple): Margini (left, top, right, bottom) in pixel (default: (20, 20, 20, 20)).
            spacing (int): Spaziatura tra i widget in pixel (default: 12).
        
        Returns:
            QVBoxLayout: Layout verticale configurato.
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout
