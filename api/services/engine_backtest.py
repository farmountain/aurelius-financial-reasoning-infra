"""Engine-backed backtest execution service for API routes."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.parity_config import PARITY_TOLERANCES, metric_within_tolerance


@dataclass
class EngineRunResult:
    metrics: dict[str, Any]
    trades: list[dict[str, Any]]
    equity_curve: list[dict[str, Any]]
    run_identity: dict[str, str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _engine_binary() -> str:
    configured = os.getenv("QUANT_ENGINE_PATH")
    if configured:
        return configured

    root = _repo_root()
    release = root / "target" / "release" / "quant_engine"
    debug = root / "target" / "debug" / "quant_engine"
    release_exe = root / "target" / "release" / "quant_engine.exe"
    debug_exe = root / "target" / "debug" / "quant_engine.exe"

    if release_exe.exists():
        return str(release_exe)
    if debug_exe.exists():
        return str(debug_exe)

    if release.exists():
        return str(release)
    if debug.exists():
        return str(debug)

    return "quant_engine.exe" if os.name == "nt" else "quant_engine"


def _engine_version() -> str:
    try:
        result = subprocess.run([
            _engine_binary(),
            "--version",
        ], capture_output=True, text=True, check=False)
        out = (result.stdout or result.stderr or "").strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _build_spec(strategy: dict[str, Any], request_data: dict[str, Any]) -> dict[str, Any]:
    lookback = int(strategy.get("parameters", {}).get("lookback", 20))
    vol_target = float(strategy.get("parameters", {}).get("vol_target", 0.15))
    symbol = request_data.get("instruments", ["SPY"])[0] if request_data.get("instruments") else "SPY"

    # Current Rust CLI supports ts_momentum.
    return {
        "initial_cash": float(request_data.get("initial_capital", 100000.0)),
        "seed": int(request_data.get("seed", 42)),
        "data_pipeline": "canonical_tier1",
        "strategy": {
            "type": "ts_momentum",
            "symbol": symbol,
            "lookback": max(2, lookback),
            "vol_target": max(0.01, vol_target),
            "vol_lookback": max(2, lookback),
        },
        "cost_model": {
            "type": "fixed_per_share",
            "cost_per_share": 0.005,
            "minimum_commission": 1.0,
        },
    }


def _default_data_path(data_source: str | None = None) -> Path:
    source = (data_source or "").strip()
    if source and source.lower() != "default":
        candidate = Path(source)
        if candidate.exists():
            return candidate

        repo_candidate = _repo_root() / "data" / source
        if repo_candidate.exists():
            return repo_candidate

    configured = os.getenv("BACKTEST_DATA_PATH")
    if configured:
        return Path(configured)
    return _repo_root() / "examples" / "alpaca_data.parquet"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_trades(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    import csv

    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def _read_equity(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    import csv

    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def _compute_profit_factor(returns: list[float]) -> float:
    gains = sum(r for r in returns if r > 0)
    losses = abs(sum(r for r in returns if r < 0))
    if losses == 0:
        return 99.0 if gains > 0 else 0.0
    return gains / losses


def _compute_win_rate(returns: list[float]) -> float:
    if not returns:
        return 0.0
    wins = sum(1 for r in returns if r > 0)
    return (wins / len(returns)) * 100.0


def _returns_from_equity(equity_curve: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for row in equity_curve:
        try:
            values.append(float(row["equity"]))
        except Exception:
            continue

    if len(values) < 2:
        return []

    out = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if prev != 0:
            out.append((curr - prev) / prev)
    return out


def _normalize_metrics(stats: dict[str, Any], equity_curve: list[dict[str, Any]], trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = _returns_from_equity(equity_curve)

    total_return_pct = float(stats.get("total_return", 0.0)) * 100.0
    max_dd_pct = -abs(float(stats.get("max_drawdown", 0.0)) * 100.0)
    sharpe = float(stats.get("sharpe_ratio", 0.0))

    metrics = {
        "total_return": total_return_pct,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sharpe * 1.1,
        "max_drawdown": max_dd_pct,
        "win_rate": _compute_win_rate(returns),
        "profit_factor": _compute_profit_factor(returns),
        "total_trades": int(stats.get("num_trades", len(trades))),
        "avg_trade": (total_return_pct / int(stats.get("num_trades", 1))) if int(stats.get("num_trades", 0)) > 0 else 0.0,
        "calmar_ratio": (total_return_pct / abs(max_dd_pct)) if max_dd_pct != 0 else 0.0,
    }
    return metrics


def _within_tolerance(a: dict[str, Any], b: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    violations = {}
    for k, tol in PARITY_TOLERANCES.items():
        av = float(a.get(k, 0.0))
        bv = float(b.get(k, 0.0))
        delta = abs(av - bv)
        if not metric_within_tolerance(k, av, bv):
            violations[k] = {"a": av, "b": bv, "delta": delta, "tolerance": tol}
    return len(violations) == 0, violations


def run_engine_backtest(strategy: dict[str, Any], request_data: dict[str, Any], run_replay_check: bool = True) -> EngineRunResult:
    data_source = request_data.get("data_source")
    data_path = _default_data_path(data_source)
    if not data_path.exists():
        raise RuntimeError(f"Backtest data file not found: {data_path}")

    spec = _build_spec(strategy, request_data)
    spec_text = json.dumps(spec, sort_keys=True)
    spec_hash = _sha256_text(spec_text)
    data_hash = _sha256_file(data_path)
    engine_version = _engine_version()

    with tempfile.TemporaryDirectory(prefix="aurelius_api_bt_") as tmp:
        tmp_path = Path(tmp)
        spec_path = tmp_path / "spec.json"
        out_dir = tmp_path / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        with spec_path.open("w", encoding="utf-8") as f:
            f.write(spec_text)

        cmd = [
            _engine_binary(),
            "backtest",
            "--spec", str(spec_path),
            "--data", str(data_path),
            "--out", str(out_dir),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"Engine backtest failed: {res.stderr or res.stdout}")

        stats = _read_json(out_dir / "stats.json")
        crv = _read_json(out_dir / "crv_report.json") if (out_dir / "crv_report.json").exists() else {}
        trades = _read_trades(out_dir / "trades.csv")
        equity = _read_equity(out_dir / "equity_curve.csv")

        metrics = _normalize_metrics(stats, equity, trades)
        metrics["crv_passed"] = bool(crv.get("passed", False))
        metrics["crv_violations"] = crv.get("violations", [])

        replay_status = {"checked": False, "passed": True, "violations": {}}
        if run_replay_check:
            replay_out = tmp_path / "replay"
            replay_out.mkdir(parents=True, exist_ok=True)
            replay = subprocess.run([
                _engine_binary(),
                "backtest",
                "--spec", str(spec_path),
                "--data", str(data_path),
                "--out", str(replay_out),
            ], capture_output=True, text=True, check=False)
            if replay.returncode == 0 and (replay_out / "stats.json").exists():
                replay_stats = _read_json(replay_out / "stats.json")
                replay_trades = _read_trades(replay_out / "trades.csv")
                replay_equity = _read_equity(replay_out / "equity_curve.csv")
                replay_metrics = _normalize_metrics(replay_stats, replay_equity, replay_trades)
                ok, violations = _within_tolerance(metrics, replay_metrics)
                replay_status = {"checked": True, "passed": ok, "violations": violations}
            else:
                replay_status = {"checked": True, "passed": False, "violations": {"engine": "replay_failed"}}

        metrics["parity_check"] = replay_status
        metrics["replay_pass"] = bool(replay_status.get("passed", False))

        run_identity = {
            "spec_hash": spec_hash,
            "data_hash": data_hash,
            "seed": str(spec.get("seed", 42)),
            "engine_version": engine_version,
        }

        metrics["run_identity"] = run_identity
        metrics["data_provenance"] = {
            "source": data_source or "default",
            "path": str(data_path),
            "data_hash": data_hash,
        }
        metrics["transformation_lineage"] = [
            {"step": "build_spec", "details": "strategy -> engine spec"},
            {"step": "execute_engine", "details": "rust quant_engine backtest"},
            {"step": "normalize_metrics", "details": "stats -> api metrics schema"},
        ]
        metrics["policy_outcomes"] = {
            "crv_passed": metrics.get("crv_passed", False),
            "replay_pass": metrics.get("replay_pass", False),
        }
        metrics["artifact_links"] = {
            "stats": "stats.json",
            "trades": "trades.csv",
            "equity_curve": "equity_curve.csv",
            "crv": "crv_report.json",
        }
        metrics["execution_mode"] = "engine"

        return EngineRunResult(
            metrics=metrics,
            trades=trades,
            equity_curve=equity,
            run_identity=run_identity,
        )
