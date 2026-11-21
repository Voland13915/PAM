import re
from typing import Callable, Dict, List, Optional

from . import codes
from .specs import Specs

WASHERS = "Стиральные машины"
FRIDGES = "Холодильники"
VACUUMS = "Пылесосы"
MICROWAVES = "Микроволновки"

_FILLER = codes.COLORS | {
    "eu", "smart", "wifi", "wi-fi", "nofrost", "no", "frost", "inverter", "sidebyside", "side",
    "by", "french", "door", "combi", "edition", "robot", "vacuum", "cleaner", "mi",
}

KINDS: Dict[str, codes.Kind] = {
    name: codes.Kind(name, filler=frozenset(_FILLER), min_code=5, join_split_codes=True,
                     noise=r"^bhr\d|^\d\.\d{3}-\d{3}\.\d|^\d{6}-\d{2}$", compact=True,
                     strip=r"\brm\s?\d{3}\b.*$|\bcadou\b.*$|чистящее средство.*$|\bdetergent\b.*$")
    for name in (WASHERS, FRIDGES, VACUUMS, MICROWAVES)
}
CATEGORIES = tuple(KINDS)

_OTHER_GOODS = {
    WASHERS: re.compile(r"^\s*сушильн|^\s*masin[aă] de uscat", re.IGNORECASE),
    FRIDGES: re.compile(
        r"винн|wine|для вина|r[aă]citor de vin|хьюмидор|автомобильн|термосумк|^\s*морозильн|"
        r"^\s*lad[aă] frigorific|termoelectric|^\s*cutie",
        re.IGNORECASE),
    VACUUMS: re.compile(
        r"^\s*(?:док-станц|станция|фильтр|мешк|насадк|щ[её]тк|аккумулятор|аксессуар)|"
        r"мойщик окон|стеклоочист|мойка высокого|geamuri|window",
        re.IGNORECASE),
}


_DEFECTIVE = re.compile(r"дефект|defect", re.IGNORECASE)


def belongs(category: str, title: str) -> bool:
    if category not in KINDS:
        return True
    pattern = _OTHER_GOODS.get(category)
    if pattern is not None and pattern.search(title):
        return False
    return not _DEFECTIVE.search(title)


def _number(text: str) -> Optional[float]:
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    return float(match.group(0).replace(",", ".")) if match else None


def _fmt(value: float) -> str:
    return ("%.1f" % value).rstrip("0").rstrip(".").replace(".", ",")


def _pairs(details: str) -> Dict[str, str]:
    result = {}
    for part in re.split(r"\s+/\s+|\s*\|\s*|;\s*", details or ""):
        if ":" in part:
            name, value = part.split(":", 1)
            result[name.strip().lower()] = value.strip()
    return result


def _find(pairs: Dict[str, str], pattern: str) -> Optional[str]:
    for name, value in pairs.items():
        if re.search(pattern, name):
            return value
    return None


def _from_text(text: str, pattern: str) -> Optional[float]:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1).replace(",", ".")) if match else None


def _placement(text: str, display: Dict[str, str]) -> None:
    if re.search(r"встраиваем|incorporabil", text, re.IGNORECASE):
        display["Установка"] = "Встраиваемая"
    elif re.search(r"отдельностоящ|independent", text, re.IGNORECASE):
        display["Установка"] = "Отдельностоящая"


def _washer(title: str, pairs: Dict[str, str], text: str, display: Dict[str, str]) -> None:
    lower = text.lower()
    _placement(text, display)
    if re.search(r"вертикальн|vertical", lower):
        display["Загрузка белья"] = "Вертикальная"
    elif re.search(r"фронтальн|frontal", lower):
        display["Загрузка белья"] = "Фронтальная"
    load = _find(pairs, r"загрузк|[iî]nc[aă]rcare|capacitate")
    kg = _number(load) if load else _from_text(text, r"(\d{1,2}(?:[.,]\d)?)\s*(?:кг|kg)\b")
    if kg:
        display["Загрузка"] = "%s кг" % _fmt(kg)
    spin = _find(pairs, r"отжим|centrifug|rota[tț]")
    rpm = _number(spin) if spin else _from_text(text, r"(\d{3,4})\s*(?:об/мин|rpm|rot)")
    if rpm:
        display["Отжим"] = "%d об/мин" % rpm
    if re.search(r"с сушкой|сушк|uscare|uscător", "%s %s" % (title.lower(), " ".join(pairs))):
        display["Сушка"] = "есть"
    energy = _find(pairs, r"энерго|energetic")
    if energy:
        display["Класс энергопотребления"] = energy.split()[0]


