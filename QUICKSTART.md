# Quick Start - Docker Compose

Get AURELIUS running in 5 minutes with Docker Compose.

## Prerequisites

- Docker Desktop or Docker Engine (20.10+)
- Docker Compose (2.0+)
- 4GB RAM minimum
- 10GB disk space

## Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/AURELIUS_Quant_Reasoning_Model.git
cd AURELIUS_Quant_Reasoning_Model
```

### 2. Configure Environment

```bash
# Copy example environment file
cp api/.env.production.example api/.env

# Edit configuration (optional - defaults work for local dev)
# Change DB_PASSWORD and SECRET_KEY for production
nano api/.env
```

### 3. Start Services

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","database":"connected",...}

# Open API documentation
open http://localhost:8000/docs
```

### 5. Create First User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "Test User"
  }'
```

### 6. Generate Strategy

```bash
# Get token from registration response
TOKEN="your_access_token_here"

# Generate strategy
curl -X POST http://localhost:8000/api/v1/strategies/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Create a momentum trading strategy",
    "risk_preference": "moderate",
    "max_strategies": 3
  }'
```

## Common Commands

```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs for specific service
docker-compose logs -f api

# Rebuild after code changes
docker-compose up -d --build

# Clean up everything
docker-compose down -v
```

## What's Running?

After `docker-compose up -d`:

- **PostgreSQL**: localhost:5432
- **API Server**: localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Troubleshooting

### Port Already in Use

```bash
# Change port in docker-compose.yml
# Under api service, change "8000:8000" to "8001:8000"
```

### Database Connection Failed

```bash
# Wait 30 seconds for PostgreSQL to start
# Check database is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres
```

### API Won't Start

```bash
# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api
```

## Next Steps

- Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment
- See [README.md](README.md) for full documentation
- Check [CHANGELOG.md](CHANGELOG.md) for latest updates
- Run integration tests: `cd api && python test_integration.py`

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (deletes database data)
docker-compose down -v
```
