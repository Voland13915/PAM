import re
from dataclasses import dataclass, field
from typing import Dict, Optional

_CPU_WORDS = re.compile(
    r"\b(intel|amd|ryzen|core|apple|qualcomm|snapdragon|celeron|pentium|athlon|mediatek|"
    r"dimensity|kirin|exynos|tensor|helio|unisoc|elite)\b|^(m\d|a\d{2})\b",
    re.IGNORECASE,
)
_GPU_WORDS = re.compile(r"\b(nvidia|geforce|rtx|gtx|radeon rx|arc a\d|mx\d{3})\b", re.IGNORECASE)
_PANELS = re.compile(r"^(ips|oled|amoled|tn|va|lcd|mini led|liquid retina( xdr)?)$", re.IGNORECASE)
_CPU_NOISE = {"intel", "amd", "apple", "qualcomm", "core", "processor", "processorul"}

DISPLAY_ORDER = [
    "Процессор", "Оперативная память", "Накопитель", "Экран", "Матрица", "Частота экрана",
    "Разрешение", "Smart-платформа", "Видеокарта", "Видеопамять", "Камера", "Аккумулятор",
]


@dataclass
class Specs:
    ram: Optional[int] = None
    storage: Optional[int] = None
    screen: Optional[float] = None
    cpu: Optional[str] = None
    display: Dict[str, str] = field(default_factory=dict)

    def known(self) -> int:
        return sum(v is not None for v in (self.ram, self.storage, self.screen, self.cpu))


def gigabytes(value: float, unit: str = "gb") -> int:
    unit = unit.lower()
    if unit in ("tb", "тб"):
        return int(round(value * 1024))
    if value >= 900:
        return int(round(value / 1000.0)) * 1024
    return int(round(value))


def size_label(gb: int) -> str:
    return "%d ТБ" % (gb // 1024) if gb >= 1024 and gb % 1024 == 0 else "%d ГБ" % gb


def _apple_cores(text: str) -> str:
    match = re.search(r"(\d+)\s*-?\s*core cpu.*?(\d+)\s*-?\s*core gpu", text) or \
        re.search(r"(\d+)\s*cpu\s*/\s*(\d+)\s*gpu", text) or \
        re.search(r"\b(\d+)c/(\d+)g\b", text)
    return " c%sg%s" % match.groups() if match else ""


_SNAPDRAGON_CODE = re.compile(r"x1[a-z]?-\d{2}-\d{3}")


def normalize_cpu(text: str) -> Optional[str]:
    text = text.lower()
    snapdragon = _SNAPDRAGON_CODE.search(text) if "snapdragon" in text else None
    if snapdragon:
        return "snapdragon " + snapdragon.group(0).replace("-", " ")
    cores = _apple_cores(text)
    text = text.split(" with ")[0]
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b\d+\s*c(?:pu)?\s*/\s*\d+\s*g(?:pu)?\b", " ", text)
    text = re.sub(r"[®™,]", " ", text).replace("-", " ")
    text = re.sub(r"\b(ultra|ryzen|core)(\d)", r"\1 \2", text)
    words: list = []
    for word in text.split():
        if word not in _CPU_NOISE and (not words or words[-1] != word):
            words.append(word)
    if not words:
        return None
    return " ".join(words) + cores


def _number(text: str) -> Optional[float]:
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    return float(match.group(0).replace(",", ".")) if match else None


def screen_label(inches: float) -> str:
    return ('%.1f"' % inches).replace('.0"', '"')


def _from_pairs(details: str, specs: Specs) -> None:
    pairs = {}
    for part in details.split(" / "):
        if ": " in part:
            key, value = part.split(": ", 1)
            pairs[key.strip().lower()] = value.strip()

    for key, value in pairs.items():
        number = _number(value)
        if key.startswith("procesor") and value:
            specs.cpu = normalize_cpu(value)
            specs.display["Процессор"] = value
        elif key.startswith("memoria operativ") and number:
            specs.ram = gigabytes(number)
        elif key.startswith("capacitate ssd") and number:
            specs.storage = gigabytes(number)
        elif key.startswith("ecran") and number:
            specs.screen = number
        elif key.startswith("rezolutie") and value:
            specs.display["Разрешение"] = value
        elif key.startswith("tehnologie") and value:
            specs.display["Матрица"] = value
        elif key.startswith("rezoluția foto") and number:
            specs.display["Камера"] = "%g Мп" % number
        elif key.startswith("capacitatea acumulatorului") and number:
            specs.display["Аккумулятор"] = "%d мА·ч" % number


def _from_segments(details: str, category: str, specs: Specs) -> None:
    sizes = []
    for segment in (s.strip() for s in details.split("|")):
        if not segment:
            continue
        ram_rom = re.fullmatch(r"(\d+)\s*ГБ\s*/\s*(\d+)\s*(ГБ|ТБ)", segment, re.IGNORECASE)
        size = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(ГБ|ТБ)", segment, re.IGNORECASE)
        if ram_rom:
            specs.ram = int(ram_rom.group(1))
            specs.storage = gigabytes(float(ram_rom.group(2)), ram_rom.group(3))
        elif re.fullmatch(r'\d+(?:[.,]\d+)?\s*"', segment):
            specs.screen = _number(segment)
        elif size:
            sizes.append(gigabytes(float(size.group(1).replace(",", ".")), size.group(2)))
        elif re.fullmatch(r"\d+\s*Гц", segment, re.IGNORECASE):
            specs.display["Частота экрана"] = segment
        elif "мА·ч" in segment or "мАч" in segment:
            specs.display["Аккумулятор"] = segment
        elif re.search(r"\b(гб|gb)\s+gddr", segment, re.IGNORECASE):
            specs.display["Видеопамять"] = segment
        elif _GPU_WORDS.search(segment):
            specs.display["Видеокарта"] = segment
        elif _PANELS.match(segment):
            specs.display["Матрица"] = segment
        elif _CPU_WORDS.search(segment):
            specs.cpu = normalize_cpu(segment)
            specs.display["Процессор"] = segment
        elif re.fullmatch(r"[a-z]?\d{2,5}[a-z]{0,3}\d?", segment, re.IGNORECASE) and specs.cpu is None:
            specs.cpu = segment.lower()

    if category == "Ноутбуки" and len(sizes) >= 2:
        specs.ram, specs.storage = sizes[0], sizes[1]
    elif sizes and specs.storage is None:
        specs.storage = sizes[0]


def parse_specs(category: str, details: str, memory=None, title: str = "", brand: str = "") -> Specs:
    if category == "Телевизоры":
        from . import tv
        return tv.parse_specs(title, details, brand)
    specs = Specs()
    details = (details or "").strip()
    if ": " in details and "|" not in details:
        _from_pairs(details, specs)
    elif details:
        _from_segments(details, category, specs)

    if specs.cpu and re.match(r"^(m\d|a\d{2})\b", specs.cpu) and not re.search(r" c\d+g\d+$", specs.cpu):
        specs.cpu += _apple_cores(title.lower())

    if memory is not None:
        ram, storage = memory
        if specs.ram is None and ram is not None:
            specs.ram = ram
        if specs.storage is None:
            specs.storage = storage

    if specs.ram is not None:
        specs.display["Оперативная память"] = size_label(specs.ram)
    if specs.storage is not None:
        specs.display["Накопитель"] = size_label(specs.storage)
    if specs.screen is not None:
        specs.display["Экран"] = screen_label(specs.screen)
    return specs
