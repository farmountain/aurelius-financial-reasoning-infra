# Database Integration Guide

## Overview

The AURELIUS REST API now integrates with PostgreSQL for persistent storage of strategies, backtests, validations, and gate results. This replaces the in-memory storage used during development.

## Prerequisites

### 1. Install PostgreSQL

**Windows (using Chocolatey):**
```bash
choco install postgresql
```

**macOS (using Homebrew):**
```bash
brew install postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
```

### 2. Start PostgreSQL Service

**Windows:**
```bash
# PostgreSQL should start automatically
# Or manually start the service
```

**macOS:**
```bash
brew services start postgresql
```

**Linux:**
```bash
sudo systemctl start postgresql
```

## Setup Steps

### Step 1: Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database
CREATE DATABASE aurelius;

# Create user
CREATE USER aurelius WITH PASSWORD 'aurelius_dev';

# Grant permissions
ALTER ROLE aurelius SET client_encoding TO 'utf8';
ALTER ROLE aurelius SET default_transaction_isolation TO 'read committed';
ALTER ROLE aurelius SET default_transaction_deferrable TO on;
ALTER ROLE aurelius SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aurelius TO aurelius;

# Quit
\q
```

### Step 2: Configure API Environment

Copy the example environment file:

```bash
cd api
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
# Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aurelius
DB_USER=aurelius
DB_PASSWORD=aurelius_dev
DB_ECHO=False
```

### Step 3: Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

New dependencies added:
- `sqlalchemy==2.0.23` - ORM framework
- `psycopg2-binary==2.9.9` - PostgreSQL adapter
- `alembic==1.13.0` - Migration tool

### Step 4: Initialize Database Tables

```bash
cd api
python init_db.py init
```

This creates all necessary tables:
- `strategies` - Generated strategies
- `backtests` - Backtest execution records
- `validations` - Walk-forward validation results
- `gate_results` - Gate verification results

### Step 5: Start the API

```bash
cd api
python main.py
```

The API will now use PostgreSQL instead of in-memory storage.

## Database Schema

### Strategies Table

```sql
CREATE TABLE strategies (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  strategy_type VARCHAR(50) NOT NULL,
  confidence FLOAT NOT NULL,
  parameters JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  status VARCHAR(20) DEFAULT 'active'
);

CREATE INDEX idx_strategies_type ON strategies(strategy_type);
CREATE INDEX idx_strategies_created ON strategies(created_at);
```

### Backtests Table

```sql
CREATE TABLE backtests (
  id VARCHAR(36) PRIMARY KEY,
  strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
  start_date VARCHAR(10) NOT NULL,
  end_date VARCHAR(10) NOT NULL,
  initial_capital FLOAT NOT NULL,
  instruments JSONB NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  error_message TEXT,
  metrics JSONB,
  trades JSONB,
  equity_curve JSONB,
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  duration_seconds FLOAT
);

CREATE INDEX idx_backtests_strategy ON backtests(strategy_id);
CREATE INDEX idx_backtests_status ON backtests(status);
CREATE INDEX idx_backtests_created ON backtests(created_at);
```

### Validations Table

```sql
CREATE TABLE validations (
  id VARCHAR(36) PRIMARY KEY,
  strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
  start_date VARCHAR(10) NOT NULL,
  end_date VARCHAR(10) NOT NULL,
  window_size_days INTEGER NOT NULL,
  train_size_days INTEGER NOT NULL,
  initial_capital FLOAT NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  error_message TEXT,
  windows JSONB,
  metrics JSONB,
  num_windows INTEGER,
  avg_train_sharpe FLOAT,
  avg_test_sharpe FLOAT,
  avg_degradation FLOAT,
  stability_score FLOAT,
  passed BOOLEAN,
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  duration_seconds FLOAT
);

CREATE INDEX idx_validations_strategy ON validations(strategy_id);
CREATE INDEX idx_validations_status ON validations(status);
CREATE INDEX idx_validations_created ON validations(created_at);
```

### Gate Results Table

```sql
CREATE TABLE gate_results (
  id VARCHAR(36) PRIMARY KEY,
  strategy_id VARCHAR(36) NOT NULL REFERENCES strategies(id),
  gate_type VARCHAR(20) NOT NULL,
  passed BOOLEAN NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  results JSONB NOT NULL,
  production_ready BOOLEAN,
  recommendation TEXT
);

CREATE INDEX idx_gate_results_strategy ON gate_results(strategy_id);
CREATE INDEX idx_gate_results_type ON gate_results(gate_type);
CREATE INDEX idx_gate_results_timestamp ON gate_results(timestamp);
```

## Management Commands

### Check Database Connection

```bash
cd api
python init_db.py check
```

### Initialize Tables

```bash
cd api
python init_db.py init
```

### Drop All Tables (WARNING: Destructive)

```bash
cd api
python init_db.py drop
```

### Reset Database (Drop and Recreate)

```bash
cd api
python init_db.py reset
```

## CRUD Operations

### Using the CLI

The database layer provides CRUD operations through SQLAlchemy:

```python
from database.crud import StrategyDB, BacktestDB, ValidationDB, GateResultDB
from database.session import SessionLocal

