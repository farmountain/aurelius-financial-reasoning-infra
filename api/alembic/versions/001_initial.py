"""Initial migration - Create main tables.

Revision ID: 001
Revises: 
Create Date: 2026-02-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    
    # Create strategies table
    op.create_table(
        'strategies',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('strategy_type', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_strategies_type', 'strategies', ['strategy_type'])
    op.create_index('idx_strategies_created', 'strategies', ['created_at'])
    
    # Create backtests table
    op.create_table(
        'backtests',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('strategy_id', sa.String(36), nullable=False),
        sa.Column('start_date', sa.String(10), nullable=False),
        sa.Column('end_date', sa.String(10), nullable=False),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('instruments', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('trades', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('equity_curve', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('duration_seconds', sa.Float()),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_backtests_strategy', 'backtests', ['strategy_id'])
    op.create_index('idx_backtests_status', 'backtests', ['status'])
    op.create_index('idx_backtests_created', 'backtests', ['created_at'])
    
    # Create validations table
    op.create_table(
        'validations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('strategy_id', sa.String(36), nullable=False),
        sa.Column('start_date', sa.String(10), nullable=False),
        sa.Column('end_date', sa.String(10), nullable=False),
        sa.Column('window_size_days', sa.Integer(), nullable=False),
        sa.Column('train_size_days', sa.Integer(), nullable=False),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('windows', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('num_windows', sa.Integer()),
        sa.Column('avg_train_sharpe', sa.Float()),
        sa.Column('avg_test_sharpe', sa.Float()),
        sa.Column('avg_degradation', sa.Float()),
        sa.Column('stability_score', sa.Float()),
        sa.Column('passed', sa.Boolean()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('duration_seconds', sa.Float()),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_validations_strategy', 'validations', ['strategy_id'])
    op.create_index('idx_validations_status', 'validations', ['status'])
    op.create_index('idx_validations_created', 'validations', ['created_at'])
    
    # Create gate_results table
    op.create_table(
        'gate_results',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('strategy_id', sa.String(36), nullable=False),
        sa.Column('gate_type', sa.String(20), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('results', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('production_ready', sa.Boolean()),
        sa.Column('recommendation', sa.Text()),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_gate_results_strategy', 'gate_results', ['strategy_id'])
    op.create_index('idx_gate_results_type', 'gate_results', ['gate_type'])
    op.create_index('idx_gate_results_timestamp', 'gate_results', ['timestamp'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_gate_results_timestamp')
    op.drop_index('idx_gate_results_type')
    op.drop_index('idx_gate_results_strategy')
    op.drop_table('gate_results')
    
    op.drop_index('idx_validations_created')
    op.drop_index('idx_validations_status')
    op.drop_index('idx_validations_strategy')
    op.drop_table('validations')
    
    op.drop_index('idx_backtests_created')
    op.drop_index('idx_backtests_status')
    op.drop_index('idx_backtests_strategy')
    op.drop_table('backtests')
    
    op.drop_index('idx_strategies_created')
    op.drop_index('idx_strategies_type')
    op.drop_table('strategies')
