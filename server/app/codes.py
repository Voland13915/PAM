import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, FrozenSet, Iterable, List, Optional, Tuple

_CODE = re.compile(r"^(?=.*\d)(?=.*[a-z])[a-z0-9][a-z0-9\-/.+]{3,}$")
_NOT_CODE = re.compile(
    r"^\d+(hz|гц|cm|см|w|вт|k|p|gb|kg|кг|l|л|pa|па|mah|мач)$|^\d+x\d+$|^(19|20)\d\d$|"
    r"^hdr\d*\+?$|^dvb|^wi-?fi|^ci\+?$|^hdmi|^usb|^bt\d|^\d(\.\d)?$"
)
_SUFFIXES = {"pro", "se", "plus", "max"}
_SAMSUNG_REGION = re.compile(r"(?<=[a-z0-9])[uet]x[a-z]{0,2}$")
_LG_OLED = re.compile(r"^\d{2,3}[a-z]\d(?=[a-z0-9]{2,4}$)")
_LG_LED = re.compile(r"^(\d{2,3}[a-z]+)(\d{2,5})([a-z]?)")
_YEAR = re.compile(r"^(19|20)\d\d$")
_CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)
COLORS = frozenset({
    "black", "white", "grey", "gray", "silver", "dark", "titan", "blue", "red", "green", "gold",
    "pink", "beige", "inox", "steel", "stainless", "graphite", "champagne", "cream", "brown",
    "obsidian", "nordic", "lotus", "brilliant", "terra", "midnight", "yellow", "orange",
    "purple", "violet", "white/blue", "black/blue", "copper", "nickel", "iron", "sage",
})


@dataclass(frozen=True)
class Kind:
    category: str
    filler: FrozenSet[str] = COLORS
    head: Optional[str] = None
    min_code: int = 4
    join_split_codes: bool = False
    extra: Optional[Callable[[str, str, str], Optional[str]]] = None
    name_word: str = ""
    noise: Optional[str] = None
    strip: Optional[str] = None
    compact: bool = False
    suffixes: FrozenSet[str] = field(default_factory=lambda: frozenset(_SUFFIXES))


def head(kind: Kind, title: str) -> str:
    if kind.strip:
        title = re.sub(kind.strip, " ", title, flags=re.IGNORECASE)
    text = re.split(r",|\(", title, maxsplit=1)[0]
    if kind.head:
        match = re.search(kind.head, text, re.IGNORECASE)
        if match:
            return text[match.end():]
    return text


def tokens(kind: Kind, title: str) -> List[Tuple[str, str]]:
    result = []
    for raw in head(kind, title).split():
        word = raw.strip(",.;:\"'″”")
        if word and not (kind.noise and re.match(kind.noise, word.lower())):
            result.append((word, word.lower()))
    return result


def after_brand(items: List[Tuple[str, str]], brand: str) -> List[Tuple[str, str]]:
    brand_l = brand.lower()
    for index, (_, lower) in enumerate(items):
        if lower == brand_l:
            return items[index + 1:]
    return items


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


def _is_code(kind: Kind, lower: str) -> bool:
    if _CYRILLIC.search(lower) or not _CODE.match(lower) or _NOT_CODE.match(lower):
        return False
    plain = re.sub(r"[^a-z0-9]", "", lower.split("/")[0])
    digits = len(re.findall(r"\d", plain))
    if kind.compact and digits == 1 and len(plain) >= 7 and re.search(r"[a-z].*\d.*[a-z]", plain):
        return True
    return digits >= 2 and len(plain) >= kind.min_code


def _joined(kind: Kind, items: List[Tuple[str, str]], index: int) -> Optional[Tuple[str, str, int]]:
    word, lower = items[index]
    if not re.fullmatch(r"[a-z0-9]{1,6}", lower):
        return None
    following = items[index + 1][1] if index + 1 < len(items) else ""
    if not re.search(r"\d", lower) and not (
            (len(lower) <= 4 and re.fullmatch(r"\d{3,}", following))
            or re.fullmatch(r"\d{4}", following)):
        return None
    if re.search(r"\d", lower) and len(lower) > 5:
        return None
    words, joined, used = [word], lower, 1
    while index + used < len(items):
        nxt_word, nxt = items[index + used]
        digits = re.fullmatch(r"\d{2,}", nxt) or (
            re.fullmatch(r"[a-z0-9]{1,6}", nxt) and re.search(r"\d", nxt))
        letters = re.fullmatch(r"[a-z]{1,3}", nxt) and joined[-1].isdigit() \
            and nxt not in kind.suffixes and nxt not in kind.filler
        if not (digits or letters):
            break
        words.append(nxt_word)
        joined += nxt
        used += 1
    if used == 1:
        return None
    return " ".join(words), joined, used


