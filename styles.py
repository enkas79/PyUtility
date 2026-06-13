"""
Styles Module
=============
Modulo per la gestione degli stili CSS dell'applicazione PyUtility.
Contiene stili predefiniti per tutti i componenti Qt.
"""


# Stile base per l'applicazione
BASE_STYLE = """
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
"""

# Stile per i pulsanti
BUTTON_STYLE = """
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
    QPushButton:pressed { 
        background-color: #222; 
    }
"""

# Stile per pulsanti primari (es. "Aggiungi", "Converti")
PRIMARY_BUTTON_STYLE = """
    QPushButton#primaryBtn, QPushButton#addBtn, QPushButton#convertBtn, QPushButton#mergeBtn { 
        background-color: #0078d4; 
        border: none; 
    }
    QPushButton#primaryBtn:hover, QPushButton#addBtn:hover, QPushButton#convertBtn:hover, QPushButton#mergeBtn:hover { 
        background-color: #1e90ff; 
    }
"""

# Stile per pulsanti di successo (es. "Salva", "Completa")
SUCCESS_BUTTON_STYLE = """
    QPushButton#successBtn { 
        background-color: #00c853; 
        border: none; 
    }
    QPushButton#successBtn:hover { 
        background-color: #4caf50; 
    }
"""

# Stile per pulsanti di pericolo (es. "Esci", "Elimina")
DANGER_BUTTON_STYLE = """
    QPushButton#dangerBtn, QPushButton#exitBtn { 
        background-color: #d32f2f; 
        border: none; 
    }
    QPushButton#dangerBtn:hover, QPushButton#exitBtn:hover { 
        background-color: #ff5252; 
    }
"""

# Stile per pulsanti informativi (es. "Info", "Guida")
INFO_BUTTON_STYLE = """
    QPushButton#infoBtn, QPushButton#helpBtn { 
        background-color: #333; 
        color: #aaa; 
        border: 1px solid #555; 
    }
    QPushButton#infoBtn:hover, QPushButton#helpBtn:hover { 
        color: #fff; 
        background-color: #444; 
    }
"""

# Stile per pulsanti secondari (es. "Svuota", "Reset")
SECONDARY_BUTTON_STYLE = """
    QPushButton#resetBtn, QPushButton#clearBtn { 
        background-color: #555; 
    }
    QPushButton#resetBtn:hover, QPushButton#clearBtn:hover { 
        background-color: #666; 
    }
"""

# Stile per pulsanti specifici (es. "Copia", "Sposta")
ACTION_BUTTON_STYLE = """
    QPushButton#copyBtn { 
        background-color: #00c853; 
        border: none; 
    }
    QPushButton#copyBtn:hover { 
        background-color: #4caf50; 
    }
    QPushButton#moveBtn { 
        background-color: #d81b60; 
        border: none; 
    }
    QPushButton#moveBtn:hover { 
        background-color: #e91e63; 
    }
"""

# Stile per input (QLineEdit, QComboBox, QSpinBox)
INPUT_STYLE = """
    QLineEdit, QComboBox, QSpinBox { 
        padding: 6px; 
        background-color: #404040; 
        border: 1px solid #555; 
        border-radius: 4px; 
        color: white; 
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus { 
        border-color: #0078d4; 
    }
    QComboBox::drop-down { 
        border: none; 
    }
    QComboBox QAbstractItemView { 
        background-color: #1e1e1e; 
        border: 1px solid #444; 
        selection-background-color: #0078d4; 
    }
"""

# Stile per QProgressBar
PROGRESS_BAR_STYLE = """
    QProgressBar { 
        border: 1px solid #444; 
        border-radius: 5px; 
        text-align: center; 
        background-color: #333; 
        min-height: 20px; 
    }
    QProgressBar::chunk { 
        background-color: #00c853; 
        border-radius: 4px; 
    }
"""

# Stile per QListWidget
LIST_WIDGET_STYLE = """
    QListWidget { 
        background-color: #1e1e1e; 
        border: 1px solid #444; 
        border-radius: 4px; 
        padding: 5px; 
        color: #e0e0e0; 
    }
    QListWidget::item:selected { 
        background-color: #0078d4; 
        color: white; 
    }
    QListWidget::item:hover { 
        background-color: #333; 
    }
"""

# Stile per QTableWidget
TABLE_WIDGET_STYLE = """
    QTableWidget { 
        background-color: #1e1e1e; 
        gridline-color: #444; 
        border: 1px solid #555; 
        color: #e0e0e0; 
    }
    QHeaderView::section { 
        background-color: #333; 
        padding: 4px; 
        border: 1px solid #444; 
        color: #ccc; 
        font-weight: bold; 
    }
    QTableWidget::item { 
        padding: 4px; 
    }
    QTableWidget::item:selected { 
        background-color: #0078d4; 
        color: white; 
    }
"""

# Stile per QFrame
FRAME_STYLE = """
    QFrame { 
        background-color: #333; 
        border-radius: 6px; 
        padding: 5px; 
    }
"""

# Stile per QMessageBox
MESSAGE_BOX_STYLE = """
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
        border-radius: 4px; 
    }
    QMessageBox QPushButton:hover { 
        background-color: #1e90ff; 
    }
"""

# Stile per QMenuBar e QMenu
MENU_STYLE = """
    QMenuBar { 
        background-color: #2d2d2d; 
        color: white; 
        padding: 4px; 
    }
    QMenuBar::item:selected { 
        background-color: #0078d4; 
    }
    QMenu { 
        background-color: #2d2d2d; 
        color: white; 
        border: 1px solid #555; 
    }
    QMenu::item:selected { 
        background-color: #0078d4; 
    }
"""

# Stile completo per l'applicazione principale (MainSuite)
MAIN_SUITE_STYLE = BASE_STYLE + BUTTON_STYLE + PRIMARY_BUTTON_STYLE + DANGER_BUTTON_STYLE + MENU_STYLE + MESSAGE_BOX_STYLE

# Stile completo per le finestre secondarie
SECONDARY_WINDOW_STYLE = (
    BASE_STYLE + BUTTON_STYLE + PRIMARY_BUTTON_STYLE + SUCCESS_BUTTON_STYLE +
    DANGER_BUTTON_STYLE + INFO_BUTTON_STYLE + SECONDARY_BUTTON_STYLE + ACTION_BUTTON_STYLE +
    INPUT_STYLE + PROGRESS_BAR_STYLE + LIST_WIDGET_STYLE + TABLE_WIDGET_STYLE + FRAME_STYLE + MESSAGE_BOX_STYLE
)


def get_style(style_type: str = "secondary") -> str:
    """
    Restituisce lo stile CSS in base al tipo richiesto.
    
    Args:
        style_type (str): Tipo di stile ("main" per MainSuite, "secondary" per le altre finestre).
    
    Returns:
        str: Stringa CSS con lo stile richiesto.
    """
    if style_type == "main":
        return MAIN_SUITE_STYLE
    else:
        return SECONDARY_WINDOW_STYLE
