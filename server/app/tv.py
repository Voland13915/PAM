import re
from collections import Counter
from typing import Iterable, List, Optional, Tuple

from .specs import Specs, screen_label

CATEGORY = "Телевизоры"

_INCH = re.compile(r"(?<![\d.,])(\d{2,3})(?:[.,]\d)?\s*(?:\"|″|”|''|дюйм|inch)", re.IGNORECASE)
_CODE = re.compile(r"^(?=.*\d)(?=.*[a-z])[a-z0-9][a-z0-9\-/.+]{3,}$")
_NOT_CODE = re.compile(
    r"^\d+(hz|гц|cm|см|w|вт|k|p|gb)$|^\d+x\d+$|^(19|20)\d\d$|^hdr\d*\+?$|^dvb|^wi-?fi|^ci\+?$|"
    r"^hdmi|^usb|^bt\d|^\d(\.\d)?$"
)
_SUFFIXES = {"pro", "se", "plus", "max"}
_CM = re.compile(r"(?<![\d.,])(\d{2,3})(?:[.,]\d)?\s*(?:cm|см)\b", re.IGNORECASE)
_SIZES = (19, 22, 24, 27, 32, 40, 42, 43, 48, 50, 55, 58, 60, 65, 70, 75, 77, 83, 85, 86, 98, 100,
          115, 116)
_SAMSUNG_REGION = re.compile(r"(?<=[a-z0-9])[uet]x[a-z]{0,2}$")
_LG_OLED = re.compile(r"^\d{2,3}[a-z]\d(?=[a-z0-9]{2,4}$)")
_LG_LED = re.compile(r"^(\d{2,3}[a-z]+)(\d{2,5})([a-z]?)")
_YEAR = re.compile(r"^(19|20)\d\d$")
_FILLER = {
    "tv", "smart", "led", "qled", "oled", "miniled", "mini", "micro", "rgb", "qd", "4k", "8k",
    "uhd", "hd", "ultra", "full", "ready", "google", "android", "televizor", "hdr", "wifi",
    "wi-fi", "black", "white", "grey", "gray", "silver", "dark", "titan", "evo", "neo",
    "nanocell", "qned", "hi-qled", "dled", "by",
}
_CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)

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


def _head(title: str) -> str:
    text = re.split(r",|\(", title, maxsplit=1)[0]
    match = re.search(r"телевизор|televizor", text, re.IGNORECASE)
    return text[match.end():] if match else text


def _tokens(title: str) -> List[Tuple[str, str]]:
    result = []
    for raw in _head(title).split():
        word = raw.strip(",.;:\"'″”")
        if word:
            result.append((word, word.lower()))
    return result


def _after_brand(tokens: List[Tuple[str, str]], brand: str) -> List[Tuple[str, str]]:
    brand_l = brand.lower()
    for index, (_, lower) in enumerate(tokens):
        if lower == brand_l:
            return tokens[index + 1:]
    return tokens


def _core(brand: str, value: str) -> str:
    if brand == "samsung":
        return _SAMSUNG_REGION.sub("", value)
    if brand == "lg":
        match = _LG_OLED.match(value)
        if match:
            return match.group(0)
        match = _LG_LED.match(value)
        if match:
            digits = match.group(2)
            if len(digits) == 5:
                return match.group(1) + digits[:4]
            return match.group(1) + digits + match.group(3)
    return value


