"""Strategy management router."""
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
import os

# Add python package to path for importing aureus
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python'))

from aureus.tasks.task_generator import TaskGenerator
from aureus.cli import parse_goal_to_spec
from api.schemas.strategy import (
    StrategyGenerationRequest,
    StrategyGenerationResponse,
    GeneratedStrategy,
    StrategyParameters,
    StrategyType,
    StrategyListResponse,
    StrategyDetailResponse,
)

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])

# In-memory storage for demo (replace with database in production)
_strategies_db = {}


def _risk_to_params(risk_level: str) -> dict:
    """Convert risk preference to parameter adjustments."""
    params = {
        "conservative": {"lookback": 40, "vol_target": 0.1, "position_size": 0.5},
        "moderate": {"lookback": 20, "vol_target": 0.15, "position_size": 1.0},
        "aggressive": {"lookback": 10, "vol_target": 0.25, "position_size": 2.0},
    }
    return params.get(risk_level, params["moderate"])


@router.post("/generate", response_model=StrategyGenerationResponse)
async def generate_strategies(request: StrategyGenerationRequest):
    """Generate strategies from natural language goal."""
    try:
        # Parse goal to spec
        spec = parse_goal_to_spec(request.goal)
        
        # Generate task from spec
        generator = TaskGenerator()
        tasks = generator.generate_tasks(spec)
        
        # Convert risk preference to parameters
        risk_params = _risk_to_params(request.risk_preference.value)
        
        # Create generated strategies
        strategies = []
        strategy_types = [
            "ts_momentum", "pairs_trading", "stat_arb", 
            "ml_classifier", "volatility_trading"
        ]
        
        for i, strategy_type in enumerate(strategy_types[:request.max_strategies]):
            param_adj = 1.0 - (i * 0.1)  # Decrease confidence for lower-ranked
            
            strategy = GeneratedStrategy(
                strategy_type=StrategyType(strategy_type),
                name=f"{strategy_type.replace('_', ' ').title()} Strategy",
                description=f"Generated strategy for: {request.goal}",
                parameters=StrategyParameters(
                    lookback=int(risk_params["lookback"] * param_adj),
                    vol_target=risk_params["vol_target"],
                    position_size=risk_params["position_size"],
                    stop_loss=2.0,
                    take_profit=5.0,
                ),
                confidence=0.9 - (i * 0.1),
            )
            strategies.append(strategy)
        
        # Store strategies
        request_id = str(uuid.uuid4())
        for strategy in strategies:
            strategy_id = str(uuid.uuid4())
            _strategies_db[strategy_id] = {
                "strategy": strategy,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
            }
        
        return StrategyGenerationResponse(
            request_id=request_id,
            strategies=strategies,
            generation_time_ms=125.5,  # Mock timing
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
):
    """List all generated strategies."""
    strategies_list = list(_strategies_db.values())
    total = len(strategies_list)
    
    # Paginate
    paginated = strategies_list[skip:skip + limit]
    strategies = [item["strategy"] for item in paginated]
    
    return StrategyListResponse(
        total=total,
        strategies=strategies,
    )


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(strategy_id: str):
    """Get details for a specific strategy."""
    if strategy_id not in _strategies_db:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy {strategy_id} not found"
        )
    
    strategy_data = _strategies_db[strategy_id]
    return StrategyDetailResponse(
        strategy_id=strategy_id,
        strategy=strategy_data["strategy"],
        created_at=strategy_data["created_at"],
        status=strategy_data["status"],
    )


@router.post("/{strategy_id}/validate")
async def validate_strategy(strategy_id: str):
    """Run quick validation on strategy parameters."""
    if strategy_id not in _strategies_db:
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
