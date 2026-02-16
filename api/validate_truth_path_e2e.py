#!/usr/bin/env python3
"""End-to-end acceptance run for generate -> backtest -> validation -> gates -> promotion checks."""

from __future__ import annotations

import os
import time
import requests
import uuid

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TOKEN = os.getenv("API_BEARER_TOKEN", "")


def ensure_token() -> str:
    if TOKEN:
        return TOKEN

    email = f"opsx-{uuid.uuid4().hex[:8]}@example.com"
    password = "Passw0rd!123"
    payload = {
        "email": email,
        "name": "opsx",
        "password": password,
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=20)
    response.raise_for_status()
    return response.json()["access_token"]


AUTH_TOKEN = ensure_token()


def headers() -> dict:
    out = {"Content-Type": "application/json"}
    if AUTH_TOKEN:
        out["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return out


def wait_for_status(url: str, status_field: str = "status", target: str = "completed", timeout: int = 120) -> dict:
    started = time.time()
    while time.time() - started < timeout:
        data = requests.get(url, headers=headers(), timeout=20).json()
        if data.get(status_field) == target:
            return data
        if data.get(status_field) == "failed":
            raise RuntimeError(f"Job failed at {url}: {data}")
        time.sleep(2)
    raise TimeoutError(f"Timeout waiting for {target} at {url}")


def main() -> int:
    strategy_resp = requests.post(
        f"{BASE_URL}/api/v1/strategies/generate",
        headers=headers(),
        json={
            "goal": "test momentum strategy",
            "risk_preference": "moderate",
            "max_strategies": 1,
        },
        timeout=30,
    )
    strategy_resp.raise_for_status()
    strategy = strategy_resp.json()["strategies"][0]
    strategy_id = strategy["id"]

    backtest_resp = requests.post(
        f"{BASE_URL}/api/v1/backtests/run",
        headers=headers(),
        json={
            "strategy_id": strategy_id,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000,
            "instruments": ["SPY"],
        },
        timeout=30,
    )
    backtest_resp.raise_for_status()
    backtest_id = backtest_resp.json()["backtest_id"]
    wait_for_status(f"{BASE_URL}/api/v1/backtests/{backtest_id}/status")

    validation_resp = requests.post(
        f"{BASE_URL}/api/v1/validation/run",
        headers=headers(),
        json={
            "strategy_id": strategy_id,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "window_size_days": 60,
            "train_size_days": 180,
            "initial_capital": 100000,
        },
        timeout=30,
    )
    validation_resp.raise_for_status()
    validation_id = validation_resp.json()["validation_id"]
    wait_for_status(f"{BASE_URL}/api/v1/validation/{validation_id}/status")

    gate_resp = requests.post(
        f"{BASE_URL}/api/v1/gates/product-gate",
        headers=headers(),
        json={
            "strategy_id": strategy_id,
            "backtest_id": backtest_id,
            "validation_id": validation_id,
        },
        timeout=30,
    )
    gate_resp.raise_for_status()

    print("E2E acceptance run completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
