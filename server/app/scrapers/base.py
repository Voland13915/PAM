import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = (
    "Mozilla/5.0 (compatible; TechPriceBot/0.1; "
    "student price-comparison project, UTM)"
)


class ParseError(Exception):
    pass


class AccessBlocked(Exception):
    pass


class PageNotFound(Exception):
    pass


@dataclass
class ScrapedItem:
    external_id: str
    title: str
    brand: str
    price: float
    old_price: Optional[float] = None
    url: str = ""
    in_stock: bool = True
    details: str = ""
    image_url: str = ""
    color: str = ""


_IMAGE_ATTRIBUTES = ("data-src", "data-lazy-src", "data-original", "data-srcset", "srcset", "src")


def pick_image(card, base_url: str) -> str:
    for img in card.find_all("img"):
        for attribute in _IMAGE_ATTRIBUTES:
            value = (img.get(attribute) or "").strip()
            if not value:
                continue
            value = value.split(",")[0].split()[0]
            lower = value.lower()
            if lower.startswith("data:") or lower.endswith(".svg") or "lazy" in lower \
                    or "placeholder" in lower or "blank" in lower:
                continue
            return urljoin(base_url + "/", value)
    return ""


class Fetcher:
    def __init__(
        self,
        delay: float = 1.5,
        retries: int = 3,
        timeout: float = 20.0,
        save_dir: Optional[Path] = None,
        client: Optional[httpx.Client] = None,
        check_robots: bool = True,
    ):
        self.delay = delay
        self.retries = retries
        self.save_dir = save_dir
        self.check_robots = check_robots
        self._robots: Dict[str, RobotFileParser] = {}
        self._last = 0.0
        self._saved = 0
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "ru,ro;q=0.8"},
        )

    def _allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        site = "%s://%s" % (parts.scheme, parts.netloc)
        if site not in self._robots:
            parser = RobotFileParser()
            try:
                response = self._client.get(site + "/robots.txt")
                lines = response.text.splitlines() if response.status_code == 200 else []
            except httpx.HTTPError:
                lines = []
            parser.parse(lines)
            self._robots[site] = parser
        return self._robots[site].can_fetch("TechPriceBot", url)

    def get(self, url: str, params: Optional[dict] = None, fresh: bool = False) -> str:
        if self.check_robots and not self._allowed(url):
            raise AccessBlocked("robots.txt сайта запрещает загрузку %s" % url)

        error: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            if fresh:
                self._client.cookies.clear()
            try:
                response = self._client.get(url, params=params)
            except httpx.TransportError as exc:
                error = exc
                time.sleep(self.delay * attempt)
                continue

            if response.status_code == 404:
                raise PageNotFound(str(response.request.url))
            if response.status_code in (401, 403, 429) or "Just a moment" in response.text[:2000]:
                protection = response.headers.get("server", "")
                raise AccessBlocked(
                    "сайт отказал в доступе (HTTP %d%s) — автоматический сбор с него "
                    "недоступен" % (response.status_code,
                                    ", защита " + protection if protection else "")
                )
            if response.status_code >= 500:
                error = httpx.HTTPStatusError(
                    "HTTP %d" % response.status_code,
                    request=response.request, response=response,
                )
                time.sleep(self.delay * attempt)
                continue
            response.raise_for_status()
            self._save(response)
            return response.text
        raise error

    def _save(self, response: httpx.Response) -> None:
        if self.save_dir is None:
            return
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self._saved += 1
        path = self.save_dir / ("%03d.html" % self._saved)
        path.write_text(
            "<!-- %s -->\n%s" % (response.request.url, response.text), encoding="utf-8"
        )

    def close(self) -> None:
        self._client.close()


def paths(value: Union[str, Tuple[str, ...]]) -> Tuple[str, ...]:
    return (value,) if isinstance(value, str) else tuple(value)


def amount(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", str(text))
    return float(digits) if digits else None


def text_of(node, selector: Optional[str] = None) -> str:
    element = node.select_one(selector) if selector else node
    return " ".join(element.get_text(" ").split()) if element is not None else ""


def absolute(url: str, base_url: str) -> str:
    return urljoin(base_url + "/", url) if url else ""


def crawl(
    fetcher: "Fetcher",
    page_url: Callable[[int], str],
    parse: Callable[[str], List[ScrapedItem]],
    max_pages: int,
    fresh_session: bool = False,
) -> Iterator[ScrapedItem]:
    seen = set()
    full_page = previous = 0
    for page in range(1, max_pages + 1):
        try:
            html = fetcher.get(page_url(page), fresh=fresh_session)
        except PageNotFound:
            if page == 1:
                raise
            return
        except (AccessBlocked, httpx.HTTPError) as exc:
            if page == 1:
                raise
            if previous < full_page:
                return
            print("  внимание: страница %d недоступна (%s: %s), собрано только до неё"
                  % (page, type(exc).__name__, exc))
            return
        try:
            items = parse(html)
        except ParseError:
            if page == 1:
                raise
            return
        fresh = [i for i in items if i.external_id not in seen]
        if not fresh:
            if page == 2:
                print("  внимание: вторая страница повторяет первую — листание не сработало")
            return
        full_page = full_page or len(items)
        previous = len(fresh)
        for item in fresh:
            seen.add(item.external_id)
            yield item
