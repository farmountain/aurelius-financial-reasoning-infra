"""Benchmark runner for evaluating task performance."""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from aureus.tasks.task_generator import Task
from aureus.tasks.synthetic_generator import SyntheticRegimeGenerator


class TaskResult(BaseModel):
    """Result of executing a single task."""
    
    task_id: str = Field(..., description="Task identifier")
    passed: bool = Field(..., description="Whether task passed")
    crv_passed: bool = Field(..., description="Whether CRV checks passed")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="CRV violations")
    error: Optional[str] = Field(None, description="Error message if failed")


class BenchmarkResults(BaseModel):
    """Aggregated results from benchmark suite."""
    
    total_tasks: int = Field(..., description="Total number of tasks")
    passed_tasks: int = Field(..., description="Number of tasks passed")
    crv_passed_tasks: int = Field(..., description="Number of tasks with CRV passed")
    pass_rate: float = Field(..., description="Overall pass rate")
    crv_pass_rate: float = Field(..., description="CRV pass rate")
    robustness_score: float = Field(..., description="Robustness metric")
    task_results: List[TaskResult] = Field(default_factory=list, description="Individual task results")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "crv_passed_tasks": self.crv_passed_tasks,
            "pass_rate": self.pass_rate,
            "crv_pass_rate": self.crv_pass_rate,
            "robustness_score": self.robustness_score,
            "task_results": [r.model_dump() for r in self.task_results],
        }


class BenchmarkRunner:
    """Run benchmark tasks and aggregate results."""
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        strict_mode: bool = False,
    ):
        """Initialize benchmark runner.
        
        Args:
            output_dir: Directory for benchmark outputs (uses temp if None)
            strict_mode: Whether to enforce strict mode
        """
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="benchmark_")
        self.strict_mode = strict_mode
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def run_task(self, task: Task) -> TaskResult:
        """Run a single benchmark task.
        
        Args:
            task: Task to execute
        
        Returns:
            Task result
        """
        try:
            # Generate synthetic data
            generator = SyntheticRegimeGenerator(task.data_config)
            data = generator.generate()
            
            # Save data to temp file
            task_dir = Path(self.output_dir) / task.task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            data_path = task_dir / "data.parquet"
            data.to_parquet(data_path, index=False)
            
            # For now, mock task execution
            # In a real implementation, this would call the orchestrator
            # to generate strategy, run backtest, and verify CRV
            
            # Mock metrics
            metrics = self._mock_task_execution(task, data)
            
            # Check if task passed based on constraints
            passed = self._check_constraints(task, metrics)
            
            # Mock CRV verification
            crv_passed, violations = self._mock_crv_check(task, metrics)
            
            return TaskResult(
                task_id=task.task_id,
                passed=passed,
                crv_passed=crv_passed,
                metrics=metrics,
                violations=violations,
            )
        
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                passed=False,
                crv_passed=False,
                metrics={},
                violations=[],
                error=str(e),
            )
    
    def run_suite(self, tasks: List[Task]) -> BenchmarkResults:
        """Run a suite of benchmark tasks.
        
        Args:
            tasks: List of tasks to execute
        
        Returns:
            Aggregated benchmark results
        """
        task_results = []
        
        for task in tasks:
            result = self.run_task(task)
            task_results.append(result)
        
        # Calculate aggregate metrics
        total_tasks = len(task_results)
        passed_tasks = sum(1 for r in task_results if r.passed)
        crv_passed_tasks = sum(1 for r in task_results if r.crv_passed)
        
        pass_rate = passed_tasks / total_tasks if total_tasks > 0 else 0.0
        crv_pass_rate = crv_passed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # Calculate robustness score (combination of pass rate and CRV compliance)
        robustness_score = (pass_rate + crv_pass_rate) / 2.0
        
        results = BenchmarkResults(
            total_tasks=total_tasks,
            passed_tasks=passed_tasks,
            crv_passed_tasks=crv_passed_tasks,
            pass_rate=pass_rate,
            crv_pass_rate=crv_pass_rate,
            robustness_score=robustness_score,
            task_results=task_results,
        )
        
        # Save results
        results_path = Path(self.output_dir) / "benchmark_results.json"
        with open(results_path, "w") as f:
            json.dump(results.to_dict(), f, indent=2)
        
        return results
    
    def _mock_task_execution(self, task: Task, data) -> Dict[str, float]:
        """Mock task execution for testing.
        
        In production, this would call the actual orchestrator.
        
        Args:
            task: Task to execute
            data: Market data
        
        Returns:
            Performance metrics
        """
        # Return mock metrics based on regime
        if task.regime.value == "trend":
            return {
                "total_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.18,
                "num_trades": 25,
            }
        elif task.regime.value == "chop":
            return {
                "total_return": 0.05,
                "sharpe_ratio": 0.6,
                "max_drawdown": 0.12,
                "num_trades": 45,
            }
        else:  # vol_spike
            return {
                "total_return": 0.08,
                "sharpe_ratio": 0.8,
                "max_drawdown": 0.22,
                "num_trades": 30,
            }
    
    def _check_constraints(self, task: Task, metrics: Dict[str, float]) -> bool:
        """Check if task constraints are satisfied.
        
        Args:
            task: Task with constraints
            metrics: Performance metrics
        
        Returns:
            True if all constraints satisfied
        """
        constraints = task.constraints
        
        if "max_drawdown" in constraints:
            if metrics.get("max_drawdown", 1.0) > constraints["max_drawdown"]:
                return False
        
        if "min_sharpe" in constraints:
            if metrics.get("sharpe_ratio", 0.0) < constraints["min_sharpe"]:
                return False
        
        return True
    
    def _mock_crv_check(self, task: Task, metrics: Dict[str, float]) -> tuple:
        """Mock CRV verification.
        
        Args:
            task: Task to verify
            metrics: Performance metrics
        
        Returns:
            Tuple of (passed, violations)
        """
        violations = []
        
        # Check for max drawdown violation
        max_dd_limit = task.constraints.get("max_drawdown", 0.25)
        if metrics.get("max_drawdown", 0.0) > max_dd_limit * 1.1:  # 10% tolerance
            violations.append({
                "rule_id": "max_drawdown_constraint",
                "severity": "high",
                "message": f"Max drawdown {metrics['max_drawdown']:.2%} exceeds limit {max_dd_limit:.2%}",
            })
        
        # Check for negative Sharpe
        if metrics.get("sharpe_ratio", 0.0) < 0:
            violations.append({
                "rule_id": "negative_sharpe",
                "severity": "medium",
                "message": "Negative Sharpe ratio detected",
            })
        
        passed = len(violations) == 0
        return passed, violations
