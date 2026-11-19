import re
from typing import List, Optional, Tuple

_TRADEMARKS = re.compile(r"[®™©]")
_SCREEN = re.compile(
    r"(?<![\d.,])(1[0-8](?:[.,]\d{1,2})?)\s*(?:\"|''|”|″|“|-?inch\b|дюйм)", re.IGNORECASE
)
_GPU = re.compile(
    r"(?:nvidia\s*)?(?:geforce\s*)?(?:rtx|gtx)\s*a?\d{3,4}(?:\s*ti)?(?:\s*super)?"
    r"(?:\s*(?:laptop\s*gpu|max-q))?"
    r"|(?:amd\s*)?radeon\s*rx\s*\d{3,4}\w*"
    r"|intel\s*arc\s*a\d{3}\w*",
    re.IGNORECASE,
)
_VRAM = re.compile(r"\d+\s*(?:gb|гб)\s*(?:gddr\d\w*|vram)", re.IGNORECASE)
_SIZE = r"(\d+(?:\.\d+)?)\s*(gb|tb|гб|тб)"
_PAIR = re.compile(
    r"(?<![\d.])(\d{1,3})(?:\s*(?:gb|гб)\s*/\s*|/)" + _SIZE + r"(?![a-zа-я])", re.IGNORECASE
)
_RAM = re.compile(
    r"(?<![\d.])(\d{1,3})\s*(?:gb|гб)\s*(?:(?:(?:lp)?ddr\d\w*\s*)?(?:ram|озу|оперативн)|(?:lp)?ddr\d)"
    r"|(?:ram|озу)\s*:?\s*(\d{1,3})\s*(?:gb|гб)",
    re.IGNORECASE,
)
_STORAGE = re.compile(
    r"(?<![\d.])" + _SIZE + r"\s*(?:pcie\s*)?(?:nvme\s*)?(?:m\.2\s*)?(?:ssd|emmc|ufs|hdd)"
    r"|(?:ssd|emmc)\s*:?\s*" + _SIZE,
    re.IGNORECASE,
)
_LOOSE_SIZE = re.compile(r"(?<![\d.])" + _SIZE + r"(?![a-zа-я])", re.IGNORECASE)

_CPU_PATTERNS = [
    r"(?:intel\s*)?core\s*ultra\s*[3579]\s*\d{3}[a-z]{0,2}\b",
    r"\bultra\s*[3579]\s*\d{3}[a-z]{0,2}\b",
    r"(?:intel\s*)?(?:core\s*)?\bi[3579][\s-]*\d{4,5}(?:[a-z]{1,3}\d?)?\b",
    r"(?:intel\s*)?core\s*[3579]\s*\d{3}[a-z]{0,2}\b",
    r"(?:amd\s*)?ryzen\s*(?:ai\s*)?(?:max\+?\s*)?(?:pro\s*)?\d\s*(?:pro\s*)?(?:hx\s*)?\d{3,4}[a-z]{0,3}\b",
    r"(?:qualcomm\s*)?snapdragon[\w\s-]{0,30}?x1[a-z]?-\d{2}-\d{3}"
    r"|(?:qualcomm\s*)?snapdragon\s*x\s*(?:elite|plus)?",
    r"\b(?:apple\s*)?m[1-6](?:\s*(?:pro|max|ultra))?\b(?:\s*\(?\s*\d+\s*c(?:pu)?\s*/\s*\d+\s*g(?:pu)?\s*\)?)?",
    r"\b(?:apple\s*)?a1[7-9]\s*pro\b(?:\s*\(?\s*\d+\s*c(?:pu)?\s*/\s*\d+\s*g(?:pu)?\s*\)?)?",
    r"(?:intel\s*)?(?:celeron|pentium)\s*(?:silver\s*|gold\s*)?n?\d{3,4}\w*",
    r"(?:intel\s*)?\bn[12]\d{2}\b",
    r"mediatek\s*kompanio\s*\d+\w*",
]
_CPU = [re.compile(p, re.IGNORECASE) for p in _CPU_PATTERNS]


