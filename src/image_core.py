"""
Image Core
==========
Logica di business dei tool immagine (nessuna dipendenza Qt):
conversione/ridimensionamento (ConvImage) e unione (MergeImage).
"""

import os
from typing import Callable, List, Optional, Tuple

from PIL import Image

from file_lister_core import unique_destination

# Modalità di ridimensionamento (stesso ordine della combo in ConvImage)
RESIZE_NONE, RESIZE_PERCENT, RESIZE_WIDTH, RESIZE_HEIGHT = range(4)

# Formato visualizzato -> formato Pillow
PIL_FORMATS = {
    "JPG": "JPEG", "JPEG": "JPEG", "PNG": "PNG", "WEBP": "WEBP",
    "BMP": "BMP", "ICO": "ICO", "TIFF": "TIFF",
}
NO_ALPHA_FORMATS = ("JPEG", "BMP")
DEFAULT_JPEG_QUALITY = 90
MERGE_JPEG_QUALITY = 95

ProgressCallback = Callable[[int, int], None]  # (elementi elaborati, totale)


def compute_target_size(size: Tuple[int, int], mode: int, value: int) -> Tuple[int, int]:
    """
    Calcola le nuove dimensioni mantenendo le proporzioni.
    Valori non validi (<= 0) lasciano la dimensione originale; il risultato è sempre >= 1px.
    """
    w, h = size
    if value <= 0 or mode == RESIZE_NONE:
        return w, h
    if mode == RESIZE_PERCENT:
        new_w, new_h = w * value / 100.0, h * value / 100.0
    elif mode == RESIZE_WIDTH:
        new_w, new_h = value, h * value / float(w)
    elif mode == RESIZE_HEIGHT:
        new_w, new_h = w * value / float(h), value
    else:
        return w, h
    return max(1, int(new_w)), max(1, int(new_h))


def flatten_alpha(img: Image.Image, background: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Converte in RGB componendo la trasparenza su sfondo pieno (default bianco)."""
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode in ("RGBA", "LA"):
        base = Image.new("RGB", img.size, background)
        base.paste(img, mask=img.split()[-1])
        return base
    return img.convert("RGB") if img.mode != "RGB" else img


def convert_image(src_path: str, out_dir: str, target_format: str, resize_mode: int,
                  resize_value: int, quality: int = DEFAULT_JPEG_QUALITY) -> str:
    """
    Converte (ed eventualmente ridimensiona) un'immagine in out_dir.
    Non sovrascrive mai: in caso di omonimia (incluso l'originale) aggiunge ' (n)'.

    Returns:
        str: Percorso del file creato.

    Raises:
        OSError: file non leggibile/non immagine o errore di scrittura.
    """
    fmt = target_format.upper()
    pil_format = PIL_FORMATS.get(fmt, "PNG")
    stem = os.path.splitext(os.path.basename(src_path))[0]

    with Image.open(src_path) as original:
        img: Image.Image = original
        if img.mode == "P":
            img = img.convert("RGBA")

        new_size = compute_target_size(img.size, resize_mode, resize_value)
        if new_size != img.size:
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        if pil_format in NO_ALPHA_FORMATS:
            img = flatten_alpha(img)
        elif img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGBA")

        out_path = unique_destination(out_dir, f"{stem}.{fmt.lower()}")
        if pil_format in ("JPEG", "WEBP"):
            img.save(out_path, pil_format, quality=quality)
        else:
            img.save(out_path, pil_format)
    return out_path


def merge_images(paths: List[str], out_path: str, vertical: bool,
                 on_progress: Optional[ProgressCallback] = None,
                 quality: int = MERGE_JPEG_QUALITY) -> str:
    """
    Unisce le immagini in un unico JPEG, in verticale o in orizzontale,
    su sfondo bianco (anche le zone trasparenti diventano bianche).

    Raises:
        ValueError: meno di due immagini o output coincidente con un input.
        OSError: file non leggibili o errore di scrittura.
    """
    if len(paths) < 2:
        raise ValueError("Servono almeno due immagini da unire.")
    out_abs = os.path.normcase(os.path.abspath(out_path))
    if any(os.path.normcase(os.path.abspath(p)) == out_abs for p in paths):
        raise ValueError("Il file di destinazione non può essere una delle immagini da unire.")

    images: List[Image.Image] = []
    try:
        images = [Image.open(p) for p in paths]
        if vertical:
            canvas = Image.new("RGB", (max(i.width for i in images), sum(i.height for i in images)),
                               (255, 255, 255))
        else:
            canvas = Image.new("RGB", (sum(i.width for i in images), max(i.height for i in images)),
                               (255, 255, 255))
        offset = 0
        for n, img in enumerate(images, start=1):
            position = (0, offset) if vertical else (offset, 0)
            canvas.paste(flatten_alpha(img), position)
            offset += img.height if vertical else img.width
            if on_progress is not None:
                on_progress(n, len(images))
        canvas.save(out_path, "JPEG", quality=quality)
    finally:
        for img in images:
            img.close()
    return out_path
