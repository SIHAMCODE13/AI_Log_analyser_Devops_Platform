# 🤖 AI DevOps Log Analyzer Platform

> **Cloud-native platform for intelligent application log analysis using Machine Learning**

[![CI/CD](https://img.shields.io/github/actions/workflow/status/your-username/ai-devops-log-analyzer/ci-cd.yml?label=CI%2FCD&logo=github)](https://github.com/your-username/ai-devops-log-analyzer)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://hub.docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-orchestrated-326CE5?logo=kubernetes)](https://kubernetes.io)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET / USERS                         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    Nginx Ingress (K8s)     │
                    └──────┬──────────┬──────────┘
                           │          │
          ┌────────────────▼──┐  ┌────▼─────────────────┐
          │   Frontend (Nginx) │  │   Backend API (FastAPI)│
          │   HTML/CSS/JS      │  │   :8000               │
          └───────────────────┘  └─────────┬─────────────┘
                                           │
                          ┌────────────────┴────────────────┐
                          │                                 │
               ┌──────────▼──────────┐          ┌──────────▼──────────┐
               │   MySQL Database    │          │  AI Microservice    │
               │   :3306             │          │  FastAPI + sklearn  │
               └─────────────────────┘          │  :8001             │
                                                └─────────────────────┘
                                                         │
               ┌────────────────────────────────────────┐
               │          OBSERVABILITY STACK           │
               │  Prometheus (:9090)  Grafana (:3000)   │
               └────────────────────────────────────────┘
```

## 🧬 AI Models

| Model | Algorithm | Purpose |
|-------|-----------|---------|
| Anomaly Detector | `IsolationForest` | Unsupervised detection of unusual log patterns |
| Error Classifier | `RandomForestClassifier` | Multi-class error type classification |

**Features extracted per log line (15 features):**
- Line length, word count, log level score
- Presence of: IP address, timestamp, exception keywords, HTTP error codes
- HTTP status code, numeric value statistics, error/warn frequency
- Token count, bracket structure, stack trace indicators

**Classification categories:** HTTP Error, Auth Failure, DB Error, Timeout, Memory, Network, Exception, Unknown

---

## 🗂️ Project Structure

```
ai-devops-log-analyzer/
├── frontend/                   # Nginx + HTML/CSS/JS dashboard
│   ├── static/{css,js}/       # Styles & client-side logic
│   ├── templates/index.html   # Main SPA page
│   ├── nginx/nginx.conf       # Nginx configuration
│   └── Dockerfile
│
├── backend/                    # FastAPI REST API
│   ├── app/
│   │   ├── main.py            # App factory + middleware
│   │   ├── api/v1/            # Route handlers
│   │   │   ├── logs.py        # POST/GET /logs
│   │   │   ├── analysis.py    # POST /analyze, GET /results
│   │   │   ├── health.py      # GET /health
│   │   │   └── stats.py       # GET /stats/dashboard
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic settings
│   │   │   └── database.py    # Async SQLAlchemy setup
│   │   ├── models/models.py   # ORM models
│   │   └── schemas/schemas.py # Pydantic request/response
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── ai-service/                 # AI prediction microservice
│   ├── app/
│   │   ├── main.py            # FastAPI app + model lifecycle
│   │   ├── routes.py          # /predict, /health, /model/info
│   │   └── services/
│   │       └── predictor.py   # IsolationForest + RandomForest pipeline
│   ├── training/train.py      # Standalone training script
│   ├── tests/test_predictor.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── database/
│   └── migrations/001_init_schema.sql  # MySQL schema
│
├── kubernetes/
│   └── base/
│       ├── frontend/deployment.yml
│       ├── backend/deployment.yml
│       ├── ai-service/deployment.yml
│       ├── database/statefulset.yml
│       └── configmap-secrets.yml
│
├── monitoring/
│   ├── prometheus/prometheus.yml
│   └── grafana/{dashboards,provisioning}/
│
├── .github/workflows/ci-cd.yml  # Full CI/CD pipeline
└── docker-compose.yml
```

---

## 🚀 Quick Start — Local Development

### Prerequisites

- Docker ≥ 24.0
- Docker Compose ≥ 2.20

### 1. Clone and start

```bash
git clone https://github.com/your-username/ai-devops-log-analyzer.git
cd ai-devops-log-analyzer

# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d --build
```

### 2. Wait for services to initialize

```bash
# Watch health status
docker compose ps

# Watch AI service model training (takes ~30s on first start)
docker compose logs -f ai-service
```

### 3. Access the platform

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost | — |
| **Backend API Docs** | http://localhost:8000/docs | — |
| **AI Service Docs** | http://localhost:8001/docs | — |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | — |

### 4. Upload a test log

```bash
# Create a sample log file
cat > test.log << 'EOF'
2024-01-15 10:00:00 INFO  App - Server started on port 8080
2024-01-15 10:00:01 INFO  App - GET /api/users 200 12ms user_id=1234
2024-01-15 10:00:02 ERROR Auth - Authentication failed for user admin@10.0.0.5 attempt 3
2024-01-15 10:00:03 CRITICAL App - OutOfMemoryError: Java heap space GC overhead exceeded
2024-01-15 10:00:04 INFO  App - GET /api/products 200 8ms
2024-01-15 10:00:05 ERROR DB - Connection refused mysql:3306 after 5 retry attempts
EOF

# Upload via API
curl -X POST http://localhost:8000/api/v1/logs/upload \
  -F "files=@test.log"

# Trigger analysis (replace LOG_ID with the ID from previous response)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"log_ids": ["LOG_ID"], "mode": "auto", "sensitivity": 7}'
```

---

## ☁️ Cloud Deployment (AWS EKS)

### Prerequisites

- AWS CLI configured
- `eksctl` installed
- `kubectl` configured

### 1. Create EKS cluster

```bash
eksctl create cluster \
  --name loganalyzer \
  --region eu-west-1 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

### 2. Configure secrets

```bash
# Encode your real values
DB_URL=$(echo -n "mysql+aiomysql://..." | base64)
SECRET=$(echo -n "your-real-secret-key" | base64)

# Edit kubernetes/base/configmap-secrets.yml with real values
kubectl apply -f kubernetes/base/configmap-secrets.yml
```

### 3. Deploy

```bash
# Apply all manifests
kubectl apply -f kubernetes/base/database/
kubectl apply -f kubernetes/base/ai-service/
kubectl apply -f kubernetes/base/backend/
kubectl apply -f kubernetes/base/frontend/

# Install nginx ingress controller
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

### 4. Configure GitHub Actions

Set these secrets in your GitHub repository (`Settings → Secrets`):

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | Your DockerHub username |
| `DOCKERHUB_TOKEN` | DockerHub access token |
| `KUBECONFIG` | Base64-encoded kubeconfig: `cat ~/.kube/config \| base64` |

---

## 🧪 Running Tests

```bash
# Backend tests
cd backend
pip install -r requirements.txt pytest pytest-asyncio httpx
pytest tests/ -v

# AI service tests
cd ai-service
pip install -r requirements.txt pytest
pytest tests/ -v

# Train AI models on synthetic data
cd ai-service
python training/train.py --synthetic --n-normal 10000 --output-dir ./models
```

---

## 📊 API Reference

### POST `/api/v1/logs/upload`
Upload log files for analysis.
- Body: `multipart/form-data` with `files[]`
- Returns: Array of log metadata objects

### GET `/api/v1/logs`
List all uploaded logs.

### POST `/api/v1/analyze`
Trigger AI analysis.
```json
{
  "log_ids": ["uuid1", "uuid2"],
  "mode": "auto",
  "sensitivity": 7
}
```

### GET `/api/v1/results`
List all analysis results with anomaly details.

### GET `/api/v1/stats/dashboard`
Dashboard aggregate statistics.

### GET `/api/v1/health`
Backend + database + AI service health check.

---

## 🔧 Configuration

All settings are controlled via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | mysql+aiomysql://... | MySQL connection string |
| `AI_SERVICE_URL` | http://ai-service:8001 | AI service URL |
| `MAX_FILE_SIZE_MB` | 100 | Upload size limit |
| `SECRET_KEY` | — | JWT secret (required in prod) |
| `DEBUG` | false | Enable debug logging |

---

## 🏢 Production Checklist

- [ ] Replace all `dev-*` secrets with production values
- [ ] Set up SSL/TLS on Ingress (cert-manager)
- [ ] Configure horizontal pod autoscaling (HPA)
- [ ] Set up backup for MySQL (AWS RDS recommended in production)
- [ ] Configure log retention policies
- [ ] Set up alerting in Grafana
- [ ] Train models on real production log data
- [ ] Enable network policies for pod isolation
- [ ] Set up RBAC for kubectl access

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
