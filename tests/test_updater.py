"""Test della logica di aggiornamento (modulo updater, nessuna dipendenza Qt)."""

import hashlib
import io
import json
from pathlib import Path
from typing import List, Tuple

import pytest

from updater import (
    ChecksumMismatch,
    ReleaseAsset,
    ReleaseInfo,
    UpdateCancelled,
    build_install_command,
    download_asset,
    download_verified,
    find_checksum_asset,
    parse_checksum,
    sha256_file,
    is_newer,
    parse_release,
    parse_version,
    select_asset,
)

RELEASE_JSON = {
    "tag_name": "v1.6.0",
    "body": "- Nuova funzione\n- Fix vari",
    "html_url": "https://github.com/enkas79/PyUtility/releases/tag/v1.6.0",
    "assets": [
        {"name": "PyUtilitySuite.exe", "browser_download_url": "https://x/PyUtilitySuite.exe", "size": 10},
        {"name": "PyUtilitySuite_Setup_v1.6.0.exe", "browser_download_url": "https://x/setup.exe", "size": 20},
        {"name": "PyUtilitySuite_v1.6.0_amd64.deb", "browser_download_url": "https://x/suite.deb", "size": 30},
        {"name": "PyUtilitySuite_v1.6.0_amd64.deb.sha256", "browser_download_url": "https://x/suite.deb.sha256",
         "size": 1},
    ],
}


# ------------------------------------------------------------ versioni
@pytest.mark.parametrize("raw, expected", [
    ("1.2.3", (1, 2, 3)),
    ("v1.10.0", (1, 10, 0)),
    ("2", (2, 0, 0)),
    ("1.x.4", (1, 0, 4)),
    ("", (0, 0, 0)),
])
def test_parse_version(raw: str, expected: Tuple[int, ...]) -> None:
    assert parse_version(raw) == expected


@pytest.mark.parametrize("remote, local, expected", [
    ("1.10.0", "1.9.0", True),
    ("1.4.0", "1.4.0", False),
    ("1.4", "1.4.0", False),
    ("v1.4.1", "1.4.0", True),
    ("1.3.9", "1.4.0", False),
    ("", "1.4.0", False),
])
def test_is_newer(remote: str, local: str, expected: bool) -> None:
    assert is_newer(remote, local) is expected


# ------------------------------------------------------------ release
def test_parse_release() -> None:
    info = parse_release(RELEASE_JSON)
    assert info.version == "1.6.0"
    assert info.changelog.startswith("- Nuova funzione")
    assert info.html_url.endswith("v1.6.0")
    assert [a.name for a in info.assets][1] == "PyUtilitySuite_Setup_v1.6.0.exe"
    assert info.assets[2].size == 30


def test_parse_release_campi_mancanti() -> None:
    info = parse_release({"tag_name": "v2.0.0"})
    assert info.version == "2.0.0"
    assert info.changelog == ""
    assert info.assets == []


def test_parse_release_senza_tag_solleva() -> None:
    with pytest.raises(ValueError):
        parse_release({"body": "x"})


@pytest.mark.parametrize("platform, expected", [
    ("win32", "PyUtilitySuite_Setup_v1.6.0.exe"),
    ("linux", "PyUtilitySuite_v1.6.0_amd64.deb"),
])
def test_select_asset_per_piattaforma(platform: str, expected: str) -> None:
    asset = select_asset(parse_release(RELEASE_JSON), platform)
    assert asset is not None and asset.name == expected


def test_select_asset_ignora_file_checksum() -> None:
    asset = select_asset(parse_release(RELEASE_JSON), "linux")
    assert asset is not None and not asset.name.endswith(".sha256")


def test_select_asset_piattaforma_non_supportata() -> None:
    assert select_asset(parse_release(RELEASE_JSON), "darwin") is None


def test_select_asset_nessun_installer() -> None:
    info = ReleaseInfo(version="1.6.0", changelog="", html_url="", assets=[])
    assert select_asset(info, "win32") is None


# ------------------------------------------------------------ download
class _FakeResponse(io.BytesIO):
    """Risposta HTTP minimale compatibile con il context manager di urlopen."""

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _fake_opener(payload: bytes):
    def opener(request, timeout: float = 0):  # noqa: ANN001 - firma di urlopen
        return _FakeResponse(payload)
    return opener


