"""Database helper functions and CRUD operations."""
from sqlalchemy.orm import Session
from database.models import Strategy, Backtest, Validation, GateResult, ReflexionIteration, OrchestratorRun
from datetime import datetime


class StrategyDB:
    """Strategy database operations."""

    @staticmethod
    def create(db: Session, strategy_data: dict) -> Strategy:
        """Create a new strategy."""
        strategy = Strategy(
            name=strategy_data.get("name"),
            description=strategy_data.get("description"),
            strategy_type=strategy_data.get("strategy_type"),
            confidence=strategy_data.get("confidence"),
            parameters=strategy_data.get("parameters"),
            status="active"
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def get(db: Session, strategy_id: str) -> Strategy:
        """Get strategy by ID."""
        return db.query(Strategy).filter(Strategy.id == strategy_id).first()

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 10) -> tuple:
        """List strategies with pagination."""
        total = db.query(Strategy).count()
        strategies = db.query(Strategy).offset(skip).limit(limit).all()
        return strategies, total

    @staticmethod
    def get_all(db: Session) -> list:
        """Get all strategies."""
        return db.query(Strategy).all()


class BacktestDB:
    """Backtest database operations."""

    @staticmethod
    def create(db: Session, strategy_id: str, request_data: dict) -> Backtest:
        """Create a new backtest record."""
        backtest = Backtest(
            strategy_id=strategy_id,
            start_date=request_data.get("start_date"),
            end_date=request_data.get("end_date"),
            initial_capital=request_data.get("initial_capital"),
            instruments=request_data.get("instruments", []),
            seed=request_data.get("seed", 42),
            data_source=request_data.get("data_source", "default"),
            status="pending"
        )
        db.add(backtest)
        db.commit()
        db.refresh(backtest)
        return backtest

    @staticmethod
    def update_running(db: Session, backtest_id: str) -> Backtest:
        """Mark backtest as running."""
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if backtest:
            backtest.status = "running"
            db.commit()
            db.refresh(backtest)
        return backtest

    @staticmethod
    def update_completed(db: Session, backtest_id: str, metrics: dict,
                        duration: float) -> Backtest:
        """Mark backtest as completed with results."""
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if backtest:
            backtest.status = "completed"
            backtest.metrics = metrics
            backtest.completed_at = datetime.utcnow()
            backtest.duration_seconds = duration
            db.commit()
            db.refresh(backtest)
        return backtest

    @staticmethod
    def update_failed(db: Session, backtest_id: str, error_message: str) -> Backtest:
        """Mark backtest as failed."""
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if backtest:
            backtest.status = "failed"
            backtest.error_message = error_message
            backtest.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(backtest)
        return backtest

    @staticmethod
    def get(db: Session, backtest_id: str) -> Backtest:
        """Get backtest by ID."""
        return db.query(Backtest).filter(Backtest.id == backtest_id).first()

    @staticmethod
    def list_by_strategy(db: Session, strategy_id: str,
                        skip: int = 0, limit: int = 10) -> tuple:
        """List backtests for a strategy."""
        query = db.query(Backtest).filter(Backtest.strategy_id == strategy_id)
        total = query.count()
        backtests = query.offset(skip).limit(limit).all()
        return backtests, total

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 10) -> tuple:
        """List all backtests."""
        total = db.query(Backtest).count()
        backtests = db.query(Backtest).offset(skip).limit(limit).all()
        return backtests, total


class ValidationDB:
    """Validation database operations."""

    @staticmethod
    def create(db: Session, strategy_id: str, request_data: dict) -> Validation:
        """Create a new validation record."""
        validation = Validation(
            strategy_id=strategy_id,
            start_date=request_data.get("start_date"),
            end_date=request_data.get("end_date"),
            window_size_days=request_data.get("window_size_days"),
            train_size_days=request_data.get("train_size_days"),
            initial_capital=request_data.get("initial_capital"),
            status="pending"
        )
        db.add(validation)
        db.commit()
        db.refresh(validation)
        return validation

    @staticmethod
    def update_completed(db: Session, validation_id: str, windows: list,
                        metrics: dict, duration: float) -> Validation:
        """Mark validation as completed with results."""
        validation = db.query(Validation).filter(Validation.id == validation_id).first()
        if validation:
            validation.status = "completed"
            validation.windows = windows
            validation.metrics = metrics
            validation.num_windows = metrics.get("num_windows")
            validation.avg_train_sharpe = metrics.get("avg_train_sharpe")
            validation.avg_test_sharpe = metrics.get("avg_test_sharpe")
            validation.avg_degradation = metrics.get("avg_degradation")
            validation.stability_score = metrics.get("stability_score")
            validation.passed = metrics.get("passed")
            validation.completed_at = datetime.utcnow()
            validation.duration_seconds = duration
            db.commit()
            db.refresh(validation)
        return validation

    @staticmethod
    def update_failed(db: Session, validation_id: str, error_message: str) -> Validation:
        """Mark validation as failed."""
        validation = db.query(Validation).filter(Validation.id == validation_id).first()
        if validation:
            validation.status = "failed"
            validation.error_message = error_message
            validation.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(validation)
        return validation

    @staticmethod
    def get(db: Session, validation_id: str) -> Validation:
        """Get validation by ID."""
        return db.query(Validation).filter(Validation.id == validation_id).first()

    @staticmethod
    def list_by_strategy(db: Session, strategy_id: str,
                        skip: int = 0, limit: int = 10) -> tuple:
        """List validations for a strategy."""
        query = db.query(Validation).filter(Validation.strategy_id == strategy_id)
        total = query.count()
        validations = query.offset(skip).limit(limit).all()
        return validations, total

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 10) -> tuple:
        """List all validations."""
        total = db.query(Validation).count()
        validations = db.query(Validation).offset(skip).limit(limit).all()
        return validations, total