db = SessionLocal()

# Create
strategy = StrategyDB.create(db, {
    "name": "My Strategy",
    "description": "Example strategy",
    "strategy_type": "ts_momentum",
    "confidence": 0.9,
    "parameters": {"lookback": 20, "vol_target": 0.15}
})

# Read
strategy = StrategyDB.get(db, strategy.id)

# List
strategies, total = StrategyDB.list(db, skip=0, limit=10)

# All strategies
all_strategies = StrategyDB.get_all(db)

db.close()
```

### Via REST API

All endpoints now use the database:

```bash
# Generate and store strategies
curl -X POST "http://localhost:8000/api/v1/strategies/generate" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Find momentum patterns", "risk_preference": "moderate"}'

# List stored strategies
curl "http://localhost:8000/api/v1/strategies"

# Run backtest (stored in DB)
curl -X POST "http://localhost:8000/api/v1/backtests/run" \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": "...", "start_date": "2023-01-01", "end_date": "2024-01-01"}'

# Get backtest results
curl "http://localhost:8000/api/v1/backtests/{backtest_id}"
```

## Querying the Database

### Connect Directly

```bash
psql -U aurelius -d aurelius
```

### Common Queries

```sql
-- Count strategies by type
SELECT strategy_type, COUNT(*) FROM strategies GROUP BY strategy_type;

-- Recent backtests
SELECT id, strategy_id, status, created_at FROM backtests 
ORDER BY created_at DESC LIMIT 10;

-- Validation results for a strategy
SELECT * FROM validations 
WHERE strategy_id = '...' 
ORDER BY created_at DESC;

-- Gate results
SELECT gate_type, passed, COUNT(*) 
FROM gate_results 
GROUP BY gate_type, passed;

-- Production-ready strategies
SELECT DISTINCT s.id, s.name, s.strategy_type
FROM strategies s
JOIN gate_results gr ON s.id = gr.strategy_id
WHERE gr.gate_type = 'product' AND gr.production_ready = true;
```

## Backup and Restore

### Backup Database

```bash
# Full backup
pg_dump -U aurelius -d aurelius > aurelius_backup.sql

# Compressed backup
pg_dump -U aurelius -d aurelius | gzip > aurelius_backup.sql.gz
```

### Restore Database

```bash
# From SQL file
psql -U aurelius -d aurelius < aurelius_backup.sql

# From compressed file
gunzip -c aurelius_backup.sql.gz | psql -U aurelius -d aurelius
```

## Performance Optimization

### Create Indexes

Indexes are automatically created on:
- `strategies.strategy_type`
- `strategies.created_at`
- `backtests.strategy_id`
- `backtests.status`
- `backtests.created_at`
- `validations.strategy_id`
- `validations.status`
- `validations.created_at`
- `gate_results.strategy_id`
- `gate_results.gate_type`
- `gate_results.timestamp`

### Connection Pooling

The API uses SQLAlchemy connection pooling:
- Pool size: 10
- Max overflow: 20

Configure in `database/session.py` if needed.

## Troubleshooting

### Connection Refused

```
Error: psycopg2.OperationalError: could not connect to server
```

**Solution:**
1. Check PostgreSQL is running
2. Verify DB_HOST, DB_PORT, DB_USER, DB_PASSWORD in `.env`
3. Test connection: `psql -U aurelius -d aurelius`

### Permission Denied

```
Error: FATAL: Ident authentication failed for user "aurelius"
```

**Solution:**
1. Update PostgreSQL authentication in `pg_hba.conf`
2. Change method from `ident` to `md5` or `password`
3. Restart PostgreSQL

### Tables Already Exist

```
Error: CREATE TABLE ... already exists
```

**Solution:**
```bash
cd api
python init_db.py reset
```

## Migration Management

Currently using manual migrations. For future migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Production Considerations

### Security

1. **Use strong password**: Change `aurelius_dev` to a strong password
2. **SSL connections**: Enable SSL for remote connections
3. **User permissions**: Limit database user to specific tables
4. **Connection limits**: Configure PostgreSQL connection limits

### High Availability

1. **Replication**: Set up PostgreSQL streaming replication
2. **Backups**: Automated daily backups
3. **Monitoring**: Monitor database performance and disk usage

### Performance

1. **Connection pooling**: Already configured
2. **Query optimization**: Add indexes as needed
3. **Table partitioning**: Partition large tables by date
4. **Archive old data**: Move old data to archive tables

## Next Steps

1. **Test integration**: Run API and verify database operations
2. **Add migrations**: Set up Alembic for schema version control
3. **Performance testing**: Load test with large datasets
4. **Monitoring**: Set up database monitoring and alerting
5. **Backup automation**: Configure automated backups

## Support

For issues or questions:
- Check logs: `tail -f api.log`
- Review database logs: Check PostgreSQL log directory
- Test directly with psql before debugging API
