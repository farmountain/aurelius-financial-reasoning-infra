"""Tests for HipCortex storage integration."""

import pytest
import json
import tempfile
from pathlib import Path
from aureus.tasks.storage import (
    HipCortexStorage,
    TaskArtifact,
    GoldTrajectory,
    store_task_suite,
)
from aureus.tasks.task_generator import TaskGenerator
from aureus.tasks.synthetic_generator import RegimeType


def test_hipcortex_storage_initialization():
    """Test HipCortex storage initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir) / ".hipcortex"
        storage = HipCortexStorage(str(storage_dir))
        
        assert storage.storage_dir.exists()
        assert storage.tasks_dir.exists()
        assert storage.trajectories_dir.exists()


def test_task_artifact_to_json():
    """Test task artifact JSON serialization."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    artifact = TaskArtifact(task=task)
    json_str = artifact.to_json()
    
    assert isinstance(json_str, str)
    # Should be valid JSON
    data = json.loads(json_str)
    assert data["artifact_type"] == "task"
    assert "task" in data


def test_task_artifact_compute_hash():
    """Test task artifact hash computation."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    artifact1 = TaskArtifact(task=task)
    artifact2 = TaskArtifact(task=task)
    
    # Same task should produce same hash
    assert artifact1.compute_hash() == artifact2.compute_hash()


def test_task_artifact_different_tasks_different_hash():
    """Test that different tasks produce different hashes."""
    generator = TaskGenerator(seed=42)
    task1 = generator.generate_design_task(RegimeType.TREND)
    task2 = generator.generate_design_task(RegimeType.CHOP)
    
    artifact1 = TaskArtifact(task=task1)
    artifact2 = TaskArtifact(task=task2)
    
    assert artifact1.compute_hash() != artifact2.compute_hash()


def test_store_task():
    """Test storing a task."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        artifact_hash = storage.store_task(task)
        
        assert isinstance(artifact_hash, str)
        assert len(artifact_hash) == 64  # SHA256 hash length
        
        # Check that file was created
        artifact_path = storage.tasks_dir / f"{artifact_hash}.json"
        assert artifact_path.exists()


def test_store_task_creates_symlink():
    """Test that storing task creates symlink with task_id."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        storage.store_task(task)
        
        # Check that symlink was created
        task_link = storage.tasks_dir / f"{task.task_id}.json"
        assert task_link.exists()
        assert task_link.is_symlink()


def test_retrieve_task():
    """Test retrieving a stored task."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        storage.store_task(task)
        
        # Retrieve task
        retrieved_task = storage.retrieve_task(task.task_id)
        
        assert retrieved_task is not None
        assert retrieved_task.task_id == task.task_id
        assert retrieved_task.task_type == task.task_type
        assert retrieved_task.regime == task.regime


