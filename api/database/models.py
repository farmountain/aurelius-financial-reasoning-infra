"""SQLAlchemy ORM models for AURELIUS."""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base
import uuid


class Strategy(Base):
    """Strategy model for storing generated strategies."""
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)

    # Parameters as JSON
    parameters = Column(JSON, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="active")

    # Relationships
    backtests = relationship("Backtest", back_populates="strategy", cascade="delete")
    validations = relationship("Validation", back_populates="strategy", cascade="delete")
    gate_results = relationship("GateResult", back_populates="strategy", cascade="delete")

    def __repr__(self):
        return f"<Strategy {self.id}: {self.name}>"


class Backtest(Base):
    """Backtest execution results."""
    __tablename__ = "backtests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)

    # Configuration
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)
    initial_capital = Column(Float, nullable=False)
    instruments = Column(JSON, nullable=False)
    seed = Column(Integer, nullable=False, default=42)
    data_source = Column(String(255), nullable=False, default="default")

    # Status
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    error_message = Column(Text)

    # Results as JSON
    metrics = Column(JSON)  # Sharpe, return, drawdown, etc
    trades = Column(JSON)  # List of individual trades
    equity_curve = Column(JSON)  # Daily equity values

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")

    def __repr__(self):
        return f"<Backtest {self.id}: {self.status}>"


class Validation(Base):
    """Walk-forward validation results."""
    __tablename__ = "validations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)

    # Configuration
    start_date = Column(String(10), nullable=False)
    end_date = Column(String(10), nullable=False)
    window_size_days = Column(Integer, nullable=False)
    train_size_days = Column(Integer, nullable=False)
    initial_capital = Column(Float, nullable=False)

    # Status
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    error_message = Column(Text)

    # Results as JSON
    windows = Column(JSON)  # Per-window results
    metrics = Column(JSON)  # Summary metrics

    # Summary metrics (denormalized for easier querying)
    num_windows = Column(Integer)
    avg_train_sharpe = Column(Float)
    avg_test_sharpe = Column(Float)
    avg_degradation = Column(Float)
    stability_score = Column(Float)
    passed = Column(Boolean)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # Relationships
    strategy = relationship("Strategy", back_populates="validations")

    def __repr__(self):
        return f"<Validation {self.id}: {self.status}>"


class GateResult(Base):
    """Gate verification results."""
    __tablename__ = "gate_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)

    # Gate type
    gate_type = Column(String(20), nullable=False)  # dev, crv, product

    # Status and results
    passed = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Detailed results as JSON
    results = Column(JSON, nullable=False)

    # For product gate specifically
    production_ready = Column(Boolean)
    recommendation = Column(Text)

    # Relationships
    strategy = relationship("Strategy", back_populates="gate_results")

    def __repr__(self):
        return f"<GateResult {self.id}: {self.gate_type} - {'PASS' if self.passed else 'FAIL'}>"


class ReflexionIteration(Base):
    """Reflexion iteration history per strategy."""
    __tablename__ = "reflexion_iterations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False, index=True)
    iteration_num = Column(Integer, nullable=False)
    improvement_score = Column(Float, nullable=False, default=0.0)
    feedback = Column(Text)
    improvements = Column(JSON, nullable=False, default=list)
    context_data = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    strategy = relationship("Strategy")

    def __repr__(self):
        return f"<ReflexionIteration {self.id}: strategy={self.strategy_id} iteration={self.iteration_num}>"


class OrchestratorRun(Base):
    """Persisted end-to-end orchestrator runs."""
    __tablename__ = "orchestrator_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="pending")
    current_stage = Column(String(50), nullable=True)
    stages = Column(JSON, nullable=False, default=dict)
    inputs = Column(JSON, nullable=False, default=dict)
    outputs = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    strategy = relationship("Strategy")

    def __repr__(self):
        return f"<OrchestratorRun {self.id}: status={self.status} stage={self.current_stage}>"
