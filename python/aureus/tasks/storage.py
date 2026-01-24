"""HipCortex integration for storing tasks and gold trajectories."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from aureus.tasks.task_generator import Task


class ArtifactType(str):
    """Types of artifacts stored in HipCortex."""
    
    TASK = "task"
    GOLD_TRAJECTORY = "gold_trajectory"
    BENCHMARK_RESULT = "benchmark_result"


class TaskArtifact(BaseModel):
    """Task artifact for storage."""
    
    artifact_type: str = Field(default=ArtifactType.TASK, description="Artifact type")
    task: Task = Field(..., description="Task definition")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def to_json(self) -> str:
        """Convert to JSON string.
        
        Returns:
            JSON representation
        """
        data = {
            "artifact_type": self.artifact_type,
            "task": self.task.to_dict(),
            "metadata": self.metadata,
        }
        return json.dumps(data, sort_keys=True, indent=2)
    
    def compute_hash(self) -> str:
        """Compute content hash.
        
        Returns:
            SHA256 hash of canonical JSON
        """
        canonical = self.to_json()
        return hashlib.sha256(canonical.encode()).hexdigest()


class GoldTrajectory(BaseModel):
    """Gold trajectory (expected solution) for a task."""
    
    artifact_type: str = Field(default=ArtifactType.GOLD_TRAJECTORY, description="Artifact type")
    task_id: str = Field(..., description="Associated task ID")
    strategy_spec: Dict[str, Any] = Field(..., description="Strategy specification")
    expected_metrics: Dict[str, float] = Field(..., description="Expected performance metrics")
    crv_report: Optional[Dict[str, Any]] = Field(None, description="Expected CRV report")
    
    def to_json(self) -> str:
        """Convert to JSON string.
        
        Returns:
            JSON representation
        """
        data = {
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "strategy_spec": self.strategy_spec,
            "expected_metrics": self.expected_metrics,
            "crv_report": self.crv_report,
        }
        return json.dumps(data, sort_keys=True, indent=2)
    
    def compute_hash(self) -> str:
        """Compute content hash.
        
        Returns:
            SHA256 hash of canonical JSON
        """
        canonical = self.to_json()
        return hashlib.sha256(canonical.encode()).hexdigest()


class HipCortexStorage:
    """Storage interface for tasks and gold trajectories."""
    
    def __init__(self, storage_dir: str = ".hipcortex"):
        """Initialize storage.
        
        Args:
            storage_dir: Directory for artifact storage
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir = self.storage_dir / "tasks"
        self.trajectories_dir = self.storage_dir / "trajectories"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.trajectories_dir.mkdir(parents=True, exist_ok=True)
    
    def store_task(self, task: Task, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a task artifact.
        
        Args:
            task: Task to store
            metadata: Additional metadata
        
        Returns:
            Artifact hash
        """
        artifact = TaskArtifact(
            task=task,
            metadata=metadata or {},
        )
        
        artifact_hash = artifact.compute_hash()
        artifact_path = self.tasks_dir / f"{artifact_hash}.json"
        
        with open(artifact_path, "w") as f:
            f.write(artifact.to_json())
        
        # Also create a symlink with task_id for easy lookup
        task_link = self.tasks_dir / f"{task.task_id}.json"
        if task_link.exists():
            task_link.unlink()
        task_link.symlink_to(artifact_path.name)
        
        return artifact_hash
    
    def store_gold_trajectory(self, trajectory: GoldTrajectory) -> str:
        """Store a gold trajectory artifact.
        
        Args:
            trajectory: Gold trajectory to store
        
        Returns:
            Artifact hash
        """
        artifact_hash = trajectory.compute_hash()
        artifact_path = self.trajectories_dir / f"{artifact_hash}.json"
        
        with open(artifact_path, "w") as f:
            f.write(trajectory.to_json())
        
        # Also create a symlink with task_id for easy lookup
        traj_link = self.trajectories_dir / f"{trajectory.task_id}.json"
        if traj_link.exists():
            traj_link.unlink()
        traj_link.symlink_to(artifact_path.name)
        
        return artifact_hash
    
    def retrieve_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task if found, None otherwise
        """
        task_link = self.tasks_dir / f"{task_id}.json"
        if not task_link.exists():
            return None
        
        with open(task_link, "r") as f:
            data = json.load(f)
        
        return Task.from_dict(data["task"])
    
    def retrieve_gold_trajectory(self, task_id: str) -> Optional[GoldTrajectory]:
        """Retrieve a gold trajectory by task ID.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Gold trajectory if found, None otherwise
        """
        traj_link = self.trajectories_dir / f"{task_id}.json"
        if not traj_link.exists():
            return None
        
        with open(traj_link, "r") as f:
            data = json.load(f)
        
        return GoldTrajectory(**data)
    
    def list_tasks(self) -> List[str]:
        """List all stored task IDs.
        
        Returns:
            List of task IDs
        """
        task_ids = []
        for path in self.tasks_dir.glob("*.json"):
            if not path.is_symlink():
                continue
            # Extract task_id from symlink name
            task_id = path.stem
            # Accept any task_id format
            task_ids.append(task_id)
        return sorted(task_ids)
    
    def list_trajectories(self) -> List[str]:
        """List all stored trajectory task IDs.
        
        Returns:
            List of task IDs with trajectories
        """
        task_ids = []
        for path in self.trajectories_dir.glob("*.json"):
            if not path.is_symlink():
                continue
            # Extract task_id from symlink name
            task_id = path.stem
            # Accept any task_id format (including test_XXX for tests)
            task_ids.append(task_id)
        return sorted(task_ids)


def store_task_suite(
    tasks: List[Task],
    storage_dir: str = ".hipcortex",
) -> Dict[str, str]:
    """Store a suite of tasks.
    
    Args:
        tasks: List of tasks to store
        storage_dir: Storage directory
    
    Returns:
        Mapping of task_id to artifact_hash
    """
    storage = HipCortexStorage(storage_dir)
    task_hashes = {}
    
    for task in tasks:
        artifact_hash = storage.store_task(task)
        task_hashes[task.task_id] = artifact_hash
    
    return task_hashes
