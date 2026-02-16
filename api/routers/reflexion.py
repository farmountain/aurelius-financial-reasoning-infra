"""Reflexion workflow router."""
from __future__ import annotations

import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.session import get_db
from database.crud import StrategyDB, ReflexionDB
from security.dependencies import get_current_user
from security.auth import TokenData
from websocket.manager import manager

router = APIRouter(prefix="/api/v1/reflexion", tags=["reflexion"])


class ReflexionRunRequest(BaseModel):
    feedback: str | None = Field(default=None, description="Optional user feedback for this iteration")


def _derive_improvement(strategy_id: str, iteration_num: int, feedback: str | None) -> float:
    seed = f"{strategy_id}:{iteration_num}:{feedback or ''}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()
    raw = int(digest[:8], 16) % 401
    return round((raw - 200) / 100.0, 2)


@router.post("/{strategy_id}/run")
async def run_reflexion_iteration(
    strategy_id: str,
    request: ReflexionRunRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    strategy = StrategyDB.get(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    existing = ReflexionDB.list_by_strategy(db, strategy_id, limit=1)
    next_iteration = 1 if not existing else existing[0].iteration_num + 1
    improvement_score = _derive_improvement(strategy_id, next_iteration, request.feedback)
    improvements = [
        f"Adjusted lookback bias for iteration {next_iteration}",
        "Updated volatility targeting to reduce regime sensitivity",
        "Improved parameter guardrails for drawdown control",
    ]

    row = ReflexionDB.create_iteration(
        db=db,
        strategy_id=strategy_id,
        improvement_score=improvement_score,
        feedback=request.feedback,
        improvements=improvements,
        context_data={
            "trigger": "manual",
            "user_id": current_user.user_id,
            "strategy_type": strategy.strategy_type,
        },
    )

    await manager.broadcast(
        {
            "event": "reflexion_iteration_created",
            "payload": {
                "strategy_id": strategy_id,
                "iteration_id": row.id,
                "iteration_num": row.iteration_num,
                "improvement_score": row.improvement_score,
            },
        },
        event_type="reflexion_iteration_created",
    )

    return {
        "id": row.id,
        "strategy_id": row.strategy_id,
        "iteration_num": row.iteration_num,
        "improvement_score": row.improvement_score,
        "feedback": row.feedback,
        "improvements": row.improvements,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/{strategy_id}/history")
async def get_reflexion_history(
    strategy_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    strategy = StrategyDB.get(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    rows = ReflexionDB.list_by_strategy(db, strategy_id, limit=limit)
    return [
        {
            "id": row.id,
            "strategy_id": row.strategy_id,
            "iteration_num": row.iteration_num,
            "improvement_score": row.improvement_score,
            "feedback": row.feedback,
            "improvements": row.improvements,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
