import asyncio
import os
import subprocess
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .db import BASE_DIR, conn
from .scrapers import AUTOMATIC

LOG_DIR = BASE_DIR / "logs"
KEEP_LOGS = 14
STALE_AFTER = timedelta(hours=20)
STARTUP_DELAY = 60.0


def enabled() -> bool:
    return os.environ.get("AUTO_SCRAPE", "1") == "1"


def run_at() -> time:
    value = os.environ.get("SCRAPE_AT", "13:00")
    try:
        hours, minutes = (int(part) for part in value.split(":", 1))
        return time(hours, minutes)
    except ValueError:
        return time(4, 0)


def next_run(now: datetime, at: time) -> datetime:
    candidate = now.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
    return candidate if candidate > now else candidate + timedelta(days=1)


def last_sync() -> Optional[datetime]:
    row = conn.execute(
        "SELECT MAX(last_sync) AS last FROM stores WHERE last_sync != '' AND code IN (%s)"
        % ",".join("?" * len(AUTOMATIC)),
        AUTOMATIC,
    ).fetchone()
    if row is None or not row["last"]:
        return None
    moment = datetime.fromisoformat(row["last"].replace("Z", "+00:00"))
    return moment.astimezone().replace(tzinfo=None)


def is_stale(now: datetime) -> bool:
    last = last_sync()
    return last is None or now - last > STALE_AFTER


def _stamp(moment: Optional[datetime]) -> Optional[str]:
    return moment.astimezone().isoformat(timespec="seconds") if moment else None


class ScrapeRunner:
    def __init__(self, command: Optional[List[str]] = None, log_dir: Path = LOG_DIR):
        self.command = command or [sys.executable, "-m", "app.scrape", "all"]
        self.log_dir = log_dir
        self.running = False
        self.reason = ""
        self.started_at: Optional[datetime] = None
        self.finished_at: Optional[datetime] = None
        self.exit_code: Optional[int] = None
        self.log_path: Optional[Path] = None
        self.next_at: Optional[datetime] = None

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": enabled(),
            "running": self.running,
            "reason": self.reason,
            "startedAt": _stamp(self.started_at),
            "finishedAt": _stamp(self.finished_at),
            "exitCode": self.exit_code,
            "nextAt": _stamp(self.next_at),
            "lastSync": _stamp(last_sync()),
            "log": self.log_path.name if self.log_path else None,
        }

    def _prune_logs(self) -> None:
        logs = sorted(self.log_dir.glob("scrape-*.log"))
        for old in logs[:-KEEP_LOGS]:
            try:
                old.unlink()
            except OSError:
                pass

    async def run(self, reason: str) -> bool:
        if self.running:
            return False
        self.running = True
        await self._execute(reason)
        return True

    def start(self, reason: str) -> bool:
        if self.running:
            return False
        self.running = True
        asyncio.get_running_loop().create_task(self._execute(reason))
        return True

    async def _execute(self, reason: str) -> None:
        self.reason = reason
        self.started_at = datetime.now()
        self.exit_code = None
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / self.started_at.strftime("scrape-%Y%m%d-%H%M%S.log")
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "AUTO_SCRAPE": "0"}
        print("Автосбор цен (%s) начат, журнал: %s" % (reason, self.log_path), flush=True)
        process = None
        try:
            with self.log_path.open("w", encoding="utf-8") as log:
                process = subprocess.Popen(
                    self.command, cwd=str(BASE_DIR), env=env,
                    stdout=log, stderr=subprocess.STDOUT,
                )
                self.exit_code = await asyncio.to_thread(process.wait)
        except asyncio.CancelledError:
            if process is not None and process.poll() is None:
                process.terminate()
            raise
        except OSError as exc:
            self.exit_code = -1
            print("Автосбор цен не запустился: %s" % exc, flush=True)
        finally:
            self.running = False
            self.finished_at = datetime.now()
            self._prune_logs()
        print("Автосбор цен завершён, код %s" % self.exit_code, flush=True)

    async def loop(self) -> None:
        at = run_at()
        if is_stale(datetime.now()):
            self.next_at = datetime.now() + timedelta(seconds=STARTUP_DELAY)
            await asyncio.sleep(STARTUP_DELAY)
            await self.run("данные устарели")
        while True:
            self.next_at = next_run(datetime.now(), at)
            await asyncio.sleep(max((self.next_at - datetime.now()).total_seconds(), 1.0))
            await self.run("по расписанию")


runner = ScrapeRunner()
