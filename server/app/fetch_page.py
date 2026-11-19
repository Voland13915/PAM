import argparse
import sys
from pathlib import Path

import httpx

from .scrapers.base import USER_AGENT, AccessBlocked, Fetcher, PageNotFound


def trace(client: httpx.Client, url: str) -> None:
    print(url)
    for _ in range(12):
        sent = ", ".join(sorted(client.cookies.keys()))
        response = client.get(url)
        cookies = ", ".join(sorted(response.cookies.keys()))
        print("  %d %s%s%s" % (response.status_code, response.headers.get("location", ""),
                               "  отправлены: " + sent if sent else "",
                               "  получены: " + cookies if cookies else ""))
        if response.status_code not in (301, 302, 303, 307, 308):
            return
        url = str(response.url.join(response.headers.get("location", "")))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.fetch_page")
    parser.add_argument("url", nargs="+")
    parser.add_argument("--out", type=Path, default=Path("pages"))
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args(argv)

    if args.trace:
        with httpx.Client(follow_redirects=False, timeout=20.0,
                          headers={"User-Agent": USER_AGENT,
                                   "Accept-Language": "ru,ro;q=0.8"}) as client:
            for url in args.url:
                trace(client, url)
        return 0

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
