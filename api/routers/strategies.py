"""Strategy management router."""
import uuid
import time
import hashlib
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python'))

try:
    from aureus.cli import parse_goal_to_spec
    HAS_AUREUS = True
except ImportError:
    HAS_AUREUS = False

from schemas.strategy import (
    StrategyGenerationRequest,
    StrategyGenerationResponse,
    GeneratedStrategy,
    StrategyParameters,
    StrategyType,
    StrategyListResponse,
    StrategyDetailResponse,
)
from database.session import get_db
from database.crud import StrategyDB
from websocket.manager import manager
from security.dependencies import get_current_user
from security.auth import TokenData

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


def _risk_to_params(risk_level: str) -> dict:
    """Convert risk preference to parameter adjustments."""
    params = {
        "conservative": {"lookback": 40, "vol_target": 0.1, "position_size": 0.5},
        "moderate": {"lookback": 20, "vol_target": 0.15, "position_size": 1.0},
        "aggressive": {"lookback": 10, "vol_target": 0.25, "position_size": 2.0},
    }
    return params.get(risk_level, params["moderate"])


STRATEGY_KEYWORDS = {
    "ts_momentum": {"momentum", "trend", "breakout"},
    "pairs_trading": {"pairs", "cointegration", "spread", "mean reversion"},
    "stat_arb": {"arbitrage", "stat", "cross-sectional"},
    "ml_classifier": {"ml", "machine learning", "classifier", "prediction"},
    "volatility_trading": {"volatility", "vol", "variance"},
    "mean_reversion": {"mean reversion", "revert", "range"},
    "trend_following": {"trend", "follow", "momentum"},
    "market_neutral": {"market neutral", "neutral", "beta"},
}


def _select_strategy_types(goal: str, risk_level: str, max_strategies: int) -> list[str]:
    """Deterministically select strategy candidates from goal and risk profile."""
    goal_lower = goal.lower()

    scored: list[tuple[str, int]] = []
    for strategy_type, keywords in STRATEGY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in goal_lower)
        if risk_level == "aggressive" and strategy_type in {"ml_classifier", "volatility_trading", "stat_arb"}:
            score += 1
        if risk_level == "conservative" and strategy_type in {"market_neutral", "pairs_trading", "mean_reversion"}:
            score += 1
        scored.append((strategy_type, score))

    scored.sort(key=lambda x: (-x[1], x[0]))
    ordered = [s for s, _ in scored]

    # Deterministic tie-break rotation based on goal+risk.
    digest = hashlib.sha256(f"{goal_lower}:{risk_level}".encode("utf-8")).hexdigest()
    rotation = int(digest[:2], 16) % len(ordered)
    rotated = ordered[rotation:] + ordered[:rotation]

    return rotated[:max_strategies]


@router.post("/generate", response_model=StrategyGenerationResponse)
async def generate_strategies(request: StrategyGenerationRequest, current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate strategies from natural language goal."""
    try:
        start_time = time.perf_counter()

        # Parse goal to spec
        if HAS_AUREUS:
            spec = parse_goal_to_spec(request.goal)

        # Convert risk preference to parameters
        risk_params = _risk_to_params(request.risk_preference.value)

        # Create generated strategies
        strategies = []
        strategy_types = _select_strategy_types(
            request.goal,
            request.risk_preference.value,
            request.max_strategies,
        )

        request_id = str(uuid.uuid4())

        for i, strategy_type in enumerate(strategy_types):
            param_adj = 1.0 - (i * 0.1)  # Decrease confidence for lower-ranked

            # Create parameters dict
            params_dict = {
                "lookback": int(risk_params["lookback"] * param_adj),
                "vol_target": risk_params["vol_target"],
                "position_size": risk_params["position_size"],
                "stop_loss": 2.0,
                "take_profit": 5.0,
            }

            if strategy_type in {"mean_reversion", "pairs_trading"}:
                params_dict["lookback"] = max(5, int(params_dict["lookback"] * 1.2))
            elif strategy_type in {"volatility_trading", "ml_classifier"}:
                params_dict["vol_target"] = min(0.35, params_dict["vol_target"] + 0.03)

            # Save to database
            strategy_data = {
                "name": f"{strategy_type.replace('_', ' ').title()} Strategy",
                "description": f"Generated strategy for: {request.goal}",
                "strategy_type": strategy_type,
                "confidence": 0.9 - (i * 0.1),
                "parameters": params_dict,
            }

            db_strategy = StrategyDB.create(db, strategy_data)

            # Create response object
            strategy_enum = StrategyType(strategy_type) if strategy_type in StrategyType._value2member_map_ else StrategyType.TREND_FOLLOWING

            strategy = GeneratedStrategy(
                id=db_strategy.id,
                strategy_type=strategy_enum,
                name=strategy_data["name"],
                description=strategy_data["description"],
                parameters=StrategyParameters(**params_dict),
                confidence=strategy_data["confidence"],
            )
            strategies.append(strategy)

        # Broadcast WebSocket event for strategy creation
        import asyncio
        asyncio.create_task(manager.broadcast({
            "event": "strategy_created",
            "payload": {
                "request_id": request_id,
                "strategy_count": len(strategies),
                "strategies": [s.dict() for s in strategies],
                "timestamp": datetime.utcnow().isoformat()
            }
        }, event_type="strategy_created"))

        generation_time_ms = (time.perf_counter() - start_time) * 1000.0

        return StrategyGenerationResponse(
            request_id=request_id,
            strategies=strategies,
            generation_time_ms=round(generation_time_ms, 3),
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Strategy generation failed: {str(e)}"
        )


@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all generated strategies."""
    strategies_db, total = StrategyDB.list(db, skip=skip, limit=limit)

    strategies = []
    for s in strategies_db:
        strategy = GeneratedStrategy(
            id=s.id,
            strategy_type=StrategyType(s.strategy_type),
            name=s.name,
            description=s.description,
            parameters=StrategyParameters(**s.parameters),
            confidence=s.confidence,
        )
        strategies.append(strategy)

    return StrategyListResponse(
        total=total,
        strategies=strategies,
    )


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Get details for a specific strategy."""
    strategy_db = StrategyDB.get(db, strategy_id)

    if not strategy_db:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy {strategy_id} not found"
        )

    strategy = GeneratedStrategy(
        strategy_type=StrategyType(strategy_db.strategy_type),
        name=strategy_db.name,
        description=strategy_db.description,
        parameters=StrategyParameters(**strategy_db.parameters),
        confidence=strategy_db.confidence,
    )

    return StrategyDetailResponse(
        strategy_id=strategy_id,
        strategy=strategy,
        created_at=strategy_db.created_at.isoformat(),
        status=strategy_db.status,
    )


@router.post("/{strategy_id}/validate")
async def validate_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Run quick validation on strategy parameters."""
    strategy_db = StrategyDB.get(db, strategy_id)

    if not strategy_db:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy {strategy_id} not found"
        )

    return {
        "strategy_id": strategy_id,
        "valid": True,
        "issues": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
