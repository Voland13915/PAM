import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlsplit
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

    def get(self, url: str, params: Optional[dict] = None) -> str:
        if self.check_robots and not self._allowed(url):
            raise AccessBlocked("robots.txt сайта запрещает загрузку %s" % url)

        error: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
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
