import argparse
import sys
from pathlib import Path

from .scrapers.base import AccessBlocked, Fetcher, PageNotFound


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.fetch_page")
    parser.add_argument("url", nargs="+")
    parser.add_argument("--out", type=Path, default=Path("pages"))
    args = parser.parse_args(argv)

    fetcher = Fetcher(save_dir=args.out)
    failed = 0
    try:
        for url in args.url:
            try:
                html = fetcher.get(url)
                print("OK  %s (%d символов)" % (url, len(html)))
            except (AccessBlocked, PageNotFound) as exc:
                print("НЕТ %s: %s" % (url, exc))
                failed += 1
    finally:
        fetcher.close()
    print("Страницы сохранены в %s" % args.out.resolve())
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
