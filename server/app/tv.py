import re
from typing import List, Optional, Tuple

from . import codes
from .specs import Specs, screen_label

CATEGORY = "Телевизоры"

_INCH = re.compile(r"(?<![\d.,])(\d{2,3})(?:[.,]\d)?\s*(?:\"|″|”|''|дюйм|inch)", re.IGNORECASE)
_CM = re.compile(r"(?<![\d.,])(\d{2,3})(?:[.,]\d)?\s*(?:cm|см)\b", re.IGNORECASE)
_SIZES = (19, 22, 24, 27, 32, 40, 42, 43, 48, 50, 55, 58, 60, 65, 70, 75, 77, 83, 85, 86, 98, 100,
          115, 116)
_FILLER = frozenset({
    "tv", "smart", "led", "qled", "oled", "miniled", "mini", "micro", "rgb", "qd", "4k", "8k",
    "uhd", "hd", "ultra", "full", "ready", "google", "android", "televizor", "hdr", "wifi",
    "wi-fi", "black", "white", "grey", "gray", "silver", "dark", "titan", "evo", "neo",
    "nanocell", "qned", "hi-qled", "dled", "by",
})


def _extra(title: str, details: str, brand: str) -> Optional[str]:
    inches = diagonal(title, details, brand)
    return str(inches) if inches else None


KIND = codes.Kind(CATEGORY, filler=_FILLER, head=r"телевизор|televizor", extra=_extra,
                  name_word="TV")
aliases = codes.aliases

_MATRICES = [
    (r"micro\s*rgb", "Micro RGB"),
    (r"rgb\s*-?\s*mini\s*-?\s*led|mini\s*-?\s*rgb|mrgb", "RGB Mini LED"),
    (r"qd\s*-?\s*oled", "QD-OLED"),
    (r"\boled\b|\boled(?=\d)", "OLED"),
    (r"neo\s*qled", "Neo QLED"),
    (r"mini\s*-?\s*led", "Mini LED"),
    (r"nano\s*cell|nano\d", "NanoCell"),
    (r"qned", "QNED"),
    (r"qled", "QLED"),
    (r"\b(?:d|edge\s*)?led\b", "LED"),
]
_PLATFORMS = [
    (r"google\s*tv", "Google TV"),
    (r"android", "Android TV"),
    (r"tizen", "Tizen"),
    (r"web\s*os|\(web\)", "webOS"),
    (r"vidaa", "VIDAA"),
    (r"titan\s*os", "Titan OS"),
]


def diagonal(title: str, details: str = "", brand: str = "") -> Optional[int]:
    match = _INCH.search(title)
    if match:
        return int(match.group(1))
    found = code(title, brand)
    if found:
        digits = re.search(r"\d{2,3}", found[0])
        if digits and 19 <= int(digits.group(0)) <= 120:
            return int(digits.group(0))
    match = _INCH.search(details or "")
    if match:
        return int(match.group(1))
    for _, lower in codes.after_brand(codes.tokens(KIND, title), brand):
        if lower.isdigit() and int(lower) in _SIZES:
            return int(lower)
    match = _CM.search("%s %s" % (title, details or ""))
    if match:
        inches = int(match.group(1)) / 2.54
        return min(_SIZES, key=lambda size: abs(size - inches))
    return None


def key(title: str, brand: str, details: str = "") -> str:
    return codes.key(KIND, title, brand, details)


def code(title: str, brand: str) -> Optional[Tuple[str, str]]:
    return codes.code(KIND, title, brand)


def _first(patterns, text: str) -> Optional[str]:
    for pattern, label in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return None


def _resolution(text: str) -> Optional[str]:
    if re.search(r"7680|\b8k\b", text, re.IGNORECASE):
        return "8K"
    if re.search(r"3840|\b4k\b|uhd|ultra\s*hd", text, re.IGNORECASE):
        return "4K Ultra HD"
    if re.search(r"1920|full\s*hd|\bfhd\b", text, re.IGNORECASE):
        return "Full HD"
    if re.search(r"1366|1280|hd\s*ready|\bhd\b", text, re.IGNORECASE):
        return "HD"
    return None


def parse_specs(title: str, details: str = "", brand: str = "") -> Specs:
    text = "%s %s" % (title, details or "")
    specs = Specs()
    inches = diagonal(title, details, brand)
    if inches:
        specs.screen = float(inches)
        specs.display["Экран"] = screen_label(inches)
    resolution = _resolution(text)
    if resolution:
        specs.display["Разрешение"] = resolution
    matrix = _first(_MATRICES, text)
    if matrix:
        specs.display["Матрица"] = matrix
    rate = re.search(r"(\d{2,3})\s*(?:гц|hz)\b", text, re.IGNORECASE)
    if rate:
        specs.display["Частота экрана"] = "%s Гц" % rate.group(1)
    platform = _first(_PLATFORMS, text)
    if platform:
        specs.display["Smart-платформа"] = platform
    return specs


def product_name(titles: List[str], brands: List[str], specs: Specs) -> str:
    suffix = screen_label(int(specs.screen)) if specs.screen else ""
    return codes.product_name(KIND, titles, brands, suffix)
