"""Task generator and benchmark suite for AURELIUS."""

from aureus.tasks.synthetic_generator import (
    RegimeType,
    SyntheticRegimeGenerator,
    generate_regime_data,
)
from aureus.tasks.task_generator import (
    TaskType,
    Task,
    TaskGenerator,
)
from aureus.tasks.benchmark import (
    BenchmarkRunner,
    BenchmarkResults,
    TaskResult,
)
from aureus.tasks.storage import (
    HipCortexStorage,
    TaskArtifact,
    GoldTrajectory,
    store_task_suite,
)

__all__ = [
    "RegimeType",
    "SyntheticRegimeGenerator",
    "generate_regime_data",
    "TaskType",
    "Task",
    "TaskGenerator",
    "BenchmarkRunner",
    "BenchmarkResults",
    "TaskResult",
    "HipCortexStorage",
    "TaskArtifact",
    "GoldTrajectory",
    "store_task_suite",
]
