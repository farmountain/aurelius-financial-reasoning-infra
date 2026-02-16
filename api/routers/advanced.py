"""
Advanced Features API Router
Portfolio optimization, risk analytics, ML optimization
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import numpy as np
from datetime import datetime
import logging

from api.database.session import get_db
from api.security.dependencies import get_current_user
from api.advanced.portfolio_optimizer import (
    PortfolioOptimizer,
    OptimizationMethod,
    PortfolioMetrics
)
from api.advanced.risk_metrics import RiskAnalyzer, RiskMetrics, format_risk_metrics
from api.advanced.ml_optimizer import (
    StrategyOptimizer,
    OptimizationResult,
    EXAMPLE_PARAM_SPACES
)
from api.database.crud import StrategyDB
from api.services.engine_backtest import run_engine_backtest
from api.advanced.risk_management import (
    RiskManager,
    RiskLimits,
    PositionSizeMethod
)
from api.advanced.indicators import (
    indicator_registry,
    calculate_indicator,
    calculate_multiple_indicators
)
from api.advanced.multi_asset import (
    AssetClass,
    AssetMetadata,
    MultiAssetPortfolio,
    CrossAssetAnalyzer,
    OptionPricer
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/advanced", tags=["advanced"])


# Request/Response Models
class OptimizePortfolioRequest(BaseModel):
    returns: List[List[float]]  # Matrix of returns for each asset
    method: str = "max_sharpe"
    risk_free_rate: float = 0.02
    target_return: Optional[float] = None
    max_weight: float = 1.0
    min_weight: float = 0.0


class RiskAnalysisRequest(BaseModel):
    returns: List[float]
    equity_curve: Optional[List[float]] = None
    risk_free_rate: float = 0.02


class OptimizeStrategyRequest(BaseModel):
    strategy_id: str
    param_space: Dict[str, Dict[str, Any]]
    data_start: str
    data_end: str
    n_trials: int = 100
    objective_metric: str = "sharpe_ratio"


class PositionSizeRequest(BaseModel):
    symbol: str
    signal_strength: float
    current_price: float
    volatility: float
    method: str = "volatility"


class StopLossRequest(BaseModel):
    entry_price: float
    volatility: float
    atr: Optional[float] = None
    method: str = "atr"


@router.post("/portfolio/optimize")
async def optimize_portfolio(
    request: OptimizePortfolioRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Optimize portfolio allocation using modern portfolio theory
    """
    try:
        # Convert returns to numpy array
        returns = np.array(request.returns)
        
        # Validate returns shape
        if returns.ndim != 2:
            raise HTTPException(400, "Returns must be a 2D array (assets x time)")
        
        # Create optimizer
        optimizer = PortfolioOptimizer(
            risk_free_rate=request.risk_free_rate,
            max_weight=request.max_weight,
            min_weight=request.min_weight
        )
        
        # Map method string to enum
        method_map = {
            "max_sharpe": OptimizationMethod.MAX_SHARPE,
            "min_variance": OptimizationMethod.MIN_VARIANCE,
            "risk_parity": OptimizationMethod.RISK_PARITY,
            "max_return": OptimizationMethod.MAX_RETURN,
            "efficient_frontier": OptimizationMethod.EFFICIENT_FRONTIER
        }
        
        method = method_map.get(request.method.lower())
        if method is None:
            raise HTTPException(400, f"Unknown optimization method: {request.method}")
        
        # Optimize
        constraints = {}
        if request.target_return is not None:
            constraints["target_return"] = request.target_return
        
        result = optimizer.optimize(returns, method, constraints)
        
        # Calculate diversification ratio
        div_ratio = optimizer.calculate_diversification_ratio(result.weights, returns)
        
        return {
            "success": True,
            "method": request.method,
            "weights": result.weights.tolist(),
            "expected_return": float(result.expected_return),
            "volatility": float(result.volatility),
            "sharpe_ratio": float(result.sharpe_ratio),
            "diversification_ratio": float(div_ratio),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Portfolio optimization error: {str(e)}")
        raise HTTPException(500, f"Optimization failed: {str(e)}")


@router.post("/portfolio/efficient-frontier")
async def calculate_efficient_frontier(
    request: OptimizePortfolioRequest,
    n_points: int = 50,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate efficient frontier for portfolio
    """
    try:
        returns = np.array(request.returns)
        
        optimizer = PortfolioOptimizer(
            risk_free_rate=request.risk_free_rate,
            max_weight=request.max_weight,
            min_weight=request.min_weight
        )
        
        frontier = optimizer.efficient_frontier(returns, n_points)
        
        return {
            "success": True,
            "n_points": len(frontier),
            "frontier": [
                {
                    "return": float(p.expected_return),
                    "volatility": float(p.volatility),
                    "sharpe_ratio": float(p.sharpe_ratio),
                    "weights": p.weights.tolist()
                }
                for p in frontier
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Efficient frontier error: {str(e)}")
        raise HTTPException(500, f"Calculation failed: {str(e)}")


@router.post("/risk/analyze")
async def analyze_risk(
    request: RiskAnalysisRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate comprehensive risk metrics
    """
    try:
        returns = np.array(request.returns)
        equity_curve = np.array(request.equity_curve) if request.equity_curve else None
        
        analyzer = RiskAnalyzer(risk_free_rate=request.risk_free_rate)
        metrics = analyzer.calculate_all_metrics(returns, equity_curve)
        
        return {
            "success": True,
            "metrics": format_risk_metrics(metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Risk analysis error: {str(e)}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.post("/strategy/optimize")
async def optimize_strategy(
    request: OptimizeStrategyRequest,
    db = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Optimize strategy parameters using ML
    """
    try:
        # Get example param space if strategy_id matches
        param_space = request.param_space
        if not param_space and request.strategy_id in EXAMPLE_PARAM_SPACES:
            param_space = EXAMPLE_PARAM_SPACES[request.strategy_id]
        
        if not param_space:
            raise HTTPException(400, "Parameter space required")
        
        # Create optimizer
        optimizer = StrategyOptimizer(
            objective_metric=request.objective_metric,
            n_trials=request.n_trials
        )
        
        strategy = StrategyDB.get(db, request.strategy_id)
        if not strategy:
            raise HTTPException(404, f"Strategy not found: {request.strategy_id}")

        base_strategy = {
            "id": strategy.id,
            "strategy_type": strategy.strategy_type,
            "parameters": strategy.parameters or {},
        }

        instruments = [base_strategy["parameters"].get("symbol", "SPY")]

        # Real backtest adapter
        def backtest_function(params, data):
            strategy_for_trial = {
                **base_strategy,
                "parameters": {
                    **base_strategy["parameters"],
                    **params,
                },
            }

            result = run_engine_backtest(
                strategy=strategy_for_trial,
                request_data={
                    "start_date": request.data_start,
                    "end_date": request.data_end,
                    "initial_capital": 100000.0,
                    "instruments": instruments,
                },
                run_replay_check=False,
            )

            return {
                "sharpe_ratio": float(result.metrics.get("sharpe_ratio", 0.0)),
                "total_return": float(result.metrics.get("total_return", 0.0)),
                "max_drawdown": float(result.metrics.get("max_drawdown", 0.0)),
            }
        
        # Placeholder data container used by optimizer callback signature.
        trial_data = np.array([])
        
        # Optimize
        result = optimizer.optimize(
            backtest_function,
            param_space,
            trial_data,
            study_name=f"{request.strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        return {
            "success": True,
            "strategy_id": request.strategy_id,
            "best_params": result.best_params,
            "best_value": float(result.best_value),
            "n_trials": result.n_trials,
            "optimization_time": float(result.optimization_time),
            "study_name": result.study_name,
            "history": result.optimization_history[:10],  # Return top 10
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Strategy optimization error: {str(e)}")
        raise HTTPException(500, f"Optimization failed: {str(e)}")


@router.post("/risk/position-size")
async def calculate_position_size(
    request: PositionSizeRequest,
    initial_capital: float = 100000,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate optimal position size
    """
    try:
        risk_manager = RiskManager(initial_capital)
        
        method_map = {
            "fixed": PositionSizeMethod.FIXED,
            "kelly": PositionSizeMethod.KELLY,
            "volatility": PositionSizeMethod.VOLATILITY,
            "max_loss": PositionSizeMethod.MAX_LOSS
        }
        
        method = method_map.get(request.method.lower(), PositionSizeMethod.VOLATILITY)
        
        size = risk_manager.calculate_position_size(
            request.symbol,
            request.signal_strength,
            request.current_price,
            request.volatility,
            method
        )
        
        position_value = size * request.current_price
        position_pct = position_value / initial_capital
        
        return {
            "success": True,
            "symbol": request.symbol,
            "position_size": float(size),
            "position_value": float(position_value),
            "position_pct": float(position_pct),
            "method": request.method,
            "current_price": request.current_price,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Position sizing error: {str(e)}")
        raise HTTPException(500, f"Calculation failed: {str(e)}")


@router.post("/risk/stop-loss")
async def calculate_stop_loss(
    request: StopLossRequest,
    risk_reward_ratio: float = 2.0,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate stop-loss and take-profit levels
    """
    try:
        risk_manager = RiskManager(100000)
        
        stop_loss = risk_manager.calculate_stop_loss(
            request.entry_price,
            request.volatility,
            request.atr,
            request.method
        )
        
        take_profit = risk_manager.calculate_take_profit(
            request.entry_price,
            stop_loss,
            risk_reward_ratio
        )
        
        risk_amount = request.entry_price - stop_loss
        risk_pct = risk_amount / request.entry_price
        reward_amount = take_profit - request.entry_price
        reward_pct = reward_amount / request.entry_price
        
        return {
            "success": True,
            "entry_price": request.entry_price,
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "risk_amount": float(risk_amount),
            "risk_pct": float(risk_pct),
            "reward_amount": float(reward_amount),
            "reward_pct": float(reward_pct),
            "risk_reward_ratio": float(reward_amount / risk_amount),
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Stop-loss calculation error: {str(e)}")
        raise HTTPException(500, f"Calculation failed: {str(e)}")


@router.get("/risk/limits")
async def get_risk_limits(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current risk limits configuration
    """
    limits = RiskLimits()
    
    return {
        "success": True,
        "limits": {
            "max_position_size": limits.max_position_size,
            "max_portfolio_leverage": limits.max_portfolio_leverage,
            "max_daily_loss": limits.max_daily_loss,
            "max_drawdown": limits.max_drawdown,
            "max_correlation": limits.max_correlation,
            "min_sharpe_ratio": limits.min_sharpe_ratio
        },
        "timestamp": datetime.now().isoformat()
    }


# Custom Indicators Endpoints

class CalculateIndicatorRequest(BaseModel):
    indicator_name: str
    data: Dict[str, List[float]]
    parameters: Dict[str, Any] = {}


@router.post("/indicators/calculate")
async def calculate_technical_indicator(
    request: CalculateIndicatorRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate a technical indicator
    """
    try:
        # Convert lists to numpy arrays
        data_arrays = {k: np.array(v) for k, v in request.data.items()}
        
        # Calculate indicator
        result = calculate_indicator(
            request.indicator_name,
            data_arrays,
            **request.parameters
        )
        
        # Convert back to lists
        result_lists = {k: v.tolist() for k, v in result.items()}
        
        return {
            "success": True,
            "indicator": request.indicator_name,
            "parameters": request.parameters,
            "result": result_lists,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Indicator calculation error: {str(e)}")
        raise HTTPException(500, f"Calculation failed: {str(e)}")


@router.get("/indicators/list")
async def list_indicators(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all available indicators
    """
    indicators = indicator_registry.list_indicators()
    
    return {
        "success": True,
        "indicators": indicators,
        "count": len(indicators),
        "timestamp": datetime.now().isoformat()
    }


# Multi-Asset Endpoints

class AssetRequest(BaseModel):
    symbol: str
    asset_class: str
    exchange: str
    currency: str
    contract_size: float = 1.0
    tick_size: float = 0.01


class OptionPricingRequest(BaseModel):
    spot: float
    strike: float
    time_to_expiry: float
    volatility: float
    risk_free_rate: float
    option_type: str = "call"


@router.post("/multi-asset/option-price")
async def calculate_option_price(
    request: OptionPricingRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate option price and Greeks using Black-Scholes
    """
    try:
        asset = AssetMetadata(
            symbol="OPTION",
            asset_class=AssetClass.OPTION,
            exchange="",
            currency="USD"
        )
        
        pricer = OptionPricer(asset)
        result = pricer.black_scholes(
            request.spot,
            request.strike,
            request.time_to_expiry,
            request.volatility,
            request.risk_free_rate,
            request.option_type
        )
        
        return {
            "success": True,
            "option_type": request.option_type,
            "spot": request.spot,
            "strike": request.strike,
            "result": {k: float(v) for k, v in result.items()},
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Option pricing error: {str(e)}")
        raise HTTPException(500, f"Calculation failed: {str(e)}")


class CorrelationRequest(BaseModel):
    returns: Dict[str, List[float]]


@router.post("/multi-asset/correlation")
async def calculate_correlation_matrix(
    request: CorrelationRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate correlation matrix across multiple assets
    """
    try:
        # Convert to numpy arrays
        returns_arrays = {k: np.array(v) for k, v in request.returns.items()}
        
        analyzer = CrossAssetAnalyzer([])
        corr_matrix = analyzer.calculate_correlation_matrix(returns_arrays)
        
        symbols = list(request.returns.keys())
        
        return {
            "success": True,
            "symbols": symbols,
            "correlation_matrix": corr_matrix.tolist(),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Correlation calculation error: {str(e)}")
        raise HTTPException(500, f"Calculation failed: {str(e)}")
