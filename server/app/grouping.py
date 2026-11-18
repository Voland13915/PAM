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
    if category == "Ноутбуки":
        return ("ram", "storage", "cpu", "screen")
    model = base.split("|")[1] if base.count("|") >= 1 else base
    fields = ["storage"]
    if not apple:
        fields.append("ram")
    if not any(word in model.split() or word in model for word in _FOLDABLE):
        fields.append("screen")
    return tuple(fields)


def compatible(a: Specs, b: Specs, fields: Tuple[str, ...], category: str) -> bool:
    for name in fields:
        x, y = getattr(a, name), getattr(b, name)
        if x is None or y is None:
            continue
        if name == "screen":
            if abs(x - y) > SCREEN_TOLERANCE.get(category, 0.3):
                return False
        elif x != y:
            return False
    return True


def _merge(target: Specs, source: Specs) -> None:
    for name in ("ram", "storage", "screen", "cpu"):
        if getattr(target, name) is None and getattr(source, name) is not None:
            setattr(target, name, getattr(source, name))
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
    if ambiguous:
        specs = Specs(display={})
        for entry in ambiguous:
            _merge(specs, entry.specs)
        result.append(("%s|?" % base, ambiguous, specs))
    return result
