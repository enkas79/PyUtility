"""
BaseWindow Module
=================
Classe base per tutte le finestre della suite PyUtility.
Fornisce funzionalità comuni come centratura, stile CSS, gestione errori e logging.
"""

import logging
import os
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QLabel, QMenuBar, QMessageBox, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app_info import APP_NAME, AUTHOR, get_app_version, resource_path, user_data_dir
from styles import get_style

__all__ = ["BaseWindow", "SortableTableItem", "add_help_menu", "get_app_version",
           "logger", "resource_path", "show_about"]


def _configure_logging() -> None:
    """
    Log su file nella cartella dati dell'utente: la cartella corrente o quella
    di installazione possono essere in sola lettura (prima: crash all'avvio).
    """
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    try:
        log_dir = user_data_dir()
        os.makedirs(log_dir, exist_ok=True)
        handler: logging.Handler = logging.FileHandler(
            os.path.join(log_dir, "utility.log"), encoding="utf-8")
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
        root.setLevel(logging.INFO)


_configure_logging()
logger = logging.getLogger(__name__)


def show_about(parent: QWidget, tool_name: Optional[str] = None) -> None:
    """Dialogo 'Informazioni' con autore e versione letta da version.txt."""
    subtitle = f"<br><i>{tool_name}</i>" if tool_name else ""
    QMessageBox.about(
        parent,
        "Informazioni",
        f"<b>{APP_NAME}</b>{subtitle}<br><br>"
        f"Versione: {get_app_version()}<br>"
        f"Autore: {AUTHOR}",
    )


def add_help_menu(menubar: QMenuBar, parent: QWidget,
                  on_guide: Callable[[], None],
                  on_check_updates: Callable[[], None],
                  on_about: Callable[[], None]) -> None:
    """Aggiunge il menu 'Aiuto' standard: Guida, Controlla Aggiornamenti, Informazioni."""
    help_menu = menubar.addMenu("&Aiuto")
    act_guide = QAction("Guida", parent)
    act_guide.setShortcut("F1")
    act_guide.triggered.connect(lambda _=False: on_guide())
    act_update = QAction("Controlla Aggiornamenti", parent)
    act_update.triggered.connect(lambda _=False: on_check_updates())
    act_about = QAction("Informazioni su...", parent)
    act_about.triggered.connect(lambda _=False: on_about())
    help_menu.addAction(act_guide)
    help_menu.addAction(act_update)
    help_menu.addSeparator()
    help_menu.addAction(act_about)


class SortableTableItem(QTableWidgetItem):
    """Cella di tabella che ordina in base a una chiave numerica invece che al testo."""

    def __init__(self, text: str, sort_key: float) -> None:
        super().__init__(text)
        self._sort_key = sort_key

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, SortableTableItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)


class BaseWindow(QWidget):
    """
    Classe base per tutte le finestre della suite PyUtility.
    
    Fornisce metodi comuni per:
    - Centrare la finestra sullo schermo.
    - Applicare il foglio di stile centralizzato (styles.py).
    - Creare la barra dei menu con il menu 'Aiuto' standard
      (Guida, Controlla Aggiornamenti, Informazioni).
    - Mostrare messaggi di errore/informazione standardizzati.
    - Validare percorsi file/directory.
    
    Le sottoclassi definiscono GUIDE_TEXT (testo della guida) e possono
    aggiungere menu propri ridefinendo add_custom_menus().

    Args:
        title (str): Titolo della finestra.
        min_width (int): Larghezza minima (default: 400).
        min_height (int): Altezza minima (default: 500).
        parent (QWidget, optional): Widget genitore (default: None).
    """

    GUIDE_TEXT: str = ""

    def __init__(
        self,
        title: str,
        min_width: int = 400,
        min_height: int = 500,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.tool_name = title
        self._update_controller = None  # creato alla prima richiesta (import lazy)
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
        """Applica il foglio di stile centralizzato della suite."""
        self.setStyleSheet(get_style("secondary"))

    # ------------------------------------------------------------ menu
    def create_menu_bar(self) -> QMenuBar:
        """
        Crea la barra dei menu (da agganciare con layout.setMenuBar):
        menu specifici del tool seguiti dal menu 'Aiuto' standard.
        """
        menubar = QMenuBar(self)
        self.add_custom_menus(menubar)
        add_help_menu(menubar, self, self.show_guide, self.check_updates, self.show_about)
        return menubar

    def add_custom_menus(self, menubar: QMenuBar) -> None:
        """Hook per i menu specifici del tool (default: nessuno)."""

    def show_guide(self) -> None:
        """Mostra la guida all'uso del tool."""
        text = self.GUIDE_TEXT or "Nessuna guida disponibile per questo strumento."
        QMessageBox.information(self, f"Guida - {self.tool_name}", text)

    def show_about(self) -> None:
        """Mostra autore e versione."""
        show_about(self, self.tool_name)

    def check_updates(self) -> None:
        """Verifica manuale degli aggiornamenti (in background)."""
        if self._update_controller is None:
            from update_manager import UpdateController  # import lazy: evita cicli
            self._update_controller = UpdateController(self)
        self._update_controller.check(silent=False)

    @staticmethod
    def set_label_state(label: QLabel, state: str) -> None:
        """
        Imposta lo stato visivo di una label ('muted' o 'ok') tramite la
        proprietà dinamica definita in styles.py, senza colori inline.
        """
        label.setProperty("state", state)
        label.style().unpolish(label)
        label.style().polish(label)

    def closeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        """Interrompe un eventuale download di aggiornamento prima di chiudere."""
        if self._update_controller is not None:
            self._update_controller.shutdown()
        super().closeEvent(event)

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

    def create_vertical_layout(self, margins: tuple = (24, 24, 24, 24), spacing: int = 12) -> QVBoxLayout:
        """
        Crea un layout verticale con margini e spaziatura predefiniti.
        
        Args:
            margins (tuple): Margini (left, top, right, bottom) in pixel (default: (24, 24, 24, 24)).
            spacing (int): Spaziatura tra i widget in pixel (default: 12).
        
        Returns:
            QVBoxLayout: Layout verticale configurato.
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout
