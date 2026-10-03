"""
Styles Module
=============
Foglio di stile QSS centralizzato della suite PyUtility.

Regole:
- palette scura con contrasto testo/sfondo WCAG AA (>= 4.5:1, verificato
  da tests/test_styles.py);
- spaziature (padding, margini) in multipli di 4px;
- nessun widget deve definire colori inline: usare objectName o la
  proprietà dinamica "state" (vedi BaseWindow.set_label_state).
"""

from typing import Dict

# ------------------------------------------------------------ palette
PALETTE: Dict[str, str] = {
    "bg": "#2b2b2b",            # sfondo finestre
    "surface": "#333333",       # riquadri, header tabelle
    "surface_alt": "#1e1e1e",   # liste e tabelle
    "input": "#404040",         # campi di input
    "border": "#555555",
    "border_soft": "#444444",
    "text": "#ffffff",
    "text_secondary": "#e0e0e0",
    "text_muted": "#b3b3b3",
    "text_disabled": "#9e9e9e",
    "accent_text": "#4da3ff",   # testo in evidenza (titoli)
    "ok_text": "#81c784",       # testo stato positivo
    "primary": "#0078d4",
    "primary_hover": "#106ebe",
    "primary_pressed": "#005a9e",
    "success": "#2e7d32",
    "success_hover": "#1b5e20",
    "danger": "#c62828",
    "danger_hover": "#b71c1c",
    "move": "#ad1457",
    "move_hover": "#880e4f",
    "neutral": "#444444",
    "neutral_hover": "#555555",
    "secondary": "#555555",
    "secondary_hover": "#666666",
}

# Coppie (testo, sfondo) verificate dai test di contrasto
CONTRAST_PAIRS = [
    ("text_secondary", "bg"), ("text_muted", "bg"), ("accent_text", "bg"), ("ok_text", "bg"),
    ("text_secondary", "surface_alt"), ("text_secondary", "surface"), ("text", "input"),
    ("text", "primary"), ("text", "primary_hover"), ("text", "success"), ("text", "success_hover"),
    ("text", "danger"), ("text", "danger_hover"), ("text", "move"), ("text", "move_hover"),
    ("text", "neutral"), ("text", "neutral_hover"), ("text", "secondary"), ("text", "secondary_hover"),
    ("text_disabled", "surface"),
]

_P = PALETTE

# Stile base per l'applicazione
BASE_STYLE = f"""
    QWidget {{
        background-color: {_P['bg']};
        color: {_P['text']};
        font-family: 'Segoe UI', sans-serif;
    }}
    QLabel {{
        color: {_P['text_secondary']};
        font-size: 14px;
    }}
    QLabel#title {{
        font-size: 24px;
        font-weight: bold;
        color: {_P['accent_text']};
        margin-bottom: 4px;
    }}
    QLabel#subtitle {{
        font-size: 12px;
        color: {_P['text_muted']};
        margin-bottom: 16px;
    }}
    QLabel#sectionTitle {{
        font-weight: bold;
        color: {_P['text_secondary']};
    }}
    QLabel#successTitle {{
        font-size: 22px;
        font-weight: bold;
        color: {_P['ok_text']};
        margin-bottom: 8px;
    }}
    QLabel#colorSwatch {{
        border: 1px solid {_P['border']};
        border-radius: 4px;
    }}
    QLabel[state="muted"] {{
        color: {_P['text_muted']};
    }}
    QLabel[state="ok"] {{
        color: {_P['ok_text']};
    }}
"""

# Stile per i pulsanti
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {_P['neutral']};
        color: {_P['text']};
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        border: 1px solid {_P['border']};
    }}
    QPushButton:hover {{
        background-color: {_P['neutral_hover']};
    }}
    QPushButton:disabled {{
        background-color: {_P['surface']};
        color: {_P['text_disabled']};
    }}
    QPushButton:pressed {{
        background-color: #222222;
    }}
"""

# Stile per pulsanti primari (es. "Aggiungi", "Converti")
PRIMARY_BUTTON_STYLE = f"""
    QPushButton#primaryBtn, QPushButton#addBtn, QPushButton#convertBtn, QPushButton#mergeBtn {{
        background-color: {_P['primary']};
        border: none;
    }}
    QPushButton#primaryBtn:hover, QPushButton#addBtn:hover, QPushButton#convertBtn:hover,
    QPushButton#mergeBtn:hover {{
        background-color: {_P['primary_hover']};
    }}
    QPushButton#primaryBtn:pressed, QPushButton#addBtn:pressed, QPushButton#convertBtn:pressed,
    QPushButton#mergeBtn:pressed {{
        background-color: {_P['primary_pressed']};
    }}
"""

# Stile per pulsanti di successo (es. "Salva", "Avvia")
SUCCESS_BUTTON_STYLE = f"""
    QPushButton#successBtn {{
        background-color: {_P['success']};
        border: none;
    }}
    QPushButton#successBtn:hover {{
        background-color: {_P['success_hover']};
    }}
"""

# Stile per pulsanti di pericolo (es. "Esci", "Elimina")
DANGER_BUTTON_STYLE = f"""
    QPushButton#dangerBtn, QPushButton#exitBtn {{
        background-color: {_P['danger']};
        border: none;
    }}
    QPushButton#dangerBtn:hover, QPushButton#exitBtn:hover {{
        background-color: {_P['danger_hover']};
    }}
"""

# Stile per pulsanti informativi (es. "Scegli colore")
INFO_BUTTON_STYLE = f"""
    QPushButton#infoBtn, QPushButton#helpBtn {{
        background-color: {_P['surface']};
        color: {_P['text_muted']};
        border: 1px solid {_P['border']};
    }}
    QPushButton#infoBtn:hover, QPushButton#helpBtn:hover {{
        color: {_P['text']};
        background-color: {_P['neutral']};
    }}
"""

# Stile per pulsanti secondari (es. "Svuota", "Reset")
SECONDARY_BUTTON_STYLE = f"""
    QPushButton#resetBtn, QPushButton#clearBtn {{
        background-color: {_P['secondary']};
    }}
    QPushButton#resetBtn:hover, QPushButton#clearBtn:hover {{
        background-color: {_P['secondary_hover']};
    }}
"""

# Stile per pulsanti specifici (es. "Copia", "Sposta")
ACTION_BUTTON_STYLE = f"""
    QPushButton#copyBtn {{
        background-color: {_P['success']};
        border: none;
    }}
    QPushButton#copyBtn:hover {{
        background-color: {_P['success_hover']};
    }}
    QPushButton#moveBtn {{
        background-color: {_P['move']};
        border: none;
    }}
    QPushButton#moveBtn:hover {{
        background-color: {_P['move_hover']};
    }}
"""

# Stile per input (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox)
INPUT_STYLE = f"""
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        padding: 4px 8px;
        min-height: 20px;
        background-color: {_P['input']};
        border: 1px solid {_P['border']};
        border-radius: 4px;
        color: {_P['text']};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {_P['primary']};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {_P['surface_alt']};
        border: 1px solid {_P['border_soft']};
        selection-background-color: {_P['primary']};
    }}
