"""Test della logica immagini (conversione, ridimensionamento, unione) senza Qt."""

from pathlib import Path
from typing import List, Tuple

import pytest
from PIL import Image

from image_core import (
    RESIZE_HEIGHT,
    RESIZE_NONE,
    RESIZE_PERCENT,
    RESIZE_WIDTH,
    compute_target_size,
    convert_image,
    merge_images,
)


def _img(path: Path, size: Tuple[int, int] = (40, 20), mode: str = "RGB",
         color: object = "red") -> Path:
    Image.new(mode, size, color).save(path)
    return path


# ------------------------------------------------------------ dimensioni
@pytest.mark.parametrize("mode, value, expected", [
    (RESIZE_NONE, 0, (400, 200)),
    (RESIZE_PERCENT, 50, (200, 100)),
    (RESIZE_WIDTH, 100, (100, 50)),
    (RESIZE_HEIGHT, 50, (100, 50)),
    (RESIZE_PERCENT, 0, (400, 200)),  # valore non valido: dimensione originale
])
def test_compute_target_size(mode: int, value: int, expected: Tuple[int, int]) -> None:
    assert compute_target_size((400, 200), mode, value) == expected


def test_compute_target_size_mai_zero() -> None:
    assert compute_target_size((1000, 1), RESIZE_PERCENT, 10) == (100, 1)


# ------------------------------------------------------------ conversione
def test_convert_image_formato_e_ridimensionamento(tmp_path: Path) -> None:
    src = _img(tmp_path / "a.png", (40, 20), "RGBA", (255, 0, 0, 128))
    out = tmp_path / "out"
    out.mkdir()
    result = convert_image(str(src), str(out), "JPG", RESIZE_PERCENT, 50)
    assert Path(result) == out / "a.jpg"
    with Image.open(result) as img:
        assert img.format == "JPEG"
        assert img.size == (20, 10)
        assert img.mode == "RGB"


def test_convert_image_non_sovrascrive_originale(tmp_path: Path) -> None:
    # Bug v1.5.0: PNG -> PNG nella stessa cartella sostituiva l'originale
    src = _img(tmp_path / "a.png", (40, 20))
    result = convert_image(str(src), str(tmp_path), "PNG", RESIZE_PERCENT, 50)
    assert Path(result) == tmp_path / "a (1).png"
    with Image.open(src) as original:
        assert original.size == (40, 20)


def test_convert_image_omonimi_in_cartelle_diverse(tmp_path: Path) -> None:
    (tmp_path / "x").mkdir()
    (tmp_path / "y").mkdir()
    out = tmp_path / "out"
    out.mkdir()
    first = convert_image(str(_img(tmp_path / "x" / "f.png")), str(out), "BMP", RESIZE_NONE, 0)
    second = convert_image(str(_img(tmp_path / "y" / "f.png")), str(out), "BMP", RESIZE_NONE, 0)
    assert first != second
    assert sorted(p.name for p in out.iterdir()) == ["f (1).bmp", "f.bmp"]


def test_convert_image_file_non_valido(tmp_path: Path) -> None:
    bad = tmp_path / "rotto.png"
    bad.write_bytes(b"non un'immagine")
    with pytest.raises(OSError):
        convert_image(str(bad), str(tmp_path), "JPG", RESIZE_NONE, 0)


# ------------------------------------------------------------ unione
def test_merge_images_verticale(tmp_path: Path) -> None:
    a = _img(tmp_path / "a.jpg", (30, 10))
    b = _img(tmp_path / "b.jpg", (20, 15), color="blue")
    progress: List[Tuple[int, int]] = []
    out = merge_images([str(a), str(b)], str(tmp_path / "m.jpg"), vertical=True,
                       on_progress=lambda d, t: progress.append((d, t)))
    with Image.open(out) as img:
        assert img.size == (30, 25)
    assert progress[-1] == (2, 2)


def test_merge_images_orizzontale_modi_misti(tmp_path: Path) -> None:
    a = _img(tmp_path / "a.png", (10, 10), "RGBA", (0, 0, 0, 0))
    b = _img(tmp_path / "b.png", (10, 20), "L", 128)
    out = merge_images([str(a), str(b)], str(tmp_path / "m.jpg"), vertical=False)
    with Image.open(out) as img:
        assert img.size == (20, 20)
        assert img.mode == "RGB"
        # Le zone trasparenti diventano bianche, non nere
        assert img.getpixel((2, 2)) == (255, 255, 255)


def test_merge_images_richiede_almeno_due(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        merge_images([str(_img(tmp_path / "a.jpg"))], str(tmp_path / "m.jpg"), vertical=True)


def test_merge_images_output_uguale_a_input(tmp_path: Path) -> None:
    a = _img(tmp_path / "a.jpg")
    b = _img(tmp_path / "b.jpg")
    with pytest.raises(ValueError):
        merge_images([str(a), str(b)], str(a), vertical=True)
