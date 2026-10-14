<div align="center">

# 🤖 AI DevOps Log Analyzer Platform

**Plateforme cloud-native d'analyse intelligente de logs applicatifs propulsée par le Machine Learning**

[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/your-username/ai-devops-log-analyzer/actions)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-orchestrated-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 Description

**AI DevOps Log Analyzer Platform** est une solution complète, conteneurisée et orchestrée avec Kubernetes, permettant d'ingérer, stocker, analyser et visualiser des logs applicatifs. Grâce à deux modèles de Machine Learning (`IsolationForest` et `RandomForestClassifier`), la plateforme détecte automatiquement les anomalies et classe les erreurs par catégorie (HTTP, authentification, base de données, timeout, mémoire, réseau, exception, inconnu).

Le projet adopte une architecture microservices moderne : frontend Nginx, API backend FastAPI, microservice IA dédié, base MySQL et stack d'observabilité Prometheus + Grafana. Le pipeline CI/CD GitHub Actions permet un déploiement automatisé sur AWS EKS.

## ✨ Fonctionnalités principales

- 🔍 Détection d'anomalies non supervisée via `IsolationForest`
- 🧠 Classification multi-classes des erreurs via `RandomForest`
- 📤 Upload de logs (multi-fichiers, jusqu'à 100 Mo)
- 📊 Dashboard avec statistiques agrégées
- 🐳 100 % conteneurisé (Docker + Docker Compose)
- ☸️ Orchestration Kubernetes (manifests EKS-ready)
- 📈 Observabilité : Prometheus + Grafana
- 🔄 Pipeline CI/CD complet (build, test, push, deploy)
- 🧪 Tests automatisés (`pytest`) sur tous les services

---

## 📐 Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET / USERS                         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    Nginx Ingress (K8s)    │
                    └──────┬──────────┬─────────┘
                           │          │
          ┌────────────────▼──┐  ┌────▼──────────────────┐
          │  Frontend (Nginx) │  │  Backend API (FastAPI)│
          │  HTML/CSS/JS      │  │  :8000                │
          └───────────────────┘  └─────────┬─────────────┘
                                           │
                          ┌────────────────┴────────────────┐
                          │                                 │
               ┌──────────▼──────────┐          ┌───────────▼─────────┐
               │   MySQL Database    │          │  AI Microservice    │
               │   :3306             │          │  FastAPI + sklearn  │
               └─────────────────────┘          │  :8001              │
                                                └─────────────────────┘

               ┌─────────────────────────────────────────┐
               │          OBSERVABILITY STACK            │
               │  Prometheus (:9090)   Grafana (:3000)   │
               └─────────────────────────────────────────┘
```

## 🧬 Modèles IA

| Modèle | Algorithme | Objectif |
|--------|-----------|----------|
| Détecteur d'anomalies | `IsolationForest` | Détection non supervisée de patterns inhabituels |
| Classificateur d'erreurs | `RandomForestClassifier` | Classification multi-classes du type d'erreur |

**15 features extraites par ligne de log :**

- Longueur de ligne, nombre de mots, score du niveau de log
- Présence d'adresse IP, timestamp, mots-clés d'exception, codes HTTP d'erreur
- Code de statut HTTP, statistiques numériques, fréquence erreurs/warnings
- Nombre de tokens, structure de brackets, indicateurs de stack trace

**Catégories de classification :** HTTP Error · Auth Failure · DB Error · Timeout · Memory · Network · Exception · Unknown

---

## 🗂️ Structure du projet

```text
ai-devops-log-analyzer/
├── frontend/                    # Dashboard Nginx + HTML/CSS/JS
│   ├── static/{css,js}/         # Styles et logique client
│   ├── templates/index.html     # Page SPA principale
│   ├── nginx/nginx.conf         # Configuration Nginx
│   └── Dockerfile
│
├── backend/                     # API REST FastAPI
│   ├── app/
│   │   ├── main.py              # App factory + middleware
│   │   ├── api/v1/              # Routes
│   │   │   ├── logs.py          # POST/GET /logs
│   │   │   ├── analysis.py      # POST /analyze, GET /results
│   │   │   ├── health.py        # GET /health
│   │   │   └── stats.py         # GET /stats/dashboard
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic settings
│   │   │   └── database.py      # SQLAlchemy async
│   │   ├── models/models.py     # Modèles ORM
│   │   └── schemas/schemas.py   # Schémas Pydantic
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── ai-service/                  # Microservice de prédiction IA
│   ├── app/
│   │   ├── main.py              # App FastAPI + cycle de vie des modèles
│   │   ├── routes.py            # /predict, /health, /model/info
│   │   └── services/
│   │       └── predictor.py     # Pipeline IsolationForest + RandomForest
│   ├── training/train.py        # Script d'entraînement
│   ├── tests/test_predictor.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── database/
│   └── migrations/001_init_schema.sql
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
├── .github/workflows/ci-cd.yml  # Pipeline CI/CD
└── docker-compose.yml
```

---

## 🚀 Démarrage rapide (développement local)

### Prérequis

- Docker ≥ 24.0
- Docker Compose ≥ 2.20

### 1. Cloner et lancer

```bash
git clone https://github.com/your-username/ai-devops-log-analyzer.git
cd ai-devops-log-analyzer

# Build + démarrage
docker compose up --build

# Ou en arrière-plan
docker compose up -d --build
```

### 2. Vérifier l'état des services

```bash
docker compose ps

# Entraînement du modèle IA (~30 s au premier démarrage)
docker compose logs -f ai-service
```

### 3. Accéder à la plateforme

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Dashboard** | http://localhost | — |
| **Backend API Docs** | http://localhost:8000/docs | — |
| **AI Service Docs** | http://localhost:8001/docs | — |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | — |

### 4. Tester avec un fichier de log

```bash
# Créer un fichier de log d'exemple
cat > test.log << 'EOF'
2024-01-15 10:00:00 INFO     App  - Server started on port 8080
2024-01-15 10:00:01 INFO     App  - GET /api/users 200 12ms user_id=1234
2024-01-15 10:00:02 ERROR    Auth - Authentication failed for user admin@10.0.0.5 attempt 3
2024-01-15 10:00:03 CRITICAL App  - OutOfMemoryError: Java heap space GC overhead exceeded
2024-01-15 10:00:04 INFO     App  - GET /api/products 200 8ms
2024-01-15 10:00:05 ERROR    DB   - Connection refused mysql:3306 after 5 retry attempts
EOF

# Upload via l'API
curl -X POST http://localhost:8000/api/v1/logs/upload \
  -F "files=@test.log"

# Lancer l'analyse (remplacez LOG_ID par l'ID retourné ci-dessus)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"log_ids": ["LOG_ID"], "mode": "auto", "sensitivity": 7}'
```

---

## ☁️ Déploiement Cloud (AWS EKS)

### Prérequis

- AWS CLI configuré
- `eksctl` installé
- `kubectl` configuré

### 1. Créer le cluster EKS

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

### 2. Configurer les secrets

```bash
# Encoder vos vraies valeurs
DB_URL=$(echo -n "mysql+aiomysql://..." | base64)
SECRET=$(echo -n "your-real-secret-key" | base64)

# Éditez kubernetes/base/configmap-secrets.yml avec les vraies valeurs
kubectl apply -f kubernetes/base/configmap-secrets.yml
```

### 3. Déployer

```bash
kubectl apply -f kubernetes/base/database/
kubectl apply -f kubernetes/base/ai-service/
kubectl apply -f kubernetes/base/backend/
kubectl apply -f kubernetes/base/frontend/

# Installer l'ingress controller Nginx
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

### 4. Configurer GitHub Actions

Ajoutez ces secrets dans votre dépôt (`Settings → Secrets and variables → Actions`) :

| Secret | Valeur |
|--------|--------|
| `DOCKERHUB_USERNAME` | Votre nom d'utilisateur DockerHub |
| `DOCKERHUB_TOKEN` | Token d'accès DockerHub |
| `KUBECONFIG` | kubeconfig encodé en base64 : `cat ~/.kube/config \| base64` |

---

## 🧪 Tests

```bash
# Backend
cd backend
pip install -r requirements.txt pytest pytest-asyncio httpx
pytest tests/ -v

# AI service
cd ../ai-service
pip install -r requirements.txt pytest
pytest tests/ -v

# Entraîner les modèles sur données synthétiques
python training/train.py --synthetic --n-normal 10000 --output-dir ./models
```

---

## 📊 Référence API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/logs/upload` | Upload de fichiers de logs (`multipart/form-data`, champ `files[]`) |
| `GET` | `/api/v1/logs` | Liste des logs uploadés |
| `POST` | `/api/v1/analyze` | Lancer l'analyse IA |
| `GET` | `/api/v1/results` | Résultats d'analyse avec détails des anomalies |
| `GET` | `/api/v1/stats/dashboard` | Statistiques agrégées du dashboard |
| `GET` | `/api/v1/health` | Health check global (backend, base de données, service IA) |

**Exemple de corps pour `POST /api/v1/analyze` :**

```json
{
  "log_ids": ["uuid1", "uuid2"],
  "mode": "auto",
  "sensitivity": 7
}
```

---

## 🔧 Configuration

Tous les paramètres sont contrôlés par variables d'environnement :

| Variable | Valeur par défaut | Description |
|----------|-------------------|-------------|
| `DATABASE_URL` | `mysql+aiomysql://...` | Chaîne de connexion MySQL |
| `AI_SERVICE_URL` | `http://ai-service:8001` | URL du microservice IA |
| `MAX_FILE_SIZE_MB` | `100` | Taille maximale d'upload |
| `SECRET_KEY` | — | Clé JWT (obligatoire en production) |
| `DEBUG` | `false` | Active les logs de debug |

---

## 🏢 Checklist production

- [ ] Remplacer tous les secrets `dev-*` par des valeurs de production
- [ ] Activer SSL/TLS sur l'Ingress (cert-manager)
- [ ] Configurer l'autoscaling horizontal (HPA)
- [ ] Mettre en place des sauvegardes MySQL (AWS RDS recommandé en production)
- [ ] Définir des politiques de rétention des logs
- [ ] Configurer les alertes dans Grafana
- [ ] Entraîner les modèles sur de vraies données de production
- [ ] Activer les network policies pour l'isolation des pods
- [ ] Configurer le RBAC pour l'accès `kubectl`

---

## 📄 Licence

Ce projet est distribué sous licence MIT — voir le fichier [LICENSE](LICENSE).
