import re
from typing import List, Optional, Tuple

_PREFIX = re.compile(
    r"^\s*(смартфон|smartphone|мобильный телефон|telefon mobil|игровой ноутбук|"
    r"ноутбук|ультрабук|laptop|notebook)\s+",
    re.IGNORECASE,
)
_REFURBISHED = re.compile(r"\{\s*ref|\{\s*grade|refurb|восстановлен", re.IGNORECASE)
_BRACKETS = re.compile(r"\{[^}]*\}|\[[^\]]*\]")
_PART_NUMBER = re.compile(r"\(([A-Za-z0-9][A-Za-z0-9.\-#/]{5,})\)")
_MEMORY = re.compile(r"^(?:(\d{1,2})/)?(\d{1,4})(gb|tb)$|^(\d{1,2})/(\d{2,4})$")
_SAMSUNG_CODE = re.compile(r"^[a-z]\d{3}[a-z]?$")
_CYRILLIC = re.compile(r"[а-яё]")

_DROP = {
    "xiaomi", "apple", "samsung", "5g", "4g", "lte", "nfc", "dual", "sim", "ds", "eu",
    "z", "moto",
}
PROTECTED = {
    "pro", "max", "plus", "ultra", "fe", "fs", "f", "lite", "mini", "power", "fusion",
    "neo", "edge", "prime", "note", "slim", "air", "s", "c", "x", "t", "a", "flip", "fold",
    "go", "play", "turbo", "explorer", "racing", "classic", "duo", "core", "se",
    "edition", "gt", "xl", "e", "i", "r", "ai",
}
_COLORS = {
    "black", "white", "blue", "green", "red", "pink", "purple", "gold", "silver",
    "gray", "grey", "graphite", "midnight", "starlight", "titanium", "titan", "natural",
    "desert", "teal", "ultramarine", "glacier", "sky", "night", "star", "mint",
    "lavender", "yellow", "orange", "cream", "ice", "ocean", "violet", "navy", "jet",
    "shadow", "awesome", "graygreen", "olive", "umber", "luna", "arctic", "space",
    "deep", "cosmic", "light", "dark", "rose", "coral", "sage", "plum", "copper",
    "bronze", "beige", "brown", "lime", "aqua", "cyan", "frost", "pearl", "onyx",
    "obsidian", "porcelain", "hazel", "iceblue", "icyblue", "silverblue", "midnightblack",
}


def clean_title(title: str) -> str:
    return _PREFIX.sub("", title).strip()


def is_refurbished(title: str) -> bool:
    return bool(_REFURBISHED.search(title))


def part_number(title: str) -> Optional[str]:
    match = _PART_NUMBER.search(title)
    if match is None:
        return None
    value = match.group(1).lower()
    return value if re.search(r"\d", value) and re.search(r"[a-z]", value) else None


def _normalize(title: str) -> str:
    text = _BRACKETS.sub(" ", clean_title(title)).lower()
    text = re.sub(r"[\"”″']", " ", text)
    text = text.replace("гб", "gb").replace("тб", "tb")
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"(\d)\s+(gb|tb)\b", r"\1\2", text)
    text = re.sub(r"\+", " plus ", text)
    text = re.sub(r"\b(flip|fold|xcover)(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)(pro|plus|fe|fs|ultra|lite|max|mini|power)\b", r"\1 \2", text)
    text = re.sub(r"\bpro\s*plus\b", "pro plus", text)
    text = re.sub(r"\bproplus\b", "pro plus", text)
    return text


def _memory(token: str) -> Optional[Tuple[Optional[int], int]]:
    match = _MEMORY.match(token)
    if match is None:
        return None
    if match.group(2) is not None:
        ram, storage, unit = match.group(1), int(match.group(2)), match.group(3)
        if unit == "tb":
            storage *= 1024
        if storage < 32:
            return None
    else:
        ram, storage = match.group(4), int(match.group(5))
    return (int(ram) if ram else None), storage