"""

# Stile per QCheckBox e QRadioButton
CHECKBOX_STYLE = f"""
    QCheckBox, QRadioButton {{
        spacing: 8px;
        color: {_P['text_secondary']};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid #777777;
        border-radius: 4px;
        background-color: {_P['input']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {_P['primary']};
        border-color: {_P['primary']};
    }}
"""

# Stile per QProgressBar
PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        border: 1px solid {_P['border_soft']};
        border-radius: 4px;
        text-align: center;
        background-color: {_P['surface']};
        color: {_P['text']};
        min-height: 20px;
    }}
    QProgressBar::chunk {{
        background-color: {_P['success']};
        border-radius: 4px;
    }}
"""

# Stile per QListWidget
LIST_WIDGET_STYLE = f"""
    QListWidget {{
        background-color: {_P['surface_alt']};
        border: 1px solid {_P['border_soft']};
        border-radius: 4px;
        padding: 4px;
        color: {_P['text_secondary']};
    }}
    QListWidget::item:selected {{
        background-color: {_P['primary']};
        color: {_P['text']};
    }}
    QListWidget::item:hover {{
        background-color: {_P['surface']};
    }}
"""

# Stile per QTableWidget
TABLE_WIDGET_STYLE = f"""
    QTableWidget {{
        background-color: {_P['surface_alt']};
        gridline-color: {_P['border_soft']};
        border: 1px solid {_P['border']};
        color: {_P['text_secondary']};
    }}
    QHeaderView::section {{
        background-color: {_P['surface']};
        padding: 4px;
        border: 1px solid {_P['border_soft']};
        color: {_P['text_secondary']};
        font-weight: bold;
    }}
    QTableWidget::item {{
        padding: 4px;
    }}
    QTableWidget::item:selected {{
        background-color: {_P['primary']};
        color: {_P['text']};
    }}
"""

# Stile per QFrame (riquadri di raggruppamento).
# ".QFrame" = solo istanze esatte: QLabel, QListWidget e QTableWidget derivano da QFrame.
FRAME_STYLE = f"""
    .QFrame {{
        background-color: {_P['surface']};
        border-radius: 8px;
        padding: 8px;
    }}
    .QFrame QLabel, .QFrame QRadioButton, .QFrame QCheckBox {{
        background-color: transparent;
    }}
"""

# Stile per QMessageBox, QDialog e QProgressDialog
DIALOG_STYLE = f"""
    QDialog, QMessageBox {{
        background-color: {_P['surface_alt']};
    }}
    QMessageBox QLabel {{
        color: {_P['text']};
        font-size: 13px;
    }}
    QMessageBox QPushButton, QDialog QPushButton {{
        background-color: {_P['primary']};
        color: {_P['text']};
        padding: 8px 24px;
        border: none;
        border-radius: 4px;
    }}
    QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
        background-color: {_P['primary_hover']};
    }}
    QMessageBox QTextEdit {{
        background-color: {_P['bg']};
        color: {_P['text_secondary']};
    }}
"""
# Retrocompatibilità con il vecchio nome
MESSAGE_BOX_STYLE = DIALOG_STYLE

# Stile per QMenuBar e QMenu
MENU_STYLE = f"""
    QMenuBar {{
        background-color: #2d2d2d;
        color: {_P['text']};
        padding: 4px;
    }}
    QMenuBar::item {{
        padding: 4px 8px;
        background-color: transparent;
    }}
    QMenuBar::item:selected {{
        background-color: {_P['primary']};
    }}
    QMenu {{
        background-color: #2d2d2d;
        color: {_P['text']};
        border: 1px solid {_P['border']};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 4px 24px 4px 16px;
    }}
    QMenu::item:selected {{
        background-color: {_P['primary']};
    }}
"""

# Stile completo per l'hub principale (src/main.py)
MAIN_SUITE_STYLE = (
    BASE_STYLE + BUTTON_STYLE + PRIMARY_BUTTON_STYLE + DANGER_BUTTON_STYLE +
    PROGRESS_BAR_STYLE + MENU_STYLE + DIALOG_STYLE
)

# Stile completo per le finestre secondarie
SECONDARY_WINDOW_STYLE = (
    BASE_STYLE + BUTTON_STYLE + PRIMARY_BUTTON_STYLE + SUCCESS_BUTTON_STYLE +
    DANGER_BUTTON_STYLE + INFO_BUTTON_STYLE + SECONDARY_BUTTON_STYLE + ACTION_BUTTON_STYLE +
    INPUT_STYLE + CHECKBOX_STYLE + PROGRESS_BAR_STYLE + LIST_WIDGET_STYLE + TABLE_WIDGET_STYLE +
    FRAME_STYLE + DIALOG_STYLE + MENU_STYLE
)


def get_style(style_type: str = "secondary") -> str:
    """
    Restituisce il foglio di stile QSS in base al tipo richiesto.

    Args:
        style_type (str): "main" per l'hub principale, "secondary" per i tool.

    Returns:
        str: Stringa QSS con lo stile richiesto.
    """
    if style_type == "main":
        return MAIN_SUITE_STYLE
    return SECONDARY_WINDOW_STYLE
