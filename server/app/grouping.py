import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .specs import Specs

_FOLDABLE = {"fold", "flip", "duo", "razr", "trifold", "open", "find n"}
SCREEN_TOLERANCE = {"Смартфоны": 0.3, "Ноутбуки": 1.0}


@dataclass
class Entry:
    item: Any
    base: str
    category: str
    specs: Specs
    fields: Tuple[str, ...]


@dataclass
class Cluster:
    specs: Specs
    members: List[Entry] = field(default_factory=list)


def comparable_fields(category: str, base: str, apple: bool) -> Tuple[str, ...]:
    if category in ("Телевизоры", "Стиральные машины", "Холодильники", "Пылесосы",
                    "Микроволновки"):
        return ()
    if category == "Ноутбуки":
        return ("ram", "storage", "cpu", "screen")
    model = base.split("|")[1] if base.count("|") >= 1 else base
    fields = ["storage"]
    if not apple:
        fields.append("ram")
    if not any(word in model.split() or word in model for word in _FOLDABLE):
        fields.append("screen")
    return tuple(fields)


_CORES = re.compile(r" c\d+g\d+$")


def same_cpu(a: str, b: str) -> bool:
    if a == b:
        return True
    if _CORES.search(a) and _CORES.search(b):
        return False
    short, full = sorted((_CORES.sub("", a), _CORES.sub("", b)), key=len)
    if short == full:
        return True
    return " " not in short and bool(re.search(r"\d", short)) and full.split()[-1] == short


def compatible(a: Specs, b: Specs, fields: Tuple[str, ...], category: str) -> bool:
    for name in fields:
        x, y = getattr(a, name), getattr(b, name)
        if x is None or y is None:
            continue
        if name == "screen":
            if abs(x - y) > SCREEN_TOLERANCE.get(category, 0.3):
                return False
        elif name == "cpu":
            if not same_cpu(x, y):
                return False
        elif x != y:
            return False
    return True


def _merge(target: Specs, source: Specs) -> None:
    for name in ("ram", "storage", "screen", "cpu"):
        if getattr(target, name) is None and getattr(source, name) is not None:
            setattr(target, name, getattr(source, name))
    if target.cpu and source.cpu and not _CORES.search(target.cpu) and _CORES.search(source.cpu) \
            and same_cpu(target.cpu, source.cpu):
        target.cpu = source.cpu
    for label, value in source.display.items():
        target.display.setdefault(label, value)


def _signature(specs: Specs, fields: Tuple[str, ...]) -> str:
    parts = []
    for name in ("ram", "storage", "cpu"):
        if name in fields:
            value = getattr(specs, name)
            parts.append("%s=%s" % (name, "?" if value is None else value))
    return ",".join(parts)


def cluster(entries: List[Entry]) -> List[Tuple[str, List[Entry], Specs]]:
    if not entries:
        return []
    base = entries[0].base
    category = entries[0].category
    fields = entries[0].fields
    ordered = sorted(entries, key=lambda e: -e.specs.known())

    clusters: List[Cluster] = []
    ambiguous: List[Entry] = []
    for entry in ordered:
        matches = [c for c in clusters if compatible(c.specs, entry.specs, fields, category)]
        if not matches:
            new = Cluster(Specs(display={}))
            _merge(new.specs, entry.specs)
            new.members.append(entry)
            clusters.append(new)
        elif len(matches) == 1:
            matches[0].members.append(entry)
            _merge(matches[0].specs, entry.specs)
        else:
            ambiguous.append(entry)

    if len(clusters) == 1 and not ambiguous:
        return [(base, clusters[0].members, clusters[0].specs)]

    result = []
    used: Dict[str, int] = {}
    for c in clusters:
        signature = _signature(c.specs, fields)
        if signature in used:
            used[signature] += 1
            signature += ",screen=%s" % c.specs.screen
        else:
            used[signature] = 1
        result.append(("%s|%s" % (base, signature), c.members, c.specs))
    loose: List[Cluster] = []
    for entry in ambiguous:
        target = next((c for c in loose if compatible(c.specs, entry.specs, fields, category)), None)
        if target is None:
            target = Cluster(Specs(display={}))
            loose.append(target)
        target.members.append(entry)
        _merge(target.specs, entry.specs)
    for index, c in enumerate(loose):
        key = "%s|?" % base if index == 0 else "%s|?|%s" % (base, _signature(c.specs, fields))
        if index and any(k == key for k, _, _ in result):
            key += ",%d" % index
        result.append((key, c.members, c.specs))
    return result
