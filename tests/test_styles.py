"""Verifiche sul foglio di stile centralizzato: contrasto WCAG AA e griglia 4px."""

import re

import pytest

from styles import CONTRAST_PAIRS, PALETTE, get_style


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


@pytest.mark.parametrize("fg, bg", CONTRAST_PAIRS)
def test_contrasto_wcag_aa(fg: str, bg: str) -> None:
    assert _contrast(PALETTE[fg], PALETTE[bg]) >= 4.5, (fg, bg)


@pytest.mark.parametrize("style_type", ["main", "secondary"])
def test_spaziature_multipli_di_4(style_type: str) -> None:
    qss = get_style(style_type)
    for prop, value in re.findall(r"(padding|margin[\w-]*|spacing)\s*:\s*([^;]+);", qss):
        for px in re.findall(r"(\d+)px", value):
            assert int(px) % 4 == 0, f"{prop}: {value}"