def _fridge(title: str, pairs: Dict[str, str], text: str, display: Dict[str, str]) -> None:
    lower = text.lower()
    for pattern, label in (
        (r"side\s*-?\s*by\s*-?\s*side|sidebyside", "Side-by-Side"),
        (r"french\s*door", "French Door"),
        (r"нижней морозил|congelator jos|bottom", "С нижней морозильной камерой"),
        (r"верхней морозил|congelator sus|top", "С верхней морозильной камерой"),
        (r"без морозил", "Без морозильной камеры"),
        (r"однодвер|однокамер|o u[sș][aă]", "Однодверный"),
    ):
        if re.search(pattern, lower):
            display["Тип"] = label
            break
    total = _find(pairs, r"общий.*объ[её]м|volum.*total|capacitate.*total")
    chambers = re.findall(r"(\d{2,4})\s*[лl]\s*/", text, re.IGNORECASE)
    if total:
        liters = _number(total)
    elif len(chambers) == 2:
        liters = sum(int(v) for v in chambers)
    else:
        liters = _from_text(text, r"(\d{2,4})\s*(?:л|l)\b")
    if liters:
        display["Общий объём"] = "%d л" % liters
    if re.search(r"no\s*-?\s*frost|neo\s*frost|total\s*no", text, re.IGNORECASE):
        display["Разморозка"] = "No Frost"
    energy = _find(pairs, r"энерго|energetic")
    if energy:
        display["Класс энергопотребления"] = energy.split()[0]


def _vacuum(title: str, pairs: Dict[str, str], text: str, display: Dict[str, str]) -> None:
    lower = text.lower()
    for pattern, label in (
        (r"робот|robot", "Робот"),
        (r"моющ|sp[aă]lare", "Моющий"),
        (r"аквафильтр|водян\w* фильтр|filtru de ap", "С аквафильтром"),
        (r"вертикальн|vertical", "Вертикальный"),
        (r"портатив|беспровод|аккумулятор|f[aă]r[aă] fir", "Беспроводной"),
        (r"ручн|de m[aâ]n[aă]", "Ручной"),
        (r"с мешком|cu sac|\bмешок\b", "С мешком"),
        (r"контейнер|без мешка|f[aă]r[aă] sac|ciclon", "С контейнером"),
    ):
        if re.search(pattern, lower):
            display["Тип"] = label
            break
    suction = _find(pairs, r"мощность всасывания, па|putere de aspira.*pa")
    pascals = re.search(r"(\d{1,2}[\s\u00a0]?\d{3})\s*(?:па|pa)\b", text, re.IGNORECASE)
    if suction:
        display["Мощность всасывания"] = "%d Па" % _number(suction)
    elif pascals:
        display["Мощность всасывания"] = "%d Па" % int(re.sub(r"\D", "", pascals.group(1)))
    else:
        aw = _find(pairs, r"мощность всасывания|putere de aspira")
        if aw and _number(aw):
            display["Мощность всасывания"] = "%d аВт" % _number(aw)
    runtime = _find(pairs, r"время работы|autonomie")
    minutes = _number(runtime) if runtime else _from_text(text, r"(\d{2,3})\s*(?:мин|min)\b")
    if minutes:
        display["Время работы"] = "%d мин" % minutes
    power = _find(pairs, r"потребляемая мощность|putere (?:maxim|consum)")
    watts = _number(power) if power else _from_text(text, r"(\d{2,4})\s*(?:вт|w)\b")
    if watts:
        display["Потребляемая мощность"] = "%d Вт" % watts


def _microwave(title: str, pairs: Dict[str, str], text: str, display: Dict[str, str]) -> None:
    _placement(text, display)
    kind = _find(pairs, r"^тип$|^tip$")
    lower = "%s %s" % (text.lower(), (kind or "").lower())
    if re.search(r"конвекц|convec", lower):
        display["Тип"] = "С конвекцией"
    elif re.search(r"гриль|грилем|grill", lower):
        display["Тип"] = "С грилем"
    elif re.search(r"соло|solo", lower):
        display["Тип"] = "Соло"
    volume = _find(pairs, r"объ[её]м|volum|capacitate")
    liters = _number(volume) if volume else _from_text(text, r"(\d{2})\s*(?:литр\w*|litri|л|l)\b")
    if liters:
        display["Объём"] = "%d л" % liters
    power = _find(pairs, r"мощность микроволн|putere microunde")
    watts = _number(power) if power else _from_text(text, r"(\d{3,4})\s*(?:вт|w)\b")
    if watts:
        display["Мощность"] = "%d Вт" % watts


_PARSERS: Dict[str, Callable[[str, Dict[str, str], str, Dict[str, str]], None]] = {
    WASHERS: _washer, FRIDGES: _fridge, VACUUMS: _vacuum, MICROWAVES: _microwave,
}


def key(category: str, title: str, brand: str, details: str = "") -> str:
    return codes.key(KINDS[category], title, brand, details)


def parse_specs(category: str, title: str, details: str = "") -> Specs:
    specs = Specs()
    _PARSERS[category](title, _pairs(details), "%s %s" % (title, details or ""), specs.display)
    return specs


def product_name(category: str, titles: List[str], brands: List[str]) -> str:
    return codes.product_name(KINDS[category], titles, brands)