def test_retrieve_nonexistent_task():
    """Test retrieving a non-existent task returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        
        retrieved_task = storage.retrieve_task("nonexistent_task")
        assert retrieved_task is None


def test_gold_trajectory_to_json():
    """Test gold trajectory JSON serialization."""
    trajectory = GoldTrajectory(
        task_id="test_001",
        strategy_spec={"type": "ts_momentum", "lookback": 20},
        expected_metrics={"sharpe_ratio": 1.5, "max_drawdown": 0.15},
    )
    
    json_str = trajectory.to_json()
    
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["artifact_type"] == "gold_trajectory"
    assert data["task_id"] == "test_001"


def test_gold_trajectory_compute_hash():
    """Test gold trajectory hash computation."""
    trajectory1 = GoldTrajectory(
        task_id="test_001",
        strategy_spec={"type": "ts_momentum"},
        expected_metrics={"sharpe_ratio": 1.5},
    )
    
    trajectory2 = GoldTrajectory(
        task_id="test_001",
        strategy_spec={"type": "ts_momentum"},
        expected_metrics={"sharpe_ratio": 1.5},
    )
    
    # Same trajectory should produce same hash
    assert trajectory1.compute_hash() == trajectory2.compute_hash()


def test_store_gold_trajectory():
    """Test storing a gold trajectory."""
    trajectory = GoldTrajectory(
        task_id="test_001",
        strategy_spec={"type": "ts_momentum"},
        expected_metrics={"sharpe_ratio": 1.5},
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        artifact_hash = storage.store_gold_trajectory(trajectory)
        
        assert isinstance(artifact_hash, str)
        assert len(artifact_hash) == 64
        
        # Check that file was created
        artifact_path = storage.trajectories_dir / f"{artifact_hash}.json"
        assert artifact_path.exists()


def test_retrieve_gold_trajectory():
    """Test retrieving a stored gold trajectory."""
    trajectory = GoldTrajectory(
        task_id="test_001",
        strategy_spec={"type": "ts_momentum"},
        expected_metrics={"sharpe_ratio": 1.5},
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        storage.store_gold_trajectory(trajectory)
        
        # Retrieve trajectory
        retrieved = storage.retrieve_gold_trajectory("test_001")
        
        assert retrieved is not None
        assert retrieved.task_id == trajectory.task_id
        assert retrieved.strategy_spec == trajectory.strategy_spec
        assert retrieved.expected_metrics == trajectory.expected_metrics


def test_list_tasks():
    """Test listing stored tasks."""
    generator = TaskGenerator(seed=42)
    task1 = generator.generate_design_task(RegimeType.TREND)
    task2 = generator.generate_design_task(RegimeType.CHOP)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        storage.store_task(task1)
        storage.store_task(task2)
        
        task_ids = storage.list_tasks()
        
        assert len(task_ids) == 2
        assert task1.task_id in task_ids
        assert task2.task_id in task_ids
        # Should be sorted
        assert task_ids == sorted(task_ids)


def test_list_trajectories():
    """Test listing stored trajectories."""
    traj1 = GoldTrajectory(
        task_id="test_001",
        strategy_spec={},
        expected_metrics={},
    )
    traj2 = GoldTrajectory(
        task_id="test_002",
        strategy_spec={},
        expected_metrics={},
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        storage.store_gold_trajectory(traj1)
        storage.store_gold_trajectory(traj2)
        
        task_ids = storage.list_trajectories()
        
        assert len(task_ids) == 2
        assert "test_001" in task_ids
        assert "test_002" in task_ids


def test_store_task_suite():
    """Test storing a task suite."""
    generator = TaskGenerator(seed=42)
    tasks = [
        generator.generate_design_task(RegimeType.TREND),
        generator.generate_design_task(RegimeType.CHOP),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        task_hashes = store_task_suite(tasks, storage_dir=tmpdir)
        
        assert len(task_hashes) == 2
        assert tasks[0].task_id in task_hashes
        assert tasks[1].task_id in task_hashes
        
        # Verify tasks can be retrieved
        storage = HipCortexStorage(tmpdir)
        for task in tasks:
            retrieved = storage.retrieve_task(task.task_id)
            assert retrieved is not None


def test_task_artifact_with_metadata():
    """Test task artifact with metadata."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    metadata = {
        "author": "test",
        "timestamp": "2024-01-01",
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = HipCortexStorage(tmpdir)
        storage.store_task(task, metadata=metadata)
        
        # Retrieve and check metadata is stored
        artifact_path = storage.tasks_dir / f"{task.task_id}.json"
        with open(artifact_path.resolve(), "r") as f:
            data = json.load(f)
        
        assert data["metadata"] == metadata


def test_storage_determinism():
    """Test that storage produces deterministic hashes."""
    generator = TaskGenerator(seed=42)
    task = generator.generate_design_task(RegimeType.TREND)
    
    with tempfile.TemporaryDirectory() as tmpdir1:
        storage1 = HipCortexStorage(tmpdir1)
        hash1 = storage1.store_task(task)
    
    with tempfile.TemporaryDirectory() as tmpdir2:
        storage2 = HipCortexStorage(tmpdir2)
        hash2 = storage2.store_task(task)
    
    # Same task should produce same hash across different storage instances
    assert hash1 == hash2
