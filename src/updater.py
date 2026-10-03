"""
Updater
=======
Logica di business dell'autoupdate (nessuna dipendenza Qt):
interrogazione delle GitHub Releases, confronto versioni, scelta
dell'installer per la piattaforma, download e avvio dell'installazione.
I thread Qt che la usano sono in update_manager.
"""

import json
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

USER_AGENT = "PyUtilitySuite-Updater"
CHUNK_SIZE = 64 * 1024

ProgressCallback = Callable[[int, int], None]  # (byte scaricati, byte totali)
StopCallback = Callable[[], bool]


class UpdateCancelled(Exception):
    """Download interrotto su richiesta dell'utente."""


@dataclass(frozen=True)
class ReleaseAsset:
    """File allegato a una release (installer, binario, pacchetto)."""
    name: str
    url: str
    size: int = 0


@dataclass(frozen=True)
class ReleaseInfo:
    """Dati essenziali di una release pubblicata."""
    version: str
    changelog: str
    html_url: str
    assets: List[ReleaseAsset] = field(default_factory=list)


# ------------------------------------------------------------ versioni
def parse_version(version: str) -> Tuple[int, ...]:
    """Converte '1.10.0' (o 'v1.10.0') in tupla numerica di almeno 3 elementi."""
    parts: List[int] = []
    for chunk in version.strip().lstrip("vV").split("."):
        parts.append(int(chunk) if chunk.isdigit() else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer(remote_version: str, local_version: str) -> bool:
    """True se la versione remota è strettamente maggiore (confronto numerico)."""
    return parse_version(remote_version) > parse_version(local_version)


# ------------------------------------------------------------ release
def parse_release(data: dict) -> ReleaseInfo:
    """Costruisce ReleaseInfo dal JSON dell'API GitHub 'releases/latest'."""
    tag = str(data.get("tag_name") or "").strip()
    if not tag:
        raise ValueError("Release senza tag_name")
    assets = [
        ReleaseAsset(
            name=str(a.get("name", "")),
            url=str(a.get("browser_download_url", "")),
            size=int(a.get("size") or 0),
        )
        for a in data.get("assets") or []
        if a.get("name") and a.get("browser_download_url")
    ]
    return ReleaseInfo(
        version=tag.lstrip("vV"),
        changelog=str(data.get("body") or "").strip(),
        html_url=str(data.get("html_url") or ""),
        assets=assets,
    )


def fetch_latest_release(owner: str, repo: str, timeout: float = 10.0) -> ReleaseInfo:
    """
    Interroga l'API GitHub per l'ultima release pubblicata.

    Raises:
        OSError: errori di rete/HTTP.
        ValueError: risposta non valida.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return parse_release(json.loads(response.read().decode("utf-8")))


def select_asset(release: ReleaseInfo, platform: str = sys.platform) -> Optional[ReleaseAsset]:
    """Sceglie l'installer adatto alla piattaforma (None se non disponibile)."""
    names = {a.name.lower(): a for a in release.assets}
    if platform.startswith("win"):
        for lower, asset in names.items():
            if "setup" in lower and lower.endswith(".exe"):
                return asset
    elif platform.startswith("linux"):
        for lower, asset in names.items():
            if lower.endswith(".deb"):
                return asset
    return None


# ------------------------------------------------------------ download
def download_asset(
    asset: ReleaseAsset,
    dest_dir: str,
    on_progress: Optional[ProgressCallback] = None,
    should_stop: Optional[StopCallback] = None,
    opener: Callable = urllib.request.urlopen,
    timeout: float = 30.0,
) -> str:
    """
    Scarica l'asset in dest_dir passando da un file '.part', rinominato solo
    a download completato: un installer troncato non viene mai lasciato su disco.

    Returns:
        str: Percorso del file scaricato.

    Raises:
        UpdateCancelled: se should_stop() diventa True.
        ValueError: nome file non sicuro.
        OSError: errori di rete o di scrittura.
    """
    filename = os.path.basename(asset.name)
    if not filename or filename != asset.name or filename in (".", ".."):
        raise ValueError(f"Nome file non valido: {asset.name!r}")

    os.makedirs(dest_dir, exist_ok=True)
    final_path = os.path.join(dest_dir, filename)
    part_path = final_path + ".part"
    request = urllib.request.Request(asset.url, headers={"User-Agent": USER_AGENT})

    try:
        with opener(request, timeout=timeout) as response, open(part_path, "wb") as out:
            total = asset.size or int(getattr(response, "headers", {}).get("Content-Length", 0) or 0)
            done = 0
            while True:
                if should_stop is not None and should_stop():
                    raise UpdateCancelled()
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if on_progress is not None:
                    on_progress(done, max(total, done))
        os.replace(part_path, final_path)
    except BaseException:
        # Pulizia del file parziale in caso di errore o annullamento
        if os.path.exists(part_path):
            os.remove(part_path)
        raise
    return final_path


# ------------------------------------------------------------ installazione
def build_install_command(installer_path: str, platform: str = sys.platform) -> List[str]:
    """
    Comando che avvia l'installazione:
    - Windows: esegue il setup Inno Setup (sostituisce la versione installata);
    - Linux: apre il .deb con il gestore pacchetti del desktop.
    """
    if platform.startswith("win"):
        return [installer_path]
    if platform.startswith("linux"):
        return ["xdg-open", installer_path]
    raise OSError(f"Installazione automatica non supportata su {platform}")


def launch_installer(installer_path: str) -> None:
    """Avvia l'installer come processo indipendente dall'applicazione."""
    command = build_install_command(installer_path)
    if sys.platform.startswith("win"):
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        subprocess.Popen(command, creationflags=flags, close_fds=True)
    else:
        subprocess.Popen(command, start_new_session=True, close_fds=True)
