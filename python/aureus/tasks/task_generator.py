"""Task generator for creating benchmark tasks."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from aureus.tasks.synthetic_generator import RegimeType, RegimeConfig


class TaskType(str, Enum):
    """Types of tasks for benchmarking."""
    
    DESIGN = "design"
    DEBUG = "debug"
    REPAIR = "repair"
    OPTIMIZE = "optimize"


class Task(BaseModel):
    """A benchmark task with goal and constraints."""
    
    task_id: str = Field(..., description="Unique task identifier")
    task_type: TaskType = Field(..., description="Type of task")
    goal: str = Field(..., description="Task goal description")
    regime: RegimeType = Field(..., description="Market regime")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Task constraints")
    data_config: RegimeConfig = Field(..., description="Data generation configuration")
    expected_outcome: Optional[Dict[str, Any]] = Field(None, description="Expected outcome (gold trajectory)")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "goal": self.goal,
            "regime": self.regime.value,
            "constraints": self.constraints,
            "data_config": self.data_config.model_dump(),
            "expected_outcome": self.expected_outcome,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary.
        
        Args:
            data: Task dictionary
        
        Returns:
            Task instance
        """
        data_config = RegimeConfig(**data["data_config"])
        return cls(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            goal=data["goal"],
            regime=RegimeType(data["regime"]),
            constraints=data.get("constraints", {}),
            data_config=data_config,
            expected_outcome=data.get("expected_outcome"),
        )


