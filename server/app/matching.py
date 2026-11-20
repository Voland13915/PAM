import re
from typing import List, Optional, Tuple

from . import tv
from .specs import Specs, size_label

_PREFIX = re.compile(
    r"^\s*(смартфон|smartphone|мобильный телефон|телефон|telefon mobil|игровой ноутбук|workstation|"
    r"ноутбук(?:\s+игровой)?|ультрабук|(?:laptop|notebook)(?:\s+(?:gaming|business))?)\s+",
    re.IGNORECASE,
)
_REFURBISHED = re.compile(r"\{\s*ref|\{\s*grade|refurb|восстановлен", re.IGNORECASE)
_BRACKETS = re.compile(r"\{[^}]*\}|\[[^\]]*\]")
_PART_NUMBER = re.compile(r"\(([A-Za-z0-9][A-Za-z0-9.\-#/]{5,})\)")
_MEMORY = re.compile(r"^(?:(\d{1,2})/)?(\d{1,4})(gb|tb)$|^(\d{1,2})/(\d{2,4})$")
_SAMSUNG_CODE = re.compile(r"^[a-z]\d{3}[a-z]?$")
_SAMSUNG_SM = re.compile(r"^sm-?[a-z]\d{3}[a-z0-9/]*$")
_CYRILLIC = re.compile(r"[а-яё]")

