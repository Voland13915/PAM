import argparse
import sys
from pathlib import Path
from typing import List

from .scrapers import AUTOMATIC, SCRAPERS
from .scrapers.base import AccessBlocked, Fetcher, ParseError, ScrapedItem


def _print_items(items: List[ScrapedItem], limit: int = 10) -> None:
    for item in items[:limit]:
        old = " (было %.0f)" % item.old_price if item.old_price else ""
        print("  %-12s %8.0f MDL%s  %s" % (item.external_id, item.price, old, item.title))
        if item.url:
            print("  %12s %s" % ("", item.url))
    if len(items) > limit:
        print("  … и ещё %d" % (len(items) - limit))


def _scrape_store(module, categories, fetcher, args) -> int:
    if not args.dry_run:
        from . import catalog, ingest
        from .db import now_iso

        store_id = catalog.get_or_create_store(*module.STORE)

    failed = 0
    for category in categories:
        print("%s / %s…" % (module.STORE[1], category))
        started = None if args.dry_run else now_iso()
        try:
            items = list(module.scrape_category(fetcher, category, args.max_pages))
        except AccessBlocked as exc:
            print("  ДОСТУП ЗАКРЫТ: %s" % exc)
            failed += 1
            continue
        except ParseError as exc:
            print("  ОШИБКА РАЗБОРА: %s" % exc)
            failed += 1
            continue
        except Exception as exc:
            print("  ОШИБКА ЗАГРУЗКИ: %s: %s" % (type(exc).__name__, exc))
            failed += 1
            continue

        print("  найдено товаров: %d" % len(items))
        if args.dry_run:
            _print_items(items)
            continue

        with catalog.transaction():
            stats = ingest.save_items(store_id, category, items, started)
            missing = ingest.mark_missing(store_id, category, started) if items else 0
        print("  новых товаров: %(new_products)d, новых предложений: %(new_offers)d, "
              "изменений цены: %(price_changes)d" % stats)
        if missing:
            print("  пропали с сайта (нет в наличии): %d" % missing)

    if not args.dry_run and failed < len(categories):
        catalog.mark_store_synced(store_id)
    return failed


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    parser = argparse.ArgumentParser(prog="python -m app.scrape")
    parser.add_argument("store", choices=["all"] + sorted(SCRAPERS),
                        help="магазин или all — все, что собираются автоматически")
    parser.add_argument("--category", action="append",
                        help="категория (можно несколько раз); по умолчанию все")
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--delay", type=float, default=1.5,
                        help="пауза между запросами, секунд")
    parser.add_argument("--dry-run", action="store_true", help="не записывать в базу")
    parser.add_argument("--save-html", type=Path, metavar="DIR")
    args = parser.parse_args(argv)

    modules = [SCRAPERS[code] for code in AUTOMATIC] if args.store == "all" \
        else [SCRAPERS[args.store]]
    for module in modules:
        unknown = [c for c in args.category or [] if c not in module.CATEGORIES]
        if unknown:
            parser.error("нет такой категории в %s: %s (есть: %s)" % (
                module.STORE[2], ", ".join(unknown), ", ".join(module.CATEGORIES)))

    if not args.dry_run:
        from . import ingest

        removed = ingest.remove_demo_catalog()
        if removed:
            print("Удалён демо-каталог: %d товаров с выдуманными ценами." % removed)

    fetcher = Fetcher(delay=args.delay, save_dir=args.save_html)
    failed = 0
    try:
        for module in modules:
            categories = args.category or list(module.CATEGORIES)
            failed += _scrape_store(module, categories, fetcher, args)
    finally:
        fetcher.close()

    if not args.dry_run:
        from .rematch import rematch

        stats = rematch()
        print("Сопоставление: товаров %(products)d, перенесено предложений %(moved)d" % stats)

    if args.save_html:
        print("Страницы сохранены в %s" % args.save_html.resolve())
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