class TaskGenerator:
    """Generate benchmark tasks for different regimes and task types."""
    
    def __init__(self, seed: int = 42):
        """Initialize task generator.
        
        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        self.task_counter = 0
    
    def generate_design_task(
        self,
        regime: RegimeType,
        max_drawdown: float = 0.25,
        min_sharpe: Optional[float] = None,
        num_days: int = 252,
    ) -> Task:
        """Generate a strategy design task.
        
        Args:
            regime: Market regime
            max_drawdown: Maximum drawdown constraint
            min_sharpe: Minimum Sharpe ratio (optional)
            num_days: Number of trading days
        
        Returns:
            Design task
        """
        self.task_counter += 1
        task_id = f"design_{regime.value}_{self.task_counter:03d}"
        
        # Build goal and constraints
        goal = f"Design a {regime.value} strategy"
        constraints = {"max_drawdown": max_drawdown}
        
        if min_sharpe is not None:
            goal += f" with Sharpe > {min_sharpe}"
            constraints["min_sharpe"] = min_sharpe
        
        goal += f" under DD < {max_drawdown * 100}%"
        
        # Configure data generation
        data_config = self._get_regime_config(regime, num_days)
        
        return Task(
            task_id=task_id,
            task_type=TaskType.DESIGN,
            goal=goal,
            regime=regime,
            constraints=constraints,
            data_config=data_config,
        )
    
    def generate_debug_task(
        self,
        regime: RegimeType,
        issue: str,
        num_days: int = 252,
    ) -> Task:
        """Generate a strategy debug task.
        
        Args:
            regime: Market regime
            issue: Description of the issue to debug
            num_days: Number of trading days
        
        Returns:
            Debug task
        """
        self.task_counter += 1
        task_id = f"debug_{regime.value}_{self.task_counter:03d}"
        
        goal = f"Debug {regime.value} strategy: {issue}"
        constraints = {"issue": issue}
        
        data_config = self._get_regime_config(regime, num_days)
        
        return Task(
            task_id=task_id,
            task_type=TaskType.DEBUG,
            goal=goal,
            regime=regime,
            constraints=constraints,
            data_config=data_config,
        )
    
    def generate_repair_task(
        self,
        regime: RegimeType,
        violation: str,
        target_metric: Dict[str, float],
        num_days: int = 252,
    ) -> Task:
        """Generate a strategy repair task.
        
        Args:
            regime: Market regime
            violation: Description of the CRV violation
            target_metric: Target metric to fix (e.g., {"max_drawdown": 0.20})
            num_days: Number of trading days
        
        Returns:
            Repair task
        """
        self.task_counter += 1
        task_id = f"repair_{regime.value}_{self.task_counter:03d}"
        
        goal = f"Repair {regime.value} strategy: fix {violation}"
        constraints = {"violation": violation, "target_metric": target_metric}
        
        data_config = self._get_regime_config(regime, num_days)
        
        return Task(
            task_id=task_id,
            task_type=TaskType.REPAIR,
            goal=goal,
            regime=regime,
            constraints=constraints,
            data_config=data_config,
        )
    
    def generate_optimize_task(
        self,
        regime: RegimeType,
        objective: str,
        target_value: float,
        num_days: int = 252,
    ) -> Task:
        """Generate a strategy optimization task.
        
        Args:
            regime: Market regime
            objective: Optimization objective (e.g., "sharpe_ratio", "calmar_ratio")
            target_value: Target value for the objective
            num_days: Number of trading days
        
        Returns:
            Optimize task
        """
        self.task_counter += 1
        task_id = f"optimize_{regime.value}_{self.task_counter:03d}"
        
        goal = f"Optimize {regime.value} strategy for {objective} > {target_value}"
        constraints = {"objective": objective, "target_value": target_value}
        
        data_config = self._get_regime_config(regime, num_days)
        
        return Task(
            task_id=task_id,
            task_type=TaskType.OPTIMIZE,
            goal=goal,
            regime=regime,
            constraints=constraints,
            data_config=data_config,
        )
    
    def generate_task_suite(
        self,
        regimes: Optional[List[RegimeType]] = None,
        num_days: int = 252,
    ) -> List[Task]:
        """Generate a comprehensive task suite across regimes.
        
        Args:
            regimes: List of regimes (defaults to all)
            num_days: Number of trading days
        
        Returns:
            List of tasks
        """
        if regimes is None:
            regimes = [RegimeType.TREND, RegimeType.CHOP, RegimeType.VOL_SPIKE]
        
        tasks = []
        
        for regime in regimes:
            # Design tasks
            tasks.append(self.generate_design_task(regime, max_drawdown=0.25, num_days=num_days))
            tasks.append(self.generate_design_task(regime, max_drawdown=0.15, min_sharpe=1.0, num_days=num_days))
            
            # Debug tasks
            tasks.append(self.generate_debug_task(regime, "excessive drawdown", num_days=num_days))
            
            # Repair tasks
            tasks.append(self.generate_repair_task(
                regime,
                "max_drawdown_constraint",
                {"max_drawdown": 0.20},
                num_days=num_days
            ))
            
            # Optimize tasks
            tasks.append(self.generate_optimize_task(regime, "sharpe_ratio", 1.5, num_days=num_days))
        
        return tasks
    
    def _get_regime_config(self, regime: RegimeType, num_days: int) -> RegimeConfig:
        """Get configuration for a specific regime.
        
        Args:
            regime: Market regime type
            num_days: Number of trading days
        
        Returns:
            Regime configuration
        """
        base_seed = self.seed + self.task_counter
        
        if regime == RegimeType.TREND:
            return RegimeConfig(
                regime_type=regime,
                num_days=num_days,
                seed=base_seed,
                drift=0.001,  # Positive trend
                volatility=0.015,
            )
        elif regime == RegimeType.CHOP:
            return RegimeConfig(
                regime_type=regime,
                num_days=num_days,
                seed=base_seed,
                drift=0.0,
                volatility=0.02,
                mean_reversion_strength=0.2,
            )
        elif regime == RegimeType.VOL_SPIKE:
            return RegimeConfig(
                regime_type=regime,
                num_days=num_days,
                seed=base_seed,
                drift=0.0,
                volatility=0.015,
                spike_frequency=0.05,
                spike_multiplier=3.0,
            )
        else:
            raise ValueError(f"Unknown regime: {regime}")