def clean(text: str) -> str:
    text = _TRADEMARKS.sub("", text or "")
    text = re.sub(r"intel\s*core", "Intel Core", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def _gigabytes(value: str, unit: str) -> int:
    number = float(value.replace(",", "."))
    if unit.lower() in ("tb", "тб"):
        return int(round(number * 1024))
    if number >= 900:
        return int(round(number / 1000.0)) * 1024
    return int(round(number))


def size_text(gb: int) -> str:
    return "%d ТБ" % (gb // 1024) if gb >= 1024 and gb % 1024 == 0 else "%d ГБ" % gb


def screen(text: str) -> Optional[str]:
    match = _SCREEN.search(clean(text))
    return match.group(1).replace(",", ".") + '"' if match else None


def cpu(text: str) -> Optional[str]:
    text = clean(text)
    best = None
    for pattern in _CPU:
        match = pattern.search(text)
        if match is None:
            continue
        if best is None or match.start() < best.start() or \
                (match.start() == best.start() and match.end() > best.end()):
            best = match
    if best is None:
        return None
    label = " ".join(best.group(0).strip(" ,(-").split())
    if re.match(r"(i[3579]\b|ultra\b)", label, re.IGNORECASE):
        label = "Intel Core " + label
    elif re.match(r"n\d", label, re.IGNORECASE):
        label = "Intel " + label
    return label


_INCH_ANY = re.compile(r"(?<![\d.,])\d{2}(?:[.,]\d{1,2})?\s*(?:''|\"|”|″|“|-?\s*inch\b|дюйм\w*)",
                       re.IGNORECASE)
_BARE_SCREEN = re.compile(r"(?<![\w.,])1[0-8][.,]\d(?![\w.,])")
_GAMING_INCH = re.compile(r"\bgaming\s+(?=\d{2}(?:[.,]\d)?\s*(?:''|\"|”))", re.IGNORECASE)
_MODEL_END = re.compile(
    r"\s(?:cu\s+)?procesor\b|,|/|\(|\s\d{1,3}\s*(?:gb|tb|гб|тб)?\s*/\s*\d"
    r"|\s\d+\s*(?:gb|tb|гб|тб)\b|\b(?:fhd|wuxga|full\s*hd|qhd|uhd|2\.8k|3k)\b",
    re.IGNORECASE,
)


def cpu_start(text: str) -> Optional[int]:
    starts = [m.start() for m in (p.search(text) for p in _CPU) if m is not None]
    return min(starts) if starts else None


def model_part(title: str) -> str:
    text = _GAMING_INCH.sub("", clean(title))
    if "macbook" not in text.lower():
        text = _BARE_SCREEN.sub(" ", _INCH_ANY.sub(" ", text))
    cuts = [m.start() for m in [_MODEL_END.search(text)] if m is not None]
    start = cpu_start(text)
    if start is not None and start > 0:
        cuts.append(start)
    model = text[:min(cuts)] if cuts else text
    return " ".join(model.split()).strip(" -")


def gpu(text: str) -> Optional[str]:
    match = _GPU.search(clean(text))
    return " ".join(match.group(0).split()) if match else None


def _pairs(text: str, max_ram: int, min_storage: int) -> Optional[Tuple[int, int]]:
    position = 0
    while True:
        match = _PAIR.search(text, position)
        if match is None:
            return None
        ram = int(match.group(1))
        storage = _gigabytes(match.group(2), match.group(3))
        if ram <= max_ram and storage >= min_storage:
            return ram, storage
        position = match.start() + 1


def memory(text: str) -> Tuple[Optional[int], Optional[int]]:
    text = _VRAM.sub(" ", _GPU.sub(" GPU ", clean(text)))
    pair = _pairs(text, 128, 64)
    if pair is not None:
        return pair

    ram = storage = None
    taken = []
    labeled = _RAM.search(text)
    if labeled:
        ram = int(labeled.group(1) or labeled.group(2))
        taken.append(labeled.span())
    labeled = _STORAGE.search(text)
    if labeled:
        value, unit = (labeled.group(1), labeled.group(2)) if labeled.group(1) \
            else (labeled.group(3), labeled.group(4))
        storage = _gigabytes(value, unit)
        taken.append(labeled.span())

    for match in _LOOSE_SIZE.finditer(text):
        if any(start <= match.start() < end for start, end in taken):
            continue
        if text[max(0, match.start() - 6):match.start()].strip().endswith("GPU"):
            continue
        size = _gigabytes(match.group(1), match.group(2))
        if size <= 64 and ram is None:
            ram = size
        elif size >= 128 and storage is None:
            storage = size
    return ram, storage


def laptop_details(text: str) -> str:
    parts: List[str] = []
    found_screen = screen(text)
    if found_screen:
        parts.append(found_screen)
    ram, storage = memory(text)
    if ram is not None and storage is not None:
        parts += [size_text(ram), size_text(storage)]
    elif storage is not None:
        parts.append(size_text(storage))
    found_cpu = cpu(text)
    if found_cpu:
        parts.append(found_cpu)
    found_gpu = gpu(text)
    if found_gpu:
        parts.append(found_gpu)
    return " | ".join(parts)


def phone_memory(text: str) -> Tuple[Optional[int], Optional[int]]:
    text = clean(text)
    pair = _pairs(text, 32, 16)
    if pair is not None:
        return pair
    sizes = [_gigabytes(v, u) for v, u in re.findall(_SIZE, text, flags=re.IGNORECASE)]
    if len(sizes) >= 2 and sizes[0] <= 32 < sizes[1]:
        return sizes[0], sizes[1]
    big = [s for s in sizes if s >= 32]
    return None, (big[0] if big else None)


def storage_token(gb: int) -> str:
    return "%dTB" % (gb // 1024) if gb >= 1024 and gb % 1024 == 0 else "%dGB" % gb


def phone_title(name: str, attributes: str) -> str:
    ram, storage = phone_memory(attributes)
    if storage is None:
        return name
    memory = storage_token(storage) if ram is None else "%d/%s" % (ram, storage_token(storage))
    colour = attributes.split("/")[-1].strip() if attributes.count("/") >= 2 else ""
    if re.search(r"\d\s*(gb|tb|гб|тб)", colour, re.IGNORECASE):
        colour = ""
    return " ".join(p for p in (name, memory, colour) if p)
