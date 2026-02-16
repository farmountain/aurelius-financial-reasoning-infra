"""Run a live-stack end-to-end acceptance flow and record evidence.

Flow:
strategy -> backtest -> validation -> gates -> reflexion -> orchestrator
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = REPO_ROOT / "docs" / "ACCEPTANCE_EVIDENCE_CLOSE_PRODUCT_EXPERIENCE_GAPS.md"
BASE_URL = "http://127.0.0.1:8011"


def _wait_for_server(timeout_sec: int = 45) -> None:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            r = requests.get(f"{BASE_URL}/", timeout=3)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("API server did not become ready in time")


def _poll(
    url: str,
    wanted: str = "completed",
    timeout_sec: int = 240,
    interval: float = 2.0,
    headers: dict | None = None,
) -> dict:
    start = time.time()
    last = None
    while time.time() - start < timeout_sec:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        last = r.json()
        status = (last or {}).get("status")
        if status == wanted:
            return last
        if status == "failed":
            return last
        time.sleep(interval)
    return last or {}


def _append_evidence(lines: list[str]) -> None:
    content = EVIDENCE_PATH.read_text(encoding="utf-8") if EVIDENCE_PATH.exists() else "# Acceptance Evidence: close-product-experience-gaps\n"
    content = content.rstrip() + "\n\n" + "\n".join(lines) + "\n"
    EVIDENCE_PATH.write_text(content, encoding="utf-8")


def _safe_json_response(resp: requests.Response) -> dict:
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text[:1000]}
    return {
        "status_code": resp.status_code,
        "body": body,
    }


def main() -> int:
    env = os.environ.copy()
    env["DB_USER"] = "admin"
    env["DB_PASSWORD"] = "admin"
    env["DB_NAME"] = "aurelius"
    env["DB_HOST"] = "127.0.0.1"
    env["DB_PORT"] = "55432"
    env["PYTHONIOENCODING"] = "utf-8"

    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8011"],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    evidence: dict[str, object] = {
        "timestamp": datetime.utcnow().isoformat(),
        "base_url": BASE_URL,
        "environment": {
            "os": os.name,
            "db_host": env["DB_HOST"],
            "db_port": env["DB_PORT"],
            "db_name": env["DB_NAME"],
        },
    }

    try:
        _wait_for_server()

        session = requests.Session()

        # Register/login
        email = f"e2e_{uuid.uuid4().hex[:10]}@example.com"
        password = "TestPass123!"
        register_payload = {"email": email, "password": password, "name": "E2E User"}
        reg = session.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=15)
        reg.raise_for_status()
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        evidence["user_email"] = email

        # Generate strategy
        gen_payload = {
            "goal": "Build a momentum strategy with moderate risk and stable drawdown",
            "risk_preference": "moderate",
            "max_strategies": 1,
        }
        gen = session.post(f"{BASE_URL}/api/v1/strategies/generate", json=gen_payload, headers=headers, timeout=30)
        gen.raise_for_status()
        strategy = gen.json()["strategies"][0]
        strategy_id = strategy["id"]
        evidence["strategy_id"] = strategy_id

        # Backtest
        bt_payload = {
            "strategy_id": strategy_id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000,
            "instruments": ["SPY"],
            "seed": 123,
            "data_source": "default",
        }
        bt = session.post(f"{BASE_URL}/api/v1/backtests/run", json=bt_payload, headers=headers, timeout=30)
        bt.raise_for_status()
        backtest_id = bt.json()["backtest_id"]
        bt_status = _poll(
            f"{BASE_URL}/api/v1/backtests/{backtest_id}/status",
            wanted="completed",
            headers=headers,
        )
        evidence["backtest"] = {
            "backtest_id": backtest_id,
            "status": bt_status.get("status"),
            "execution_metadata": bt_status.get("execution_metadata"),
        }

        # Validation
        val_payload = {
            "strategy_id": strategy_id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "window_size_days": 90,
            "train_size_days": 180,
            "initial_capital": 100000,
        }
        val = session.post(f"{BASE_URL}/api/v1/validation/run", json=val_payload, headers=headers, timeout=30)
        val.raise_for_status()
        validation_id = val.json()["validation_id"]
        val_status = _poll(
            f"{BASE_URL}/api/v1/validation/{validation_id}/status",
            wanted="completed",
            headers=headers,
        )
        evidence["validation"] = {
            "validation_id": validation_id,
            "status": val_status.get("status"),
        }

        # Gates
        gate_payload = {
            "strategy_id": strategy_id,
            "backtest_id": backtest_id,
            "validation_id": validation_id,
        }
        dev = session.post(f"{BASE_URL}/api/v1/gates/dev-gate", json=gate_payload, headers=headers, timeout=30)
        crv = session.post(f"{BASE_URL}/api/v1/gates/crv-gate", json=gate_payload, headers=headers, timeout=30)
        product = session.post(f"{BASE_URL}/api/v1/gates/product-gate", json=gate_payload, headers=headers, timeout=30)
        gate_status = session.get(f"{BASE_URL}/api/v1/gates/{strategy_id}/status", headers=headers, timeout=30)
        evidence["gates"] = {
            "dev": _safe_json_response(dev),
            "crv": _safe_json_response(crv),
            "product": _safe_json_response(product),
            "status": _safe_json_response(gate_status),
        }

        # Reflexion visibility
        rx = session.post(
            f"{BASE_URL}/api/v1/reflexion/{strategy_id}/run",
            json={"feedback": "Improve risk-adjusted returns"},
            headers=headers,
            timeout=30,
        )
        rx.raise_for_status()
        rx_hist = session.get(f"{BASE_URL}/api/v1/reflexion/{strategy_id}/history", headers=headers, timeout=30)
        rx_hist.raise_for_status()
        evidence["reflexion"] = {
            "latest_iteration_id": rx.json().get("id"),
            "history_count": len(rx_hist.json() if isinstance(rx_hist.json(), list) else []),
        }

        # Orchestrator visibility
        orch_payload = {
            "strategy_id": strategy_id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000,
            "instruments": ["SPY"],
            "seed": 123,
            "data_source": "default",
        }
        orch = session.post(f"{BASE_URL}/api/v1/orchestrator/runs", json=orch_payload, headers=headers, timeout=300)
        orch_json = orch.json() if orch.headers.get("content-type", "").startswith("application/json") else {}
        run_id = orch_json.get("run_id")
        orch_status = session.get(f"{BASE_URL}/api/v1/orchestrator/runs/{run_id}", headers=headers, timeout=30) if run_id else None
        orch_list = session.get(f"{BASE_URL}/api/v1/orchestrator/runs", headers=headers, timeout=30)
        evidence["orchestrator"] = {
            "run_id": run_id,
            "create": _safe_json_response(orch),
            "status": _safe_json_response(orch_status) if orch_status is not None else None,
            "list": _safe_json_response(orch_list),
        }

        lines = [
            "## Live End-to-End Acceptance Run",
            f"- Timestamp (UTC): `{evidence['timestamp']}`",
            f"- API Base URL: `{BASE_URL}`",
            f"- Environment: `{json.dumps(evidence['environment'])}`",
            f"- Strategy ID: `{strategy_id}`",
            f"- Backtest: `{json.dumps(evidence['backtest'])}`",
            f"- Validation: `{json.dumps(evidence['validation'])}`",
            f"- Gates: `{json.dumps({'dev_status': evidence['gates']['dev']['status_code'], 'crv_status': evidence['gates']['crv']['status_code'], 'product_status': evidence['gates']['product']['status_code']})}`",
            f"- Reflexion: `{json.dumps(evidence['reflexion'])}`",
            f"- Orchestrator: `{json.dumps(evidence['orchestrator'])}`",
        ]
        _append_evidence(lines)

        print(json.dumps({"ok": True, "evidence": evidence}, indent=2))
        return 0

    except Exception as exc:
        failure_lines = [
            "## Live End-to-End Acceptance Run (FAILED)",
            f"- Timestamp (UTC): `{datetime.utcnow().isoformat()}`",
            f"- Error: `{type(exc).__name__}: {exc}`",
        ]
        _append_evidence(failure_lines)
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}", "partial": evidence}, indent=2))
        return 1

    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except Exception:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
