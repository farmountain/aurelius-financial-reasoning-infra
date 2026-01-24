"""Tests for benchmark runner."""

import pytest
import tempfile
from pathlib import Path
from aureus.tasks.benchmark import (
    BenchmarkRunner,
    BenchmarkResults,
    TaskResult,
)
from aureus.tasks.task_generator import TaskGenerator
from aureus.tasks.synthetic_generator import RegimeType


def test_benchmark_runner_initialization():
    """Test benchmark runner initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        
        assert runner.output_dir == tmpdir
        assert Path(tmpdir).exists()


def test_benchmark_runner_run_task():
    """Test running a single task."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND, max_drawdown=0.25)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        result = runner.run_task(task)
        
        assert isinstance(result, TaskResult)
        assert result.task_id == task.task_id
        assert isinstance(result.passed, bool)
        assert isinstance(result.crv_passed, bool)
        assert isinstance(result.metrics, dict)


def test_benchmark_runner_task_creates_data():
    """Test that running a task generates data file."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        result = runner.run_task(task)
        
        # Check that data file was created
        data_path = Path(tmpdir) / task.task_id / "data.parquet"
        assert data_path.exists()


def test_benchmark_runner_suite():
    """Test running a benchmark suite."""
    generator = TaskGenerator(seed=42)
    tasks = [
        generator.generate_design_task(RegimeType.TREND),
        generator.generate_design_task(RegimeType.CHOP),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        results = runner.run_suite(tasks)
        
        assert isinstance(results, BenchmarkResults)
        assert results.total_tasks == 2
        assert len(results.task_results) == 2


def test_benchmark_results_metrics():
    """Test benchmark results metrics calculation."""
    generator = TaskGenerator(seed=42)
    tasks = [
        generator.generate_design_task(RegimeType.TREND),
        generator.generate_design_task(RegimeType.CHOP),
        generator.generate_design_task(RegimeType.VOL_SPIKE),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        results = runner.run_suite(tasks)
        
        assert results.total_tasks == 3
        assert 0.0 <= results.pass_rate <= 1.0
        assert 0.0 <= results.crv_pass_rate <= 1.0
        assert 0.0 <= results.robustness_score <= 1.0


def test_benchmark_results_saves_json():
    """Test that benchmark results are saved to JSON."""
    generator = TaskGenerator(seed=42)
    tasks = [generator.generate_design_task(RegimeType.TREND)]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        results = runner.run_suite(tasks)
        
        # Check that results file was created
        results_path = Path(tmpdir) / "benchmark_results.json"
        assert results_path.exists()


def test_benchmark_results_to_dict():
    """Test benchmark results serialization."""
    generator = TaskGenerator(seed=42)
    tasks = [generator.generate_design_task(RegimeType.TREND)]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        results = runner.run_suite(tasks)
        
        results_dict = results.to_dict()
        
        assert "total_tasks" in results_dict
        assert "pass_rate" in results_dict
        assert "crv_pass_rate" in results_dict
        assert "robustness_score" in results_dict
        assert "task_results" in results_dict


def test_benchmark_runner_deterministic():
    """Test that benchmark runner produces stable results with same seed."""
    generator1 = TaskGenerator(seed=42)
    tasks1 = [generator1.generate_design_task(RegimeType.TREND)]
    
    generator2 = TaskGenerator(seed=42)
    tasks2 = [generator2.generate_design_task(RegimeType.TREND)]
    
    with tempfile.TemporaryDirectory() as tmpdir1:
        runner1 = BenchmarkRunner(output_dir=tmpdir1)
        results1 = runner1.run_suite(tasks1)
    
    with tempfile.TemporaryDirectory() as tmpdir2:
        runner2 = BenchmarkRunner(output_dir=tmpdir2)
        results2 = runner2.run_suite(tasks2)
    
    # Results should be identical
    assert results1.total_tasks == results2.total_tasks
    assert results1.pass_rate == results2.pass_rate
    assert results1.crv_pass_rate == results2.crv_pass_rate
    assert results1.robustness_score == results2.robustness_score


def test_benchmark_runner_multiple_runs_stable():
    """Test that multiple benchmark runs produce consistent results."""
    generator = TaskGenerator(seed=42)
    tasks = [generator.generate_design_task(RegimeType.TREND)]
    
    results_list = []
    
    for _ in range(3):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = BenchmarkRunner(output_dir=tmpdir)
            results = runner.run_suite(tasks)
            results_list.append(results)
    
    # All runs should produce same metrics
    for i in range(1, len(results_list)):
        assert results_list[i].pass_rate == results_list[0].pass_rate
        assert results_list[i].crv_pass_rate == results_list[0].crv_pass_rate
        assert results_list[i].robustness_score == results_list[0].robustness_score


def test_task_result_with_error():
    """Test task result with error."""
    result = TaskResult(
        task_id="test_001",
        passed=False,
        crv_passed=False,
        metrics={},
        violations=[],
        error="Test error",
    )
    
    assert result.task_id == "test_001"
    assert not result.passed
    assert not result.crv_passed
    assert result.error == "Test error"


def test_task_result_with_violations():
    """Test task result with CRV violations."""
    violations = [
        {
            "rule_id": "max_drawdown_constraint",
            "severity": "high",
            "message": "Max drawdown exceeded",
        }
    ]
    
    result = TaskResult(
        task_id="test_001",
        passed=False,
        crv_passed=False,
        metrics={"max_drawdown": 0.30},
        violations=violations,
    )
    
    assert len(result.violations) == 1
    assert result.violations[0]["rule_id"] == "max_drawdown_constraint"


def test_benchmark_runner_constraint_checking():
    """Test that constraint checking works correctly."""
    generator = TaskGenerator(seed=42)
    
    # Task with tight constraint
    task = generator.generate_design_task(
        RegimeType.TREND,
        max_drawdown=0.10,  # Very tight constraint
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        result = runner.run_task(task)
        
        # Task should have metrics
        assert "max_drawdown" in result.metrics


def test_robustness_score_calculation():
    """Test robustness score is average of pass rates."""
    generator = TaskGenerator(seed=42)
    tasks = [generator.generate_design_task(RegimeType.TREND)]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        results = runner.run_suite(tasks)
        
        # Robustness should be average of pass_rate and crv_pass_rate
        expected_robustness = (results.pass_rate + results.crv_pass_rate) / 2.0
        assert abs(results.robustness_score - expected_robustness) < 1e-6


def test_benchmark_results_all_fields():
    """Test that benchmark results have all required fields."""
    generator = TaskGenerator(seed=42)
    tasks = [generator.generate_design_task(RegimeType.TREND)]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(output_dir=tmpdir)
        results = runner.run_suite(tasks)
        
        # Check all required fields
        assert hasattr(results, "total_tasks")
        assert hasattr(results, "passed_tasks")
        assert hasattr(results, "crv_passed_tasks")
        assert hasattr(results, "pass_rate")
        assert hasattr(results, "crv_pass_rate")
        assert hasattr(results, "robustness_score")
        assert hasattr(results, "task_results")