def _candidates(kind: Kind, items: List[Tuple[str, str]]) -> List[Tuple[int, str, str, int]]:
    result = []
    for index, (word, lower) in enumerate(items):
        if kind.join_split_codes:
            joined = _joined(kind, items, index)
            if joined and _is_code(kind, joined[1]):
                result.append((index, joined[0], joined[1], joined[2]))
                continue
        result.append((index, word, lower, 1))
    return result


def code(kind: Kind, title: str, brand: str) -> Optional[Tuple[str, str]]:
    items = after_brand(tokens(kind, title), brand)
    for index, word, lower, used in _candidates(kind, items):
        if not _is_code(kind, lower):
            continue
        key = re.sub(r"-", "", lower.split("/")[0])
        shown = word.split("/")[0]
        if brand.lower() == "lg" and re.match(r"oled\d", key):
            key = key[4:]
        key = _core(brand.lower(), key)
        following = items[index + used][1] if index + used < len(items) else ""
        if following in kind.suffixes:
            key += " " + following
            shown += " " + following.capitalize()
        return key, shown
    return None


def model_words(kind: Kind, title: str, brand: str) -> List[Tuple[str, str]]:
    words = []
    for word, lower in after_brand(tokens(kind, title), brand):
        if kind.compact and lower == "plus":
            word, lower = "Plus", "+"
        if _CYRILLIC.search(lower) or lower in kind.filler or lower == brand.lower():
            continue
        if kind.compact and lower == "+":
            words.append((word, lower))
            continue
        if kind.extra and lower.isdigit() and not _YEAR.match(lower):
            continue
        if not re.fullmatch(r"[a-z0-9\-+/.]+", lower) or not re.search(r"[a-z0-9]", lower):
            continue
        words.append((word, lower))
    return words


def key(kind: Kind, title: str, brand: str, details: str = "") -> str:
    brand_l = brand.lower()
    found = code(kind, title, brand)
    if found:
        return "%s|code|%s %s" % (kind.category, brand_l, found[0])
    words = [lower for _, lower in model_words(kind, title, brand)]
    if not words:
        plain = re.sub(r"[^0-9a-zа-яё]+", " ", title.lower()).strip()
        return "%s|title|%s" % (kind.category, plain)
    extra = kind.extra(title, details, brand) if kind.extra else "-"
    joined = "".join(words) if kind.compact else " ".join(words)
    return "%s|model|%s %s|%s" % (kind.category, brand_l, joined, extra or "?")


def _longer_codes(base: str, bases: Iterable[str]) -> List[str]:
    brand, _, value = base.split("|")[2].partition(" ")
    category = base.split("|")[0]
    found = set()
    for other in bases:
        other_parts = other.split("|")
        if len(other_parts) != 3 or other_parts[1] != "code" or other_parts[0] != category:
            continue
        other_brand, _, other_value = other_parts[2].partition(" ")
        rest = other_value[len(value):]
        if other_brand != brand or not other_value.startswith(value) or not rest or " " in rest:
            continue
        region = category != "Телевизоры" and re.fullmatch(r"[a-z]{2,3}", rest)
        if brand in ("lg", "samsung") or region or (len(rest) >= 2 and re.search(r"\d", rest)):
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
        if len(other_parts) != 4 or other_parts[1] != "model" or other_parts[3] != parts[3] \
                or other_parts[0] != parts[0]:
            continue
        other_words = other_parts[2].split()
        if [w for w in other_words if not _YEAR.match(w)] == words and other != base:
            found.add(other)
    return sorted(found) if len(found) == 1 else []


def product_name(kind: Kind, titles: List[str], brands: List[str], suffix: str = "") -> str:
    names = []
    for title, brand in zip(titles, brands):
        found = code(kind, title, brand)
        if found:
            names.append("%s %s" % (brand, found[1]))
    if names:
        counts = Counter(n.lower() for n in names)
        return max(names, key=lambda n: counts[n.lower()])
    candidates = [(model_words(kind, t, b), t, b) for t, b in zip(titles, brands)]
    words, _, brand = max(candidates, key=lambda c: len(c[0]))
    if not words:
        return head(kind, titles[0]).strip()
    shown = [w if not w.islower() else (w.upper() if len(w) == 1 else w.capitalize())
             for w, _ in words]
    prefix = [brand]
    if kind.name_word and not any(kind.name_word.lower() in lower for _, lower in words):
        prefix.append(kind.name_word)
    name = " ".join(prefix + shown)
    if suffix:
        name += " " + suffix
    return name.strip()
