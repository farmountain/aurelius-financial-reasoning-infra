"""Tests for task generator."""

import pytest
from pydantic import ValidationError
from aureus.tasks.task_generator import (
    TaskType,
    Task,
    TaskGenerator,
)
from aureus.tasks.synthetic_generator import RegimeType, RegimeConfig


def test_task_creation():
    """Test creating a task."""
    data_config = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=100,
        seed=42,
    )
    
    task = Task(
        task_id="test_001",
        task_type=TaskType.DESIGN,
        goal="Design a trend strategy",
        regime=RegimeType.TREND,
        constraints={"max_drawdown": 0.25},
        data_config=data_config,
    )
    
    assert task.task_id == "test_001"
    assert task.task_type == TaskType.DESIGN
    assert task.goal == "Design a trend strategy"
    assert task.regime == RegimeType.TREND


def test_task_to_dict():
    """Test task serialization to dict."""
    data_config = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=100,
        seed=42,
    )
    
    task = Task(
        task_id="test_001",
        task_type=TaskType.DESIGN,
        goal="Design a trend strategy",
        regime=RegimeType.TREND,
        constraints={"max_drawdown": 0.25},
        data_config=data_config,
    )
    
    task_dict = task.to_dict()
    
    assert task_dict["task_id"] == "test_001"
    assert task_dict["task_type"] == "design"
    assert task_dict["goal"] == "Design a trend strategy"
    assert task_dict["regime"] == "trend"
    assert task_dict["constraints"]["max_drawdown"] == 0.25


def test_task_from_dict():
    """Test task deserialization from dict."""
    task_dict = {
        "task_id": "test_001",
        "task_type": "design",
        "goal": "Design a trend strategy",
        "regime": "trend",
        "constraints": {"max_drawdown": 0.25},
        "data_config": {
            "regime_type": "trend",
            "num_days": 100,
            "seed": 42,
            "initial_price": 100.0,
            "drift": 0.0005,
            "volatility": 0.02,
            "mean_reversion_strength": 0.1,
            "spike_frequency": 0.05,
            "spike_multiplier": 3.0,
        },
        "expected_outcome": None,
    }
    
    task = Task.from_dict(task_dict)
    
    assert task.task_id == "test_001"
    assert task.task_type == TaskType.DESIGN
    assert task.regime == RegimeType.TREND


def test_task_generator_design_task():
    """Test generating a design task."""
    generator = TaskGenerator(seed=42)
    
    task = generator.generate_design_task(
        regime=RegimeType.TREND,
        max_drawdown=0.25,
        num_days=252,
    )
    
    assert task.task_type == TaskType.DESIGN
    assert task.regime == RegimeType.TREND
    assert task.constraints["max_drawdown"] == 0.25
    assert "trend" in task.goal.lower()
    assert task.data_config.num_days == 252


def test_task_generator_design_task_with_sharpe():
    """Test generating a design task with Sharpe constraint."""
    generator = TaskGenerator(seed=42)
    
    task = generator.generate_design_task(
        regime=RegimeType.TREND,
        max_drawdown=0.20,
        min_sharpe=1.5,
        num_days=252,
    )
    
    assert task.constraints["max_drawdown"] == 0.20
    assert task.constraints["min_sharpe"] == 1.5
    assert "Sharpe" in task.goal


def test_task_generator_debug_task():
    """Test generating a debug task."""
    generator = TaskGenerator(seed=42)
    
    task = generator.generate_debug_task(
        regime=RegimeType.CHOP,
        issue="excessive drawdown",
        num_days=252,
    )
    
    assert task.task_type == TaskType.DEBUG
    assert task.regime == RegimeType.CHOP
    assert "excessive drawdown" in task.constraints["issue"]
    assert "debug" in task.goal.lower()