_DROP = {
    "xiaomi", "apple", "samsung", "5g", "4g", "lte", "nfc", "dual", "sim", "ds", "eu",
    "z", "zte",
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


_BRANDS = {
    "apple": "Apple", "samsung": "Samsung", "xiaomi": "Xiaomi", "poco": "Xiaomi",
    "redmi": "Xiaomi", "asus": "ASUS", "dell": "Dell", "hp": "HP", "lenovo": "Lenovo",
    "acer": "Acer", "msi": "MSI", "oppo": "OPPO", "motorola": "Motorola", "moto": "Motorola",
    "oneplus": "OnePlus", "honor": "Honor", "huawei": "Huawei", "nokia": "Nokia",
    "realme": "realme", "google": "Google", "nothing": "Nothing", "zte": "ZTE", "tcl": "TCL",
    "infinix": "Infinix", "tecno": "TECNO", "gigabyte": "Gigabyte", "microsoft": "Microsoft",
    "lg": "LG", "sony": "Sony", "vivo": "vivo", "allview": "Allview", "blackview": "Blackview",
    "ulefone": "Ulefone", "doogee": "Doogee", "fossibot": "FOSSiBOT", "cubot": "Cubot",
    "energizer": "Energizer", "prestigio": "Prestigio", "razer": "Razer", "gateway": "Gateway",
    "chuwi": "Chuwi", "machenike": "Machenike", "thunderobot": "Thunderobot",
    "iphone": "Apple", "ipad": "Apple", "macbook": "Apple", "galaxy": "Samsung",
    "hisense": "Hisense", "philips": "Philips", "kivi": "KIVI", "vesta": "Vesta",
    "blaupunkt": "Blaupunkt", "haier": "Haier", "sharp": "Sharp", "horizon": "Horizon",
    "diamant": "Diamant", "yandex": "Yandex", "toshiba": "Toshiba", "panasonic": "Panasonic",
    "thomson": "Thomson", "skyworth": "Skyworth", "ud": "UD", "nec": "NEC", "ozon": "Ozon",
}


_NOT_BRANDS = {
    "smartphone", "laptop", "notebook", "telefon", "mobil", "gaming", "business", "workstation",
    "ultrabook", "consumer", "smb", "televizor", "tv", "smart", "led", "qled", "oled", "hi-qled",
    "miniled", "mini", "micro", "rgb", "nanocell", "qned", "dled", "qd", "qd-miniled", "evo",
    "uhd", "neo",
}


def canonical_brand(word: str) -> str:
    word = word.strip(",.;:()")
    known = _BRANDS.get(word.lower())
    if known:
        return known
    return word[:1].upper() + word[1:] if word.islower() else word


def brand_from_title(title: str) -> str:
    for token in clean_title(title).split():
        word = token.strip(",.;:()\"'")
        if not word or _CYRILLIC.search(word.lower()) or not re.fullmatch(r"[A-Za-z][A-Za-z\-]*", word):
            continue
        if word.lower() in _NOT_BRANDS:
            continue
        return canonical_brand(word)
    return ""


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
    text = re.sub(r"\b(\d{1,2})gb/(\d)", r"\1/\2", text)
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


def _memory_word(word: str) -> str:
    lower = word.lower().replace("гб", "gb").replace("тб", "tb").strip(",")
    return re.sub(r"^(\d{1,2})gb/(\d)", r"\1/\2", lower)


def _storage(gb: int) -> str:
    return "%dtb" % (gb // 1024) if gb >= 1024 and gb % 1024 == 0 else "%dgb" % gb


_LOOKALIKES = str.maketrans("асеорхук", "aceopxyk")
_LOOKALIKE_TOKEN = re.compile(r"^(?=.*[a-z0-9])[a-z0-9асеорхук]+$")
_POCO_MODEL = re.compile(r"[cfmx]\d+[a-z]*")


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
    model = [_LOOKALIKE_TOKEN.sub(lambda m: m.group(0).translate(_LOOKALIKES), t) for t in model]
    model = ["motorola" if t == "moto" else t for t in model]
    model = [t for i, t in enumerate(model) if i == 0 or t != model[i - 1]]
    if "honor" in model:
        model = [t for t in model if t != "huawei"]
    model = [
        t for t in model
        if not _CYRILLIC.search(t)
        and t not in _DROP
        and t not in _COLORS
        and t.strip('"\'') != ""
        and not _SAMSUNG_SM.match(t)
        and not (samsung and _SAMSUNG_CODE.match(t))
    ]
    if samsung and model and model[0] != "galaxy":
        model = ["galaxy"] + [t for t in model if t != "galaxy"]
    if canonical_brand(brand) == "Xiaomi" and model and _POCO_MODEL.fullmatch(model[0]):
        model = ["poco"] + model
    return model, memory


_LAPTOP_CODE = re.compile(r"^(?=.*\d)(?=.*[a-z])[a-z0-9][a-z0-9\-_.]{4,}$")
_CODE_ONLY_BRANDS = {"asus", "dell", "acer"}


_DELL_SERIES = {"latitude", "vostro", "inspiron", "precision", "xps"}
_GEN_BRANDS = {"lenovo", "hp"}
_GENERATION = re.compile(r"^(?:g|gen)(\d+[a-z]*)$")
_MAC_KINDS = {"air", "pro", "neo"}


def _laptop_tokens(title: str) -> List[str]:
    text = _BRACKETS.sub(" ", clean_title(title)).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[\"”″']", " ", text)
    text = re.sub(r"\bgen\s+(\d+)", r"gen\1", text)
    return [t.strip(",") for t in text.split() if t.strip(",")]


def _mac_model(tokens: List[str]) -> Optional[str]:
    if "macbook" not in tokens:
        return None
    rest = tokens[tokens.index("macbook") + 1:]
    kind = rest[0] if rest and rest[0] in _MAC_KINDS else ""
    size = next((t.split(".")[0].split(",")[0] for t in rest[:4]
                 if re.fullmatch(r"1[3-8](?:[.,]\d)?", t)), "")
    return " ".join(p for p in ("apple macbook", kind, size) if p)


def laptop_code(title: str, brand: str) -> Optional[str]:
    tokens = _laptop_tokens(title)
    brand_l = brand.lower()
    if brand_l == "apple" or "macbook" in tokens:
        return _mac_model(tokens)

    for index, token in enumerate(tokens[:-1]):
        if brand_l == "dell" and token in _DELL_SERIES and tokens[index + 1].isdigit():
            following = [t for t in tokens[index + 1:index + 3] if t.isdigit()]
            number = next((t for t in following if len(t) >= 4), following[0])
            return "dell %s %s" % (token, number)

    if brand_l in _GEN_BRANDS:
        start = tokens.index(brand_l) + 1 if brand_l in tokens else 0
        for index in range(start, len(tokens)):
            match = _GENERATION.match(tokens[index])
            if match and index > start:
                series = [t for t in tokens[start:index] if not _CYRILLIC.search(t)
                          and t not in _COLORS]
                if series:
                    return " ".join([brand_l] + series + ["gen" + match.group(1)])

    for index, token in enumerate(tokens):
        if _CYRILLIC.search(token) or not _LAPTOP_CODE.match(token):
            continue
        if re.match(r"^\d+(gb|tb)$|^\d+/\d+|^\d-in-\d$", token):
            continue
        code = token
        if brand_l == "asus":
            code = code.split("-")[0]
        elif brand_l == "acer":
            code = "-".join(code.split("-")[:2])
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


def match_parts(category: str, brand: str, title: str,
                details: str = "") -> Tuple[str, str, Optional[int]]:
    if category == tv.CATEGORY:
        key = tv.key(title, brand, details)
        return key, key, None
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
    if len(parts) < 3 or parts[1] in ("title", "code", "model"):
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


def match_key(category: str, brand: str, title: str, details: str = "") -> str:
    return match_parts(category, brand, title, details)[1]


def display_name(title: str) -> str:
    text = re.sub(r"(\d)\s+(gb|tb|гб|тб)\b", r"\1\2", _BRACKETS.sub(" ", clean_title(title)),
                  flags=re.IGNORECASE)
    text = re.sub(r"\brefurb\w*\.?", " ", text, flags=re.IGNORECASE)
    words = text.split()
    samsung = any(w.lower() in ("samsung", "galaxy") for w in words)
    kept: List[str] = []
    for word in words:
        lower = _memory_word(word)
        if _memory(lower) is not None:
            kept.append(lower.upper() if re.search(r"[a-z]", lower) else word.strip(","))
            break
        if _CYRILLIC.search(lower) or lower.strip(",") in _COLORS:
            continue
        if (samsung and _SAMSUNG_CODE.match(lower)) or _SAMSUNG_SM.match(lower):
            continue
        kept.append(word)
    name = " ".join(kept).strip(" ,")
    if is_refurbished(title):
        name += " (восстановленный)"
    return name or clean_title(title)


_CONFIG_TOKEN = re.compile(r"^\d+(gb|tb|гб|тб)?/\d+|^\d+c/\d+g$|^\d+(gb|tb|гб|тб)$|^(ram|ssd|windows)$")
_CPU_START = {"intel", "amd", "qualcomm", "ryzen"}


_NAME_END = re.compile(r"\s-\s|\s/|/(?=[a-z])|\b(?:wuxga|fhd|full\s*hd|qhd|procesor|cu)\b", re.IGNORECASE)
_NAME_INCH = re.compile(r"(?<![\w.,])\d{2}(?:[.,]\d{1,2})?\s*(?:''|\"|”|″)|(?<![\w.,])1[0-8][.,]\d(?![\w.,])")


def _laptop_base_name(title: str) -> str:
    text = re.sub(r"\([^)]*\)", " ", _BRACKETS.sub(" ", clean_title(title)))
    text = _NAME_END.split(text, 1)[0]
    if "macbook" not in text.lower():
        text = _NAME_INCH.sub(" ", text)
    text = re.sub(r"[\"”″]|''", " ", text).replace(",", " ")
    kept: List[str] = []
    for word in text.split():
        lower = word.lower()
        if _CONFIG_TOKEN.match(lower) or (kept and lower in _CPU_START):
            break
        if _CYRILLIC.search(lower) or lower in _COLORS:
            continue
        kept.append(word)
    digits = [i for i, w in enumerate(kept) if re.search(r"\d", w)]
    return " ".join(kept[:digits[-1] + 1] if digits else kept)


def _cpu_label(text: str) -> str:
    text = re.sub(r"\s*\(.*?\)|\s+with .*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(intel|amd|apple|qualcomm)\s+", "", text, flags=re.IGNORECASE)
    return re.sub(r"^core\s+(?=i\d)", "", text, flags=re.IGNORECASE)


def _phone_name(name: str, specs: Specs) -> str:
    words = name.split()
    lower = [w.lower() for w in words]
    if "samsung" in lower and "galaxy" not in lower:
        words.insert(lower.index("samsung") + 1, "Galaxy")
    apple = any(w.lower() in ("apple", "iphone") for w in words)
    for index, word in enumerate(words):
        memory = _memory(word.lower())
        if memory is None:
            continue
        ram, storage = memory
        if ram is None and specs.ram and not apple:
            unit = "%dTB" % (storage // 1024) if storage >= 1024 and storage % 1024 == 0 \
                else "%dGB" % storage
            words[index] = "%d/%s" % (specs.ram, unit)
        break
    return " ".join(words)


def _memory_before_colour(title: str) -> bool:
    words = [_memory_word(w) for w in
             re.sub(r"(\d)\s+(gb|tb|гб|тб)\b", r"\1\2", _BRACKETS.sub(" ", title),
                    flags=re.IGNORECASE).split()]
    positions = [i for i, w in enumerate(words) if _memory(w) is not None]
    return bool(positions) and positions[0] < len(words) - 1


def product_name(category: str, titles: List[str], specs: Specs,
                 brands: Optional[List[str]] = None) -> str:
    if category == tv.CATEGORY:
        return tv.product_name(titles, brands or [brand_from_title(t) for t in titles], specs)
    if category != "Ноутбуки":
        preferred = [t for t in titles if _memory_before_colour(t)]
        return _phone_name(display_name((preferred or titles)[0]), specs)
    names = [n for n in (_laptop_base_name(t) for t in titles) if n]
    votes: dict = {}
    for n in names:
        votes.setdefault(n.lower(), []).append(n)
    best = max(votes.values(), key=lambda v: (len(v), len(v[0].split()))) if votes else []
    name = best[0] if best else display_name(titles[0])
    config = []
    if specs.display.get("Процессор"):
        cpu = _cpu_label(specs.display["Процессор"])
        if cpu.lower() not in name.lower().split(" · ")[0]:
            config.append(cpu)
    if specs.ram and specs.storage:
        config.append("%s / %s" % (size_label(specs.ram), size_label(specs.storage)))
    elif specs.storage:
        config.append(size_label(specs.storage))
    if config:
        name += " · " + ", ".join(config)
    if any(is_refurbished(t) for t in titles):
        name += " (восстановленный)"
    return name
