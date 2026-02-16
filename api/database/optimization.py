"""
Database optimization utilities
Includes index creation and query optimization helpers
"""
from sqlalchemy import inspect, text
from database.session import engine
import logging

logger = logging.getLogger(__name__)


def create_performance_indexes():
    """Create database indexes for improved query performance"""
    index_specs = [
        # Strategy indexes
        {
            "name": "idx_strategies_created_at",
            "table": "strategies",
            "columns": ["created_at"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_strategies_created_at ON strategies(created_at DESC)",
        },
        {
            "name": "idx_strategies_name",
            "table": "strategies",
            "columns": ["name"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_strategies_name ON strategies(name)",
        },

        # Backtest indexes
        {
            "name": "idx_backtests_strategy_id",
            "table": "backtests",
            "columns": ["strategy_id"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_backtests_strategy_id ON backtests(strategy_id)",
        },
        {
            "name": "idx_backtests_created_at",
            "table": "backtests",
            "columns": ["created_at"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_backtests_created_at ON backtests(created_at DESC)",
        },
        {
            "name": "idx_backtests_status",
            "table": "backtests",
            "columns": ["status"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_backtests_status ON backtests(status)",
        },

        # Validation indexes
        {
            "name": "idx_validations_strategy_id",
            "table": "validations",
            "columns": ["strategy_id"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_validations_strategy_id ON validations(strategy_id)",
        },
        {
            "name": "idx_validations_created_at",
            "table": "validations",
            "columns": ["created_at"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_validations_created_at ON validations(created_at DESC)",
        },

        # Gate result indexes
        {
            "name": "idx_gate_results_strategy_id",
            "table": "gate_results",
            "columns": ["strategy_id"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_gate_results_strategy_id ON gate_results(strategy_id)",
        },
        {
            "name": "idx_gate_results_gate_type",
            "table": "gate_results",
            "columns": ["gate_type"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_gate_results_gate_type ON gate_results(gate_type)",
        },
        {
            "name": "idx_gate_results_passed",
            "table": "gate_results",
            "columns": ["passed"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_gate_results_passed ON gate_results(passed)",
        },
        {
            "name": "idx_gate_results_timestamp",
            "table": "gate_results",
            "columns": ["timestamp"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_gate_results_timestamp ON gate_results(timestamp DESC)",
        },

        # Reflexion indexes
        {
            "name": "idx_reflexion_iterations_strategy_id",
            "table": "reflexion_iterations",
            "columns": ["strategy_id"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_reflexion_iterations_strategy_id ON reflexion_iterations(strategy_id)",
        },
        {
            "name": "idx_reflexion_iterations_created_at",
            "table": "reflexion_iterations",
            "columns": ["created_at"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_reflexion_iterations_created_at ON reflexion_iterations(created_at DESC)",
        },

        # Orchestrator indexes
        {
            "name": "idx_orchestrator_runs_strategy_id",
            "table": "orchestrator_runs",
            "columns": ["strategy_id"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_orchestrator_runs_strategy_id ON orchestrator_runs(strategy_id)",
        },
        {
            "name": "idx_orchestrator_runs_created_at",
            "table": "orchestrator_runs",
            "columns": ["created_at"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_orchestrator_runs_created_at ON orchestrator_runs(created_at DESC)",
        },

        # User indexes
        {
            "name": "idx_users_email",
            "table": "users",
            "columns": ["email"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        },
        {
            "name": "idx_users_is_active",
            "table": "users",
            "columns": ["is_active"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
        },

        # Composite indexes for common queries
        {
            "name": "idx_backtests_strategy_created",
            "table": "backtests",
            "columns": ["strategy_id", "created_at"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_backtests_strategy_created ON backtests(strategy_id, created_at DESC)",
        },
        {
            "name": "idx_gate_results_strategy_type",
            "table": "gate_results",
            "columns": ["strategy_id", "gate_type"],
            "sql": "CREATE INDEX IF NOT EXISTS idx_gate_results_strategy_type ON gate_results(strategy_id, gate_type)",
        },
    ]
    
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        created_count = 0
        skipped_count = 0

        with engine.connect() as conn:
            for spec in index_specs:
                table_name = spec["table"]
                required_columns = spec["columns"]

                if table_name not in existing_tables:
                    logger.info("Skipping index %s: table %s does not exist", spec["name"], table_name)
                    skipped_count += 1
                    continue

                table_columns = {column["name"] for column in inspector.get_columns(table_name)}
                missing_columns = [column for column in required_columns if column not in table_columns]
                if missing_columns:
                    logger.info(
                        "Skipping index %s: missing columns %s on table %s",
                        spec["name"],
                        ", ".join(missing_columns),
                        table_name,
                    )
                    skipped_count += 1
                    continue

                try:
                    conn.execute(text(spec["sql"]))
                    created_count += 1
                    logger.info("Created/verified index: %s", spec["name"])
                except Exception as e:
                    skipped_count += 1
                    logger.warning("Index creation skipped for %s: %s", spec["name"], e)
            
            conn.commit()
        logger.info(
            "Database index verification complete: %s created/verified, %s skipped",
            created_count,
            skipped_count,
        )
        return skipped_count == 0
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        return False


def analyze_tables():
    """Run ANALYZE on all tables to update statistics"""
    tables = [
        "users",
        "strategies", 
        "backtests",
        "validations",
        "gate_results",
        "reflexion_iterations",
        "orchestrator_runs",
    ]
    
    try:
        with engine.connect() as conn:
            existing_tables = set(inspect(engine).get_table_names())
            for table in tables:
                if table not in existing_tables:
                    logger.info("Skipping ANALYZE for missing table: %s", table)
                    continue
                conn.execute(text(f"ANALYZE {table}"))
                logger.info(f"Analyzed table: {table}")
            conn.commit()
        logger.info("Table analysis completed")
        return True
    except Exception as e:
        logger.error(f"Error analyzing tables: {e}")
        return False


def get_table_stats():
    """Get table size and row count statistics"""
    query = text("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
            n_tup_ins AS inserts,
            n_tup_upd AS updates,
            n_tup_del AS deletes
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            stats = []
            for row in result:
                stats.append({
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "table_size": row[3],
                    "indexes_size": row[4],
                    "inserts": row[5],
                    "updates": row[6],
                    "deletes": row[7],
                })
            return stats
    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return []


def get_slow_queries():
    """Get slow query statistics (requires pg_stat_statements extension)"""
    query = text("""
        SELECT 
            query,
            calls,
            total_exec_time / 1000 AS total_time_seconds,
            mean_exec_time / 1000 AS mean_time_seconds,
            max_exec_time / 1000 AS max_time_seconds
        FROM pg_stat_statements
        WHERE query NOT LIKE '%pg_stat_statements%'
        ORDER BY total_exec_time DESC
        LIMIT 10
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            queries = []
            for row in result:
                queries.append({
                    "query": row[0][:200],  # Truncate long queries
                    "calls": row[1],
                    "total_time": round(row[2], 3),
                    "mean_time": round(row[3], 3),
                    "max_time": round(row[4], 3),
                })
            return queries
    except Exception as e:
        logger.warning(f"Could not get slow queries (pg_stat_statements may not be enabled): {e}")
        return []


def vacuum_tables():
    """Run VACUUM on all tables to reclaim space"""
    tables = [
        "users",
        "strategies",
        "backtests",
        "validations",
        "gate_results",
        "reflexion_iterations",
        "orchestrator_runs",
    ]
    
    try:
        # VACUUM cannot run inside a transaction block
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            existing_tables = set(inspect(engine).get_table_names())
            for table in tables:
                if table not in existing_tables:
                    logger.info("Skipping VACUUM for missing table: %s", table)
                    continue
                conn.execute(text(f"VACUUM ANALYZE {table}"))
                logger.info(f"Vacuumed table: {table}")
        logger.info("Table vacuum completed")
        return True
    except Exception as e:
        logger.error(f"Error vacuuming tables: {e}")
        return False
