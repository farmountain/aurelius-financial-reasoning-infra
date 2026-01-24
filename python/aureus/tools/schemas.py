"""JSON schemas and Pydantic models for tool validation."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class ToolType(str, Enum):
    """Available tool types."""
    
    BACKTEST = "backtest"
    CRV_VERIFY = "crv_verify"
    HIPCORTEX_COMMIT = "hipcortex_commit"
    HIPCORTEX_SEARCH = "hipcortex_search"
    HIPCORTEX_SHOW = "hipcortex_show"
    GENERATE_STRATEGY = "generate_strategy"
    RUN_TESTS = "run_tests"
    CHECK_DETERMINISM = "check_determinism"
    LINT = "lint"


class StrategyConfig(BaseModel):
    """Strategy configuration schema."""
    
    type: str = Field(..., description="Strategy type (e.g., 'ts_momentum')")
    symbol: str = Field(..., description="Trading symbol")
    lookback: int = Field(20, ge=1, description="Lookback period")
    vol_target: float = Field(0.15, gt=0, le=1, description="Volatility target")
    vol_lookback: int = Field(20, ge=1, description="Volatility lookback period")


class CostModelConfig(BaseModel):
    """Cost model configuration schema."""
    
    type: str = Field(..., description="Cost model type")
    cost_per_share: Optional[float] = Field(None, ge=0)
    minimum_commission: Optional[float] = Field(None, ge=0)
    percentage: Optional[float] = Field(None, ge=0, le=1)


class BacktestSpec(BaseModel):
    """Backtest specification schema."""
    
    initial_cash: float = Field(100000.0, gt=0, description="Initial cash")
    seed: int = Field(42, description="Random seed for determinism")
    strategy: StrategyConfig
    cost_model: CostModelConfig


class BacktestToolInput(BaseModel):
    """Input schema for backtest tool."""
    
    spec: BacktestSpec
    data_path: str = Field(..., description="Path to data parquet file")
    output_dir: str = Field(..., description="Output directory for results")


class CRVVerifyToolInput(BaseModel):
    """Input schema for CRV verification tool."""
    
    stats_path: str = Field(..., description="Path to stats.json")
    trades_path: str = Field(..., description="Path to trades.csv")
    equity_path: str = Field(..., description="Path to equity_curve.csv")
    max_drawdown_limit: float = Field(0.25, gt=0, le=1, description="Max drawdown limit")


class HipcortexCommitInput(BaseModel):
    """Input schema for hipcortex commit tool."""
    
    artifact_path: str = Field(..., description="Path to artifact file")
    message: str = Field(..., description="Commit message")
    goal: Optional[str] = Field(None, description="Goal tag")
    regime_tags: Optional[List[str]] = Field(None, description="Regime tags")


class HipcortexSearchInput(BaseModel):
    """Input schema for hipcortex search tool."""
    
    goal: Optional[str] = Field(None, description="Goal keyword")
    tag: Optional[str] = Field(None, description="Tag filter")
    limit: int = Field(10, ge=1, le=100, description="Result limit")


class ToolCall(BaseModel):
    """Tool call with validated parameters."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    tool_type: ToolType
    parameters: Union[
        BacktestToolInput,
        CRVVerifyToolInput,
        HipcortexCommitInput,
        HipcortexSearchInput,
        Dict[str, Any],
    ]


class ToolResult(BaseModel):
    """Tool execution result."""
    
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    artifact_id: Optional[str] = Field(None, description="Artifact ID if applicable")
    
    def __str__(self) -> str:
        if self.success:
            return f"Success: {self.output}"
        return f"Error: {self.error}"