class GateResultDB:
    """Gate result database operations."""

    @staticmethod
    def create(db: Session, strategy_id: str, gate_type: str,
              passed: bool, results: dict) -> GateResult:
        """Create a new gate result."""
        gate_result = GateResult(
            strategy_id=strategy_id,
            gate_type=gate_type,
            passed=passed,
            results=results,
            production_ready=passed if gate_type == "product" else None,
            recommendation=results.get("recommendation") if gate_type == "product" else None
        )
        db.add(gate_result)
        db.commit()
        db.refresh(gate_result)
        return gate_result

    @staticmethod
    def get_latest(db: Session, strategy_id: str, gate_type: str) -> GateResult:
        """Get latest gate result for a strategy."""
        return db.query(GateResult).filter(
            GateResult.strategy_id == strategy_id,
            GateResult.gate_type == gate_type
        ).order_by(GateResult.timestamp.desc()).first()

    @staticmethod
    def list_by_strategy(db: Session, strategy_id: str,
                        skip: int = 0, limit: int = 10) -> tuple:
        """List gate results for a strategy."""
        query = db.query(GateResult).filter(GateResult.strategy_id == strategy_id)
        total = query.count()
        results = query.offset(skip).limit(limit).all()
        return results, total

    @staticmethod
    def get_product_gate(db: Session, strategy_id: str) -> GateResult:
        """Get latest product gate result."""
        return db.query(GateResult).filter(
            GateResult.strategy_id == strategy_id,
            GateResult.gate_type == "product"
        ).order_by(GateResult.timestamp.desc()).first()


class ReflexionDB:
    """Reflexion iteration database operations."""

    @staticmethod
    def create_iteration(
        db: Session,
        strategy_id: str,
        improvement_score: float,
        feedback: str | None,
        improvements: list[str],
        context_data: dict,
    ) -> ReflexionIteration:
        latest = db.query(ReflexionIteration).filter(
            ReflexionIteration.strategy_id == strategy_id
        ).order_by(ReflexionIteration.iteration_num.desc()).first()

        iteration_num = 1 if latest is None else latest.iteration_num + 1

        row = ReflexionIteration(
            strategy_id=strategy_id,
            iteration_num=iteration_num,
            improvement_score=improvement_score,
            feedback=feedback,
            improvements=improvements,
            context_data=context_data,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def list_by_strategy(db: Session, strategy_id: str, limit: int = 100) -> list[ReflexionIteration]:
        return db.query(ReflexionIteration).filter(
            ReflexionIteration.strategy_id == strategy_id
        ).order_by(ReflexionIteration.iteration_num.desc()).limit(limit).all()


class OrchestratorDB:
    """Orchestrator run database operations."""

    @staticmethod
    def create(db: Session, strategy_id: str | None, inputs: dict, stages: dict) -> OrchestratorRun:
        run = OrchestratorRun(
            strategy_id=strategy_id,
            status="running",
            current_stage="generate_strategy",
            stages=stages,
            inputs=inputs,
            outputs={},
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get(db: Session, run_id: str) -> OrchestratorRun | None:
        return db.query(OrchestratorRun).filter(OrchestratorRun.id == run_id).first()

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 20) -> tuple[list[OrchestratorRun], int]:
        query = db.query(OrchestratorRun).order_by(OrchestratorRun.created_at.desc())
        total = query.count()
        return query.offset(skip).limit(limit).all(), total

    @staticmethod
    def update_stage(
        db: Session,
        run_id: str,
        stage_name: str,
        status: str,
        details: dict | None = None,
        error_message: str | None = None,
    ) -> OrchestratorRun | None:
        run = OrchestratorDB.get(db, run_id)
        if not run:
            return None

        stages = dict(run.stages or {})
        stage = dict(stages.get(stage_name, {}))
        stage["status"] = status
        stage["updated_at"] = datetime.utcnow().isoformat()
        if details is not None:
            stage["details"] = details
        if error_message:
            stage["error"] = error_message
        stages[stage_name] = stage

        run.current_stage = stage_name
        run.stages = stages
        if status == "failed":
            run.status = "failed"
            run.error_message = error_message
            run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def complete(db: Session, run_id: str, outputs: dict) -> OrchestratorRun | None:
        run = OrchestratorDB.get(db, run_id)
        if not run:
            return None

        run.status = "completed"
        run.current_stage = "completed"
        run.outputs = outputs
        run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        return run
