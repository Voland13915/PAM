import asyncio
import sys
from datetime import datetime, time, timedelta, timezone

from app import catalog, scheduler
from app.db import conn
from app.scheduler import ScrapeRunner, next_run


def test_next_run_is_today_or_tomorrow():
    at = time(4, 0)
    assert next_run(datetime(2026, 11, 19, 3, 59), at) == datetime(2026, 11, 19, 4, 0)
    assert next_run(datetime(2026, 11, 19, 4, 0), at) == datetime(2026, 11, 20, 4, 0)
    assert next_run(datetime(2026, 11, 19, 23, 30), at) == datetime(2026, 11, 20, 4, 0)


def test_run_time_comes_from_environment(monkeypatch):
    monkeypatch.setenv("SCRAPE_AT", "02:30")
    assert scheduler.run_at() == time(2, 30)
    monkeypatch.setenv("SCRAPE_AT", "когда-нибудь")
    assert scheduler.run_at() == time(4, 0)


def test_stale_data_is_detected_by_last_store_sync():
    store = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    now = datetime.now()
    fresh = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    catalog.mark_store_synced(store, fresh)
    assert not scheduler.is_stale(now)
    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(timespec="milliseconds")
    conn.execute("UPDATE stores SET last_sync = ?", (old.replace("+00:00", "Z"),))
    assert scheduler.is_stale(now)


def test_runner_starts_scraper_process_and_keeps_its_log(tmp_path):
    runner = ScrapeRunner([sys.executable, "-c", "print('собрано')"], tmp_path)
    assert asyncio.run(runner.run("тест")) is True
    status = runner.status()
    assert status["running"] is False and status["exitCode"] == 0
    assert "собрано" in runner.log_path.read_text(encoding="utf-8")


def test_runner_does_not_start_twice(tmp_path):
    runner = ScrapeRunner([sys.executable, "-c", "import time; time.sleep(0.5)"], tmp_path)

    async def both():
        first = asyncio.create_task(runner.run("первый"))
        await asyncio.sleep(0.1)
        second = await runner.run("второй")
        return await first, second

    assert asyncio.run(both()) == (True, False)


def test_old_logs_are_removed(tmp_path):
    for day in range(20):
        (tmp_path / ("scrape-202611%02d-040000.log" % (day + 1))).write_text("x")
    runner = ScrapeRunner([sys.executable, "-c", "pass"], tmp_path)
    asyncio.run(runner.run("тест"))
    assert len(list(tmp_path.glob("scrape-*.log"))) == scheduler.KEEP_LOGS


def test_sync_endpoints(client, monkeypatch):
    response = client.get("/sync")
    assert response.status_code == 200
    assert set(response.json()) >= {"running", "nextAt", "lastSync", "exitCode"}

    monkeypatch.setattr(scheduler.runner, "running", True)
    assert client.post("/sync").status_code == 409

    started = []
    monkeypatch.setattr(scheduler.runner, "running", False)
    monkeypatch.setattr(scheduler.runner, "start", lambda reason: started.append(reason) or True)
    assert client.post("/sync").status_code == 202
    assert started == ["вручную"]
    assert client.get("/sync", headers={"Authorization": ""}).status_code == 401