def code(title: str, brand: str) -> Optional[Tuple[str, str]]:
    tokens = _after_brand(_tokens(title), brand)
    for index, (word, lower) in enumerate(tokens):
        if _CYRILLIC.search(lower) or not _CODE.match(lower) or _NOT_CODE.match(lower):
            continue
        if len(re.findall(r"\d", lower)) < 2:
            continue
        key = lower.split("/")[0]
        shown = word.split("/")[0]
        if brand.lower() == "lg" and re.match(r"oled\d", key):
            key = key[4:]
        key = _core(brand.lower(), key)
        following = tokens[index + 1][1] if index + 1 < len(tokens) else ""
        if following in _SUFFIXES:
            key += " " + following
            shown += " " + following.capitalize()
        return key, shown
    return None


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
    for _, lower in _after_brand(_tokens(title), brand):
        if lower.isdigit() and int(lower) in _SIZES:
            return int(lower)
    match = _CM.search("%s %s" % (title, details or ""))
    if match:
        inches = int(match.group(1)) / 2.54
        return min(_SIZES, key=lambda size: abs(size - inches))
    return None


def _model_words(title: str, brand: str) -> List[Tuple[str, str]]:
    words = []
    for word, lower in _after_brand(_tokens(title), brand):
        if _CYRILLIC.search(lower) or lower in _FILLER or lower == brand.lower():
            continue
        if lower.isdigit() and not _YEAR.match(lower):
            continue
        if not re.fullmatch(r"[a-z0-9\-+]+", lower):
            continue
        words.append((word, lower))
    return words


def key(title: str, brand: str, details: str = "") -> str:
    brand_l = brand.lower()
    found = code(title, brand)
    if found:
        return "%s|code|%s %s" % (CATEGORY, brand_l, found[0])
    inches = diagonal(title, details, brand)
    words = [lower for _, lower in _model_words(title, brand)]
    if not words:
        plain = re.sub(r"[^0-9a-zа-яё]+", " ", title.lower()).strip()
        return "%s|title|%s" % (CATEGORY, plain)
    return "%s|model|%s|%s" % (CATEGORY, " ".join([brand_l] + words), inches or "?")


def _longer_codes(base: str, bases: Iterable[str]) -> List[str]:
    brand, _, value = base.split("|")[2].partition(" ")
    found = set()
    for other in bases:
        other_parts = other.split("|")
        if len(other_parts) != 3 or other_parts[1] != "code":
            continue
        other_brand, _, other_value = other_parts[2].partition(" ")
        rest = other_value[len(value):]
        if other_brand != brand or not other_value.startswith(value) or not rest or " " in rest:
            continue
        if brand in ("lg", "samsung") or (len(rest) >= 2 and re.search(r"\d", rest)):
            found.add(other)
    return sorted(found) if len(found) == 1 else []


def aliases(base: str, bases: Iterable[str]) -> List[str]:
    parts = base.split("|")
    if len(parts) == 3 and parts[1] == "code" and len(parts[2].partition(" ")[2]) >= 4:
        return _longer_codes(base, bases)
    if len(parts) != 4 or parts[1] != "model":
        return []
    words = parts[2].split()
    if any(_YEAR.match(w) for w in words):
        return []
    found = set()
    for other in bases:
        other_parts = other.split("|")
        if len(other_parts) != 4 or other_parts[1] != "model" or other_parts[3] != parts[3]:
            continue
        other_words = other_parts[2].split()
        if [w for w in other_words if not _YEAR.match(w)] == words and other != base:
            found.add(other)
    return sorted(found) if len(found) == 1 else []


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
    names = []
    for title, brand in zip(titles, brands):
        found = code(title, brand)
        if found:
            names.append("%s %s" % (brand, found[1]))
    if names:
        counts = Counter(n.lower() for n in names)
        return max(names, key=lambda n: counts[n.lower()])
    candidates = [(_model_words(t, b), t, b) for t, b in zip(titles, brands)]
    words, title, brand = max(candidates, key=lambda c: len(c[0]))
    if not words:
        return _head(titles[0]).strip()
    shown = [w if not w.islower() else (w.upper() if len(w) == 1 else w.capitalize())
             for w, _ in words]
    prefix = [brand] if any("tv" in lower for _, lower in words) else [brand, "TV"]
    name = " ".join(prefix + shown)
    if specs.screen:
        name += " " + screen_label(int(specs.screen))
    return name.strip()
