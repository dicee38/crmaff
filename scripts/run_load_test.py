"""Нагрузочный тест GET /leads и GET /leads/{id}/card.

Проверяет NFR из CLAUDE.md: "P95 latency < 300ms для чтения карточки лида
и списка лидов". Требует запущенный backend (см. README) и засеянные
данные (scripts/seed_load_test_data.py).

Использование:
    python scripts/run_load_test.py --base-url http://127.0.0.1:8000 \
        --concurrency 20 --requests 500
"""

import argparse
import asyncio
import random
import statistics
import time

import httpx

EMAIL = "loadtest-manager-0@example.com"  # создаётся seed_load_test_data.py
PASSWORD = "secret123"


async def login(client: httpx.AsyncClient, base_url: str) -> str:
    resp = await client.post(f"{base_url}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


async def fetch_lead_ids(client: httpx.AsyncClient, base_url: str, headers: dict, n: int) -> list[str]:
    ids: list[str] = []
    cursor = None
    while len(ids) < n:
        params = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        resp = await client.get(f"{base_url}/api/v1/leads", params=params, headers=headers)
        resp.raise_for_status()
        body = resp.json()
        ids.extend(item["lead_id"] for item in body["items"])
        cursor = body["next_cursor"]
        if not cursor:
            break
    return ids[:n]


async def worker(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict,
    lead_ids: list[str],
    n_requests: int,
    list_latencies: list[float],
    card_latencies: list[float],
    errors: list[str],
) -> None:
    for _ in range(n_requests):
        is_list = random.random() < 0.5
        try:
            if is_list:
                geo = random.choice(["SY", "MA", "SA"])
                start = time.perf_counter()
                resp = await client.get(
                    f"{base_url}/api/v1/leads", params={"limit": 50, "geo": geo}, headers=headers
                )
                elapsed = (time.perf_counter() - start) * 1000
                resp.raise_for_status()
                list_latencies.append(elapsed)
            else:
                lead_id = random.choice(lead_ids)
                start = time.perf_counter()
                resp = await client.get(f"{base_url}/api/v1/leads/{lead_id}/card", headers=headers)
                elapsed = (time.perf_counter() - start) * 1000
                resp.raise_for_status()
                card_latencies.append(elapsed)
        except Exception as exc:  # noqa: BLE001 - собираем любые сбои для отчёта
            errors.append(str(exc))


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return float("nan")
    return statistics.quantiles(values, n=100)[pct - 1] if len(values) > 1 else values[0]


def _report(name: str, values: list[float]) -> None:
    if not values:
        print(f"{name}: нет данных")
        return
    print(
        f"{name}: n={len(values)} "
        f"p50={_percentile(values, 50):.1f}ms "
        f"p95={_percentile(values, 95):.1f}ms "
        f"p99={_percentile(values, 99):.1f}ms "
        f"max={max(values):.1f}ms"
    )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--requests", type=int, default=25, help="запросов на воркера")
    args = parser.parse_args()

    async with httpx.AsyncClient(timeout=30.0) as client:
        token = await login(client, args.base_url)
        headers = {"Authorization": f"Bearer {token}"}

        print("[load-test] Собираю пул lead_id для карточек...")
        lead_ids = await fetch_lead_ids(client, args.base_url, headers, n=500)
        print(f"[load-test] Пул: {len(lead_ids)} лидов")

        list_latencies: list[float] = []
        card_latencies: list[float] = []
        errors: list[str] = []

        print(f"[load-test] concurrency={args.concurrency}, requests/worker={args.requests}")
        start = time.perf_counter()
        await asyncio.gather(
            *[
                worker(client, args.base_url, headers, lead_ids, args.requests, list_latencies, card_latencies, errors)
                for _ in range(args.concurrency)
            ]
        )
        total_time = time.perf_counter() - start

        total_requests = len(list_latencies) + len(card_latencies) + len(errors)
        print(f"\n[load-test] Готово за {total_time:.1f}s, всего запросов: {total_requests}, ошибок: {len(errors)}")
        _report("GET /leads (список)", list_latencies)
        _report("GET /leads/{id}/card (карточка)", card_latencies)

        if errors:
            print(f"\nПервые ошибки: {errors[:5]}")

        p95_list = _percentile(list_latencies, 95) if list_latencies else 0
        p95_card = _percentile(card_latencies, 95) if card_latencies else 0
        print(f"\nNFR (P95 < 300ms): список={'OK' if p95_list < 300 else 'FAIL'}, карточка={'OK' if p95_card < 300 else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
