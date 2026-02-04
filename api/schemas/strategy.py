"""Schema definitions for strategy endpoints."""
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class StrategyType(str, Enum):
    """Supported strategy types."""
    MOMENTUM = "ts_momentum"
    PAIRS_TRADING = "pairs_trading"
    STAT_ARB = "stat_arb"
    ML_CLASSIFIER = "ml_classifier"
    VOLATILITY_TRADING = "volatility_trading"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    MARKET_NEUTRAL = "market_neutral"


class RiskPreference(str, Enum):
    """Risk preference levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class StrategyGenerationRequest(BaseModel):
    """Request to generate a strategy from natural language."""
    goal: str = Field(
        ...,
        description="Natural language description of trading goal"
    )
    risk_preference: RiskPreference = Field(
        default=RiskPreference.MODERATE,
        description="Risk preference level"
    )
    max_strategies: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of strategies to generate"
    )


class StrategyParameters(BaseModel):
    """Parameters generated for a strategy."""
    lookback: int = Field(..., description="Lookback period in days")
    vol_target: float = Field(..., description="Volatility target")
    position_size: float = Field(..., description="Position size percentage")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss percentage")
    take_profit: Optional[float] = Field(default=None, description="Take profit percentage")


class GeneratedStrategy(BaseModel):
    """A generated strategy with its parameters."""
    id: str = Field(..., description="Unique strategy identifier")
    strategy_type: StrategyType = Field(..., description="Type of strategy")
    name: str = Field(..., description="Human-readable strategy name")
    description: str = Field(..., description="Strategy description")
    parameters: StrategyParameters = Field(..., description="Strategy parameters")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this strategy"
    )


class StrategyGenerationResponse(BaseModel):
    """Response from strategy generation."""
    request_id: str = Field(..., description="Unique request ID")
    strategies: list[GeneratedStrategy] = Field(..., description="Generated strategies")
    generation_time_ms: float = Field(..., description="Time taken to generate in milliseconds")


class StrategyListResponse(BaseModel):
    """Response with list of strategies."""
    total: int = Field(..., description="Total number of strategies")
    strategies: list[GeneratedStrategy] = Field(..., description="List of strategies")


class StrategyDetailResponse(BaseModel):
    """Detailed response for a single strategy."""
    strategy_id: str = Field(..., description="Unique strategy identifier")
    strategy: GeneratedStrategy = Field(..., description="Strategy details")
    created_at: str = Field(..., description="Creation timestamp")
    status: str = Field(default="active", description="Strategy status")