def _storage(gb: int) -> str:
    return "%dtb" % (gb // 1024) if gb >= 1024 and gb % 1024 == 0 else "%dgb" % gb


def model_and_memory(title: str, brand: str = "") -> Tuple[List[str], Optional[Tuple[Optional[int], int]]]:
    tokens = [t for t in re.split(r"[\s,()]+", _normalize(title)) if t]
    memory = None
    model: List[str] = []
    for token in tokens:
        found = _memory(token)
        if found is not None:
            memory = found
            break
        model.append(token)
    samsung = brand.lower() == "samsung" or "galaxy" in model
    model = [
        t for t in model
        if not _CYRILLIC.search(t)
        and t not in _DROP
        and t not in _COLORS
        and t.strip('"\'') != ""
        and not (samsung and _SAMSUNG_CODE.match(t))
    ]
    if samsung and model and model[0] != "galaxy":
        model = ["galaxy"] + [t for t in model if t != "galaxy"]
    return model, memory


_LAPTOP_CODE = re.compile(r"^(?=.*\d)(?=.*[a-z])[a-z0-9][a-z0-9\-_.]{4,}$")
_CODE_ONLY_BRANDS = {"asus", "dell"}


def laptop_code(title: str, brand: str) -> Optional[str]:
    text = _BRACKETS.sub(" ", clean_title(title)).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    tokens = [t.strip(",") for t in text.split()]
    brand_l = brand.lower()
    if brand_l == "apple" or "macbook" in tokens:
        return None
    for index, token in enumerate(tokens):
        if _CYRILLIC.search(token) or not _LAPTOP_CODE.match(token):
            continue
        if re.match(r"^\d+(gb|tb)$|^\d+/\d+", token):
            continue
        code = token
        if brand_l == "asus":
            code = code.split("-")[0]
        code = code.split("_")[0]
        if len(code) < 5:
            continue
        if brand_l in _CODE_ONLY_BRANDS:
            return "%s %s" % (brand_l, code)
        series = [t for t in tokens[:index] if t != brand_l and not _CYRILLIC.search(t)]
        return " ".join([brand_l] + series + [code])
    return None


def _key(category: str, model: List[str], memory_part: str, refurbished: str) -> str:
    return "%s|%s|%s%s" % (category, " ".join(model), memory_part, refurbished)


def match_parts(category: str, brand: str, title: str) -> Tuple[str, str, Optional[int]]:
    refurbished = "|ref" if is_refurbished(title) else ""
    if category == "Ноутбуки":
        code = laptop_code(title, brand)
        if code:
            key = "%s|code|%s%s" % (category, code, refurbished)
            return key, key, None

    model, memory = model_and_memory(title, brand)
    if not model:
        words = re.sub(r"[^0-9a-zа-яё]+", " ", clean_title(title).lower()).strip()
        key = "%s|title|%s" % (category, words)
        return key, key, None
    if memory is None:
        key = _key(category, model, "?", refurbished)
        return key, key, None

    ram, storage = memory
    apple = brand.lower() == "apple" or model[0] in ("iphone", "macbook", "ipad")
    if apple and category == "Смартфоны":
        ram = None
    base = _key(category, model, _storage(storage), refurbished)
    if ram is None:
        return base, base, None
    return base, _key(category, model, "%d/%s" % (ram, _storage(storage)), refurbished), ram


def trimmed_keys(key: str) -> List[str]:
    parts = key.split("|")
    if len(parts) < 3 or parts[1] in ("title", "code"):
        return []
    model = parts[1].split()
    result = []
    for cut in range(1, 4):
        removed, kept = model[-cut:], model[:-cut]
        if len(kept) < 1 or not any(re.search(r"\d", t) for t in kept):
            break
        if any(re.search(r"\d", t) or t in PROTECTED for t in removed):
            break
        result.append("|".join([parts[0], " ".join(kept)] + parts[2:]))
    return result


def match_key(category: str, brand: str, title: str) -> str:
    return match_parts(category, brand, title)[1]


def display_name(title: str) -> str:
    text = re.sub(r"(\d)\s+(gb|tb|гб|тб)\b", r"\1\2", _BRACKETS.sub(" ", clean_title(title)),
                  flags=re.IGNORECASE)
    text = re.sub(r"\brefurb\w*\.?", " ", text, flags=re.IGNORECASE)
    words = text.split()
    kept: List[str] = []
    for word in words:
        lower = word.lower().replace("гб", "gb").replace("тб", "tb")
        if _memory(lower) is not None:
            kept.append(word)
            break
        if _CYRILLIC.search(lower) or lower.strip(",") in _COLORS:
            continue
        kept.append(word)
    name = " ".join(kept).strip(" ,")
    if is_refurbished(title):
        name += " (восстановленный)"
    return name or clean_title(title)
