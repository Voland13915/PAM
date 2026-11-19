import re
from typing import Dict, List, Optional, Tuple

COLORS: List[Tuple[str, str, str, Tuple[str, ...], Tuple[str, ...]]] = [
    ("black", "Чёрный", "#1d1d1f",
     ("black", "jet", "onyx", "obsidian", "phantom", "charcoal", "midnight black", "space black",
      "carbon black", "shadow black", "eclipse black", "abyssal black"),
     ("черн", "чёрн")),
    ("white", "Белый", "#f4f4f1",
     ("white", "porcelain", "ivory", "cloud white", "star white"),
     ("бел",)),
    ("silver", "Серебристый", "#d5d6db",
     ("silver", "platinum", "glacier silver", "natural silver", "white silver"),
     ("серебр",)),
    ("gray", "Серый", "#86888c",
     ("gray", "grey", "graphite", "slate", "gunmetal", "space gray", "space grey", "titan gray"),
     ("серый", "серая", "серое", "серого", "серо-", "серо ", "графит")),
    ("navy", "Тёмно-синий", "#22325a",
     ("navy", "deep blue", "dark blue", "midnight blue", "awesome navy"),
     ("тёмно-син", "темно-син", "тёмно син", "темно син")),
    ("midnight", "Тёмная ночь", "#2e3541",
     ("midnight",),
     ("тёмная ночь", "темная ночь", "полночь")),
    ("starlight", "Сияющая звезда", "#efe5d6",
     ("starlight",),
     ("сияющая звезда",)),
    ("lightblue", "Голубой", "#9fc3e6",
     ("light blue", "sky blue", "icy blue", "ice blue", "icyblue", "iceblue", "mist blue",
      "baby blue", "glacier blue", "sky", "icy", "ice"),
     ("голуб", "серебристо-голуб", "серебристо голуб")),
    ("blue", "Синий", "#2f63c4",
     ("blue", "ultramarine", "ocean", "indigo", "cobalt blue"),
     ("син", "индиго", "ультрамарин")),
    ("teal", "Бирюзовый", "#3a9c9b",
     ("teal", "turquoise", "aqua"),
     ("бирюз",)),
    ("green", "Зелёный", "#4f8a5b",
     ("green", "sage", "olive", "mint", "forest", "jade", "emerald"),
     ("зел", "мят", "олив")),
    ("red", "Красный", "#c8322f",
     ("red", "crimson"),
     ("красн",)),
    ("burgundy", "Бордовый", "#7a1f35",
     ("burgundy", "wine", "bordeaux", "cosmic red"),
     ("бордов",)),
    ("pink", "Розовый", "#f0a6c0",
     ("pink", "rose", "blush", "coral", "peach"),
     ("розов", "персик")),
    ("purple", "Фиолетовый", "#8a6cc4",
     ("purple", "violet", "lavender", "lilac", "plum", "cobalt violet"),
     ("фиолет", "лаванд", "сирен", "пурпур")),
    ("gold", "Золотой", "#d6b768",
     ("gold", "champagne"),
     ("золот", "шампань")),
    ("yellow", "Жёлтый", "#efd04a",
     ("yellow", "lemon", "citrus", "lemonade"),
     ("желт", "жёлт", "цитрус", "лимон")),
    ("orange", "Оранжевый", "#ef8a2a",
     ("orange", "cosmic orange", "tangerine"),
     ("оранж", "мандарин")),
    ("beige", "Бежевый", "#d9c7a5",
     ("beige", "cream", "sand", "desert", "natural", "natural titanium", "desert titanium"),
     ("беж", "кремов", "песоч")),
    ("brown", "Коричневый", "#7a5236",
     ("brown", "bronze", "copper", "umber", "mocha"),
     ("коричн", "бронз", "медн")),
    ("glacier", "Glacier", "#dce6ea",
     ("glacier",),
     ()),
]

_INFO: Dict[str, Tuple[str, str]] = {code: (name, hexcolor) for code, name, hexcolor, _, _ in COLORS}
_IGNORED = re.compile(r"red\s*magic|black\s*shark|blackview|redmi|rose\s*gold\s*edition", re.IGNORECASE)


def _patterns() -> List[Tuple[re.Pattern, str]]:
    result = []
    for code, _, _, english, russian in COLORS:
        for word in english:
            result.append((re.compile(r"\b%s\b" % re.escape(word).replace(r"\ ", r"[\s-]*")), code))
        for stem in russian:
            result.append((re.compile(r"(?<![а-яё])%s" % re.escape(stem)), code))
    return result


_PATTERNS = _patterns()


def color_of(title: str) -> str:
    text = _IGNORED.sub(" ", (title or "").lower())
    best: Optional[Tuple[int, int, str]] = None
    for pattern, code in _PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        candidate = (match.start(), -(match.end() - match.start()), code)
        if best is None or candidate < best:
            best = candidate
    return best[2] if best else ""


def color_info(code: str) -> Tuple[str, str]:
    return _INFO.get(code, (code, "#9e9e9e"))
