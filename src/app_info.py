"""
App Info
========
Metadati dell'applicazione e accesso alle risorse del progetto.
Modulo privo di dipendenze Qt: utilizzabile da GUI, updater e test.
"""

import logging
import os
import sys

APP_NAME = "Py Utility Suite"
AUTHOR = "Enrico Martini"
REPO_OWNER = "enkas79"
REPO_NAME = "PyUtility"
# Pagina usata quando la release non contiene un installer per la piattaforma corrente
FALLBACK_DOWNLOAD_URL = "https://mindnetwork.vip/download.php"

logger = logging.getLogger(__name__)


def project_root() -> str:
    """
    Cartella che contiene version.txt e assets/: la root del repository in
    sviluppo, la cartella temporanea _MEIPASS nell'eseguibile PyInstaller.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    # src/app_info.py -> root del progetto
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(relative_path: str) -> str:
    """Restituisce il percorso assoluto di una risorsa del progetto."""
    return os.path.join(project_root(), relative_path)


def get_app_version(default: str = "0.0.0") -> str:
    """
    Legge la versione corrente dal file version.txt nella root del progetto.

    Args:
        default (str): Valore restituito se version.txt non è leggibile.

    Returns:
        str: Numero di versione (es. "1.2.0").
    """
    try:
        with open(resource_path("version.txt"), "r", encoding="utf-8") as f:
            return f.read().strip() or default
    except OSError:
        logger.warning("Impossibile leggere version.txt, uso versione di default %s", default)
        return default


def user_data_dir() -> str:
    """
    Cartella scrivibile dell'utente per log e file temporanei dell'app
    (la cartella di installazione può essere in sola lettura).
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "PyUtilitySuite")
