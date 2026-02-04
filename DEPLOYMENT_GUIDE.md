# Phase 10: Production Deployment Guide

## Overview

This guide covers deploying AURELIUS to production using Docker, Kubernetes, and cloud providers (AWS/GCP/Azure).

## 🐳 Docker Deployment

### Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Build Production Images

```bash
# Build API image
cd api
docker build -t aurelius-api:latest .

# Build Rust CLI image
cd ..
docker build -f Dockerfile.rust -t aurelius-rust:latest .

# Tag for registry
docker tag aurelius-api:latest ghcr.io/yourusername/aurelius-api:latest
docker tag aurelius-rust:latest ghcr.io/yourusername/aurelius-rust:latest

# Push to registry
docker push ghcr.io/yourusername/aurelius-api:latest
docker push ghcr.io/yourusername/aurelius-rust:latest
```

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm (optional but recommended)

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace aurelius

# Create secrets
kubectl create secret generic aurelius-secrets \
  --from-literal=database-url=postgresql://user:pass@postgres:5432/aurelius \
  --from-literal=secret-key=your-secret-key \
  --from-literal=database-password=your-db-password \
  -n aurelius

# Apply manifests
kubectl apply -f k8s/deployment.yml

# Check status
kubectl get pods -n aurelius
kubectl get svc -n aurelius

# View logs
kubectl logs -f deployment/aurelius-api -n aurelius

# Scale replicas
kubectl scale deployment aurelius-api --replicas=5 -n aurelius
```

### Ingress Setup (NGINX)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aurelius-ingress
  namespace: aurelius
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: aurelius-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aurelius-api
            port:
              number: 80
```

## ☁️ Cloud Provider Deployments

### AWS ECS/EKS

#### Using ECS Fargate

```bash
# Install AWS CLI and configure
aws configure

# Create ECR repository
aws ecr create-repository --repository-name aurelius-api

# Get login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag aurelius-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aurelius-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aurelius-api:latest

# Create ECS cluster
aws ecs create-cluster --cluster-name aurelius-cluster

# Create task definition (see aws/ecs-task-definition.json)
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster aurelius-cluster \
  --service-name aurelius-api \
  --task-definition aurelius-api:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

#### Using EKS

```bash
# Create EKS cluster
eksctl create cluster \
  --name aurelius-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name aurelius-cluster

# Deploy using kubectl
kubectl apply -f k8s/deployment.yml
```

### Google Cloud Platform (GCP/GKE)

```bash
# Set up gcloud CLI
gcloud init

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/aurelius-api ./api

# Create GKE cluster
gcloud container clusters create aurelius-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --region=us-central1

# Get credentials
gcloud container clusters get-credentials aurelius-cluster --region=us-central1

# Deploy
kubectl apply -f k8s/deployment.yml
```

### Azure (AKS)

```bash
# Install Azure CLI and login
az login

# Create resource group
az group create --name aurelius-rg --location eastus

# Create container registry
az acr create --resource-group aurelius-rg --name aureliusacr --sku Basic

# Build and push image
az acr build --registry aureliusacr --image aurelius-api:latest ./api

# Create AKS cluster
az aks create \
  --resource-group aurelius-rg \
  --name aurelius-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group aurelius-rg --name aurelius-cluster

# Deploy
kubectl apply -f k8s/deployment.yml
```

## 🔒 Security Checklist

### Before Production Deployment

- [ ] Change default database passwords
- [ ] Generate secure SECRET_KEY (32+ random characters)
- [ ] Configure CORS_ORIGINS with actual domain
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Review and update .env.production
- [ ] Enable database encryption at rest
- [ ] Set up VPC/network isolation

### Environment Variables

Create `.env.production`:

```bash
# Copy example
cp api/.env.production.example api/.env.production

# Edit with production values
nano api/.env.production
```

Required changes:
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `DB_PASSWORD`: Strong database password
- `CORS_ORIGINS`: Your actual domain(s)
- `DATABASE_URL`: Production database connection string

## 📊 Monitoring Setup

### Prometheus

```yaml
# prometheus-config.yml
scrape_configs:
  - job_name: 'aurelius-api'
    static_configs:
      - targets: ['aurelius-api:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import the provided dashboard:
```bash
kubectl apply -f monitoring/grafana-dashboard.json
```

### Logs

```bash
# View API logs
kubectl logs -f deployment/aurelius-api -n aurelius

# View all pods logs
kubectl logs -l app=aurelius-api -n aurelius --tail=100

# Follow logs with stern (recommended)
stern aurelius-api -n aurelius
```

## 🔄 CI/CD Pipeline

### GitHub Actions

The CI/CD pipeline automatically:
1. Runs Rust tests
2. Runs Python tests
3. Runs API integration tests
4. Builds Docker images
5. Pushes to container registry
6. Deploys to staging (optional)

Configure secrets in GitHub:
- `GITHUB_TOKEN` (automatic)
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `KUBECONFIG` (for K8s deployments)

### Manual Deployment

```bash
# Trigger deployment
git tag v1.0.0
git push origin v1.0.0

# Or push to main
git push origin main
```

## 🚀 Performance Optimization

### Database Connection Pooling

Already configured in `database/session.py`:
- Pool size: 20
- Max overflow: 10
- Pool timeout: 30s

### Horizontal Scaling

```bash
# Scale API pods
kubectl scale deployment aurelius-api --replicas=10 -n aurelius

# Auto-scaling is configured via HorizontalPodAutoscaler
# Scales between 2-10 pods based on CPU/memory
```

### Caching (Optional)

Add Redis for caching:

```yaml
# Add to docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

## 🔍 Troubleshooting

### API Won't Start

```bash
# Check logs
docker-compose logs api

# Check database connection
docker-compose exec postgres psql -U admin -d aurelius -c "SELECT 1"

# Restart services
docker-compose restart api
```

### Database Migration Issues

```bash
# Run migrations manually
docker-compose exec api alembic upgrade head

# Check migration status
docker-compose exec api alembic current
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n aurelius

# View metrics
curl http://api.yourdomain.com/metrics

# Check database queries
docker-compose exec postgres psql -U admin -d aurelius -c "SELECT * FROM pg_stat_activity"
```

## 📝 Maintenance

### Backups

```bash
# Backup PostgreSQL
kubectl exec -n aurelius postgres-xxxxx -- pg_dump -U admin aurelius > backup.sql

# Restore
kubectl exec -i -n aurelius postgres-xxxxx -- psql -U admin aurelius < backup.sql
```

### Updates

```bash
# Update images
docker-compose pull
docker-compose up -d

# Update K8s deployment
kubectl set image deployment/aurelius-api aurelius-api=ghcr.io/user/aurelius-api:v2.0.0 -n aurelius

# Rollback if needed
kubectl rollout undo deployment/aurelius-api -n aurelius
```

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/aurelius/issues
- Documentation: See README.md and other PHASE*.md files
- API Docs: https://api.yourdomain.com/docs

## 🎯 Next Steps

After deployment:
1. Monitor application health and metrics
2. Set up automated backups
3. Configure alerting rules
4. Perform load testing
5. Document any custom configurations
6. Train team on operations procedures