def test_task_generator_repair_task():
    """Test generating a repair task."""
    generator = TaskGenerator(seed=42)
    
    task = generator.generate_repair_task(
        regime=RegimeType.VOL_SPIKE,
        violation="max_drawdown_constraint",
        target_metric={"max_drawdown": 0.20},
        num_days=252,
    )
    
    assert task.task_type == TaskType.REPAIR
    assert task.regime == RegimeType.VOL_SPIKE
    assert task.constraints["violation"] == "max_drawdown_constraint"
    assert task.constraints["target_metric"]["max_drawdown"] == 0.20


def test_task_generator_optimize_task():
    """Test generating an optimize task."""
    generator = TaskGenerator(seed=42)
    
    task = generator.generate_optimize_task(
        regime=RegimeType.TREND,
        objective="sharpe_ratio",
        target_value=1.5,
        num_days=252,
    )
    
    assert task.task_type == TaskType.OPTIMIZE
    assert task.regime == RegimeType.TREND
    assert task.constraints["objective"] == "sharpe_ratio"
    assert task.constraints["target_value"] == 1.5


def test_task_generator_unique_ids():
    """Test that task generator creates unique IDs."""
    generator = TaskGenerator(seed=42)
    
    task1 = generator.generate_design_task(RegimeType.TREND)
    task2 = generator.generate_design_task(RegimeType.TREND)
    task3 = generator.generate_debug_task(RegimeType.CHOP, "issue")
    
    assert task1.task_id != task2.task_id
    assert task1.task_id != task3.task_id
    assert task2.task_id != task3.task_id


def test_task_generator_deterministic_config():
    """Test that task generator creates deterministic configs."""
    generator1 = TaskGenerator(seed=42)
    task1 = generator1.generate_design_task(RegimeType.TREND, num_days=100)
    
    generator2 = TaskGenerator(seed=42)
    task2 = generator2.generate_design_task(RegimeType.TREND, num_days=100)
    
    # Task IDs should match
    assert task1.task_id == task2.task_id
    # Data config seeds should match
    assert task1.data_config.seed == task2.data_config.seed


def test_task_generator_suite():
    """Test generating a complete task suite."""
    generator = TaskGenerator(seed=42)
    
    tasks = generator.generate_task_suite(
        regimes=[RegimeType.TREND, RegimeType.CHOP],
        num_days=100,
    )
    
    # Should generate multiple tasks per regime
    assert len(tasks) > 0
    
    # Should have tasks for both regimes
    trend_tasks = [t for t in tasks if t.regime == RegimeType.TREND]
    chop_tasks = [t for t in tasks if t.regime == RegimeType.CHOP]
    
    assert len(trend_tasks) > 0
    assert len(chop_tasks) > 0
    
    # Should have different task types
    task_types = set(t.task_type for t in tasks)
    assert len(task_types) > 1


def test_task_generator_suite_all_regimes():
    """Test generating suite for all regimes."""
    generator = TaskGenerator(seed=42)
    
    tasks = generator.generate_task_suite(num_days=100)
    
    # Should have tasks for all three regimes
    regimes = set(t.regime for t in tasks)
    assert RegimeType.TREND in regimes
    assert RegimeType.CHOP in regimes
    assert RegimeType.VOL_SPIKE in regimes


def test_task_schema_validation():
    """Test that task schema validation works."""
    data_config = RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=100,
        seed=42,
    )
    
    # Valid task should not raise
    task = Task(
        task_id="test_001",
        task_type=TaskType.DESIGN,
        goal="Test goal",
        regime=RegimeType.TREND,
        constraints={},
        data_config=data_config,
    )
    
    assert task is not None


def test_regime_specific_configs():
    """Test that different regimes get appropriate configs."""
    generator = TaskGenerator(seed=42)
    
    trend_task = generator.generate_design_task(RegimeType.TREND)
    chop_task = generator.generate_design_task(RegimeType.CHOP)
    vol_task = generator.generate_design_task(RegimeType.VOL_SPIKE)
    
    # Trend should have positive drift
    assert trend_task.data_config.drift > 0
    
    # Chop should have mean reversion
    assert chop_task.data_config.mean_reversion_strength > 0
    
    # Vol spike should have spike parameters
    assert vol_task.data_config.spike_frequency > 0
    assert vol_task.data_config.spike_multiplier > 1