def test_download_asset_scrive_file_e_notifica_progresso(tmp_path: Path) -> None:
    payload = b"x" * 200_000
    asset = ReleaseAsset(name="setup.exe", url="https://x/setup.exe", size=len(payload))
    progress: List[Tuple[int, int]] = []

    path = download_asset(asset, str(tmp_path), on_progress=lambda d, t: progress.append((d, t)),
                          opener=_fake_opener(payload))

    assert Path(path) == tmp_path / "setup.exe"
    assert Path(path).read_bytes() == payload
    assert progress[-1] == (len(payload), len(payload))
    assert not list(tmp_path.glob("*.part"))


def test_download_asset_annullato_non_lascia_file(tmp_path: Path) -> None:
    asset = ReleaseAsset(name="setup.exe", url="https://x/setup.exe", size=200_000)
    with pytest.raises(UpdateCancelled):
        download_asset(asset, str(tmp_path), should_stop=lambda: True,
                       opener=_fake_opener(b"x" * 200_000))
    assert list(tmp_path.iterdir()) == []


def test_download_asset_nome_non_sicuro(tmp_path: Path) -> None:
    asset = ReleaseAsset(name="../evil.exe", url="https://x/e", size=1)
    with pytest.raises(ValueError):
        download_asset(asset, str(tmp_path), opener=_fake_opener(b"x"))


# ------------------------------------------------------------ installazione
def test_build_install_command_windows() -> None:
    assert build_install_command("C:\\tmp\\setup.exe", "win32") == ["C:\\tmp\\setup.exe"]


def test_build_install_command_linux() -> None:
    assert build_install_command("/tmp/suite.deb", "linux") == ["xdg-open", "/tmp/suite.deb"]


def test_build_install_command_non_supportato() -> None:
    with pytest.raises(OSError):
        build_install_command("/tmp/x", "darwin")


def test_release_json_serializzabile() -> None:
    # Garantisce che il fixture rispecchi un payload JSON reale
    assert parse_release(json.loads(json.dumps(RELEASE_JSON))).version == "1.6.0"


# ------------------------------------------------------------ checksum
DIGEST = hashlib.sha256(b"installer").hexdigest()


def test_find_checksum_asset() -> None:
    info = parse_release(RELEASE_JSON)
    deb = select_asset(info, "linux")
    setup = select_asset(info, "win32")
    assert find_checksum_asset(info, deb).name == "PyUtilitySuite_v1.6.0_amd64.deb.sha256"
    assert find_checksum_asset(info, setup) is None


@pytest.mark.parametrize("text", [
    f"{DIGEST}  setup.exe\n",
    f"{DIGEST.upper()} *setup.exe",
    f"{DIGEST}",
    f"altro_hash  altro.exe\n{DIGEST}  setup.exe\n",
])
def test_parse_checksum_formati(text: str) -> None:
    assert parse_checksum(text, "setup.exe") == DIGEST


@pytest.mark.parametrize("text", ["", "non-esadecimale  setup.exe", f"{DIGEST}  altro.exe"])
def test_parse_checksum_non_valido(text: str) -> None:
    with pytest.raises(ValueError):
        parse_checksum(text, "setup.exe")


def test_sha256_file(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"installer")
    assert sha256_file(str(f)) == DIGEST


def _url_opener(payloads: dict):
    def opener(request, timeout: float = 0):  # noqa: ANN001 - firma di urlopen
        return _FakeResponse(payloads[request.full_url])
    return opener


def test_download_verified_ok(tmp_path: Path) -> None:
    asset = ReleaseAsset("setup.exe", "https://x/setup.exe", 9)
    check = ReleaseAsset("setup.exe.sha256", "https://x/setup.exe.sha256", 80)
    opener = _url_opener({asset.url: b"installer", check.url: f"{DIGEST}  setup.exe".encode()})
    path = download_verified(asset, check, str(tmp_path), opener=opener)
    assert Path(path).read_bytes() == b"installer"


def test_download_verified_hash_errato_elimina_file(tmp_path: Path) -> None:
    asset = ReleaseAsset("setup.exe", "https://x/setup.exe", 9)
    check = ReleaseAsset("setup.exe.sha256", "https://x/setup.exe.sha256", 80)
    opener = _url_opener({asset.url: b"manomesso", check.url: f"{DIGEST}  setup.exe".encode()})
    with pytest.raises(ChecksumMismatch):
        download_verified(asset, check, str(tmp_path), opener=opener)
    assert list(tmp_path.iterdir()) == []
