# AI Task Processing Platform

Folders: `backend`, `frontend`, `worker`, `infra/k8s`.

# 🚀 AI Task Processing Platform

<div align="center">

![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Argo CD](https://img.shields.io/badge/Argo_CD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white)

**A production-grade, horizontally scalable asynchronous task processing system built with a polyglot microservices architecture — designed to handle 100,000+ tasks per day with full GitOps deployment automation.**

[Architecture](#-architecture) · [Getting Started](#-getting-started) · [API Reference](#-api-reference) · [Deployment](#-deployment) · [Scaling](#-scaling--performance) · [Contributing](#-contributing)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development (Docker Compose)](#local-development-docker-compose)
  - [Environment Variables](#environment-variables)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
  - [Kubernetes](#kubernetes-deployment)
  - [GitOps with Argo CD](#gitops-with-argo-cd)
  - [CI/CD Pipeline](#cicd-pipeline)
- [Scaling & Performance](#-scaling--performance)
- [Reliability & Fault Tolerance](#-reliability--fault-tolerance)
- [Security](#-security)
- [Database Design](#-database-design)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧩 Overview

The **AI Task Processing Platform** is a full-stack distributed system that decouples task submission from task execution through an asynchronous, queue-driven architecture. Users authenticate via a web frontend, submit tasks through a RESTful Node.js backend, and those tasks are durably queued in Redis before being consumed and processed by a fleet of stateless Python workers.

The platform is designed from the ground up for **production reliability and operational simplicity** — every component is containerised, horizontally scalable, and managed declaratively. Whether running locally with Docker Compose for development or deployed to a multi-namespace Kubernetes cluster with autoscaling and GitOps, the system behaves identically across environments.

**Core use case:** Any workload where tasks are submitted by many users, execution is CPU/time intensive or asynchronous, and results need to be tracked per user — for example, AI inference jobs, data processing pipelines, report generation, file transformations, or batch operations.

---

## ✨ Key Features

- **Asynchronous task queue** — Tasks are enqueued into Redis immediately on submission; execution happens asynchronously by worker processes, keeping API response times low regardless of task complexity.
- **Stateless Python workers** — Workers hold no local state; they pull tasks from Redis, process them, and write results to MongoDB. Because they are stateless, you can run 1 or 1,000 replicas transparently.
- **Horizontal autoscaling** — Kubernetes HPA (Horizontal Pod Autoscaler) monitors worker queue depth or CPU and spins replicas up or down automatically to absorb bursts.
- **JWT authentication** — All task endpoints are protected with JSON Web Tokens; the backend validates tokens on every request.
- **Per-user task visibility** — Tasks are indexed by `userId`, `status`, and `createdAt`, so users only ever see their own tasks and queries remain fast at scale.
- **Durable queue with dead-letter support** — Redis RPOPLPUSH pattern ensures tasks are not lost if a worker crashes mid-processing. Failed tasks are retried with exponential backoff and moved to a dead-letter queue after exhausting retries.
- **GitOps deployment** — All Kubernetes manifests live in `infra/k8s`. Argo CD watches the infra repo and auto-syncs changes to the cluster; no manual `kubectl apply` in production.
- **Full CI/CD** — GitHub Actions pipeline runs tests, builds Docker images, pushes to a registry, and patches image tags in the infra repo on every release.
- **Separate staging and production environments** — Managed via Kubernetes namespaces with environment-specific ConfigMaps, Secrets, and image tags.
- **Single-command local setup** — One `docker-compose up --build` brings up all five services (MongoDB, Redis, backend, worker, frontend) with hot-reload ready.

---

## 🏛 Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                          User Browser                             │
│                      (HTML/JS Frontend)                           │
│                        Port 3000 / 80                             │
└──────────────────────────────┬────────────────────────────────────┘
                               │  REST API (HTTP/JSON)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Backend API (Node.js)                        │
│                          Port 4000                                │
│                                                                   │
│  POST /api/auth/register   POST /api/auth/login                   │
│  POST /api/tasks           GET  /api/tasks                        │
│  GET  /api/tasks/:id                                              │
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐  │
│  │  JWT Middleware  │    │  Task Controller                     │  │
│  │  (auth guard)   │───▶│  • Validates & persists task to DB   │  │
│  └─────────────────┘    │  • Pushes task ID onto Redis queue   │  │
│                          └──────────────────────────────────────┘  │
└────────────────────┬────────────────────┬─────────────────────────┘
                     │                    │
                     ▼                    ▼
         ┌───────────────────┐  ┌───────────────────────┐
         │   MongoDB (v6)    │  │     Redis (v7)         │
         │                   │  │                        │
         │  Collections:     │  │  Queue: tasks:queue    │
         │  • users          │  │  (RPOPLPUSH pattern    │
         │  • tasks          │  │   for durability)      │
         │                   │  │                        │
         │  Indexes:         │  │  Dead-letter:          │
         │  • userId         │  │  tasks:dlq             │
         │  • status         │  │                        │
         │  • createdAt      │  │                        │
         └────────┬──────────┘  └──────────┬────────────┘
                  │                        │
                  │                        │ BLPOP / RPOPLPUSH
                  │                        ▼
                  │         ┌──────────────────────────────────────┐
                  │         │         Python Worker Pool            │
                  │         │                                       │
                  │         │  Worker 1  Worker 2  ...  Worker N    │
                  │         │  (Stateless — scale horizontally)     │
                  │         │                                       │
                  │         │  1. Dequeue task ID from Redis        │
                  │         │  2. Fetch task payload from MongoDB   │
                  │         │  3. Execute task logic                │
                  │         │  4. Write result + status back to DB  │
                  │         │  5. Retry on failure (exp. backoff)   │
                  │         └──────────────┬────────────────────────┘
                  │                        │
                  └────────────────────────┘
                       (result persistence)
```

### Data Flow

1. A user logs in via the frontend, receiving a JWT.
2. The user submits a task via `POST /api/tasks` with the JWT in the `Authorization` header.
3. The backend validates the JWT, writes the task document to MongoDB with `status: "queued"`, and pushes the task's `_id` onto the Redis queue.
4. A Python worker dequeues the task ID using the RPOPLPUSH pattern (ensuring exactly-once processing semantics), fetches the full task from MongoDB, processes it, and writes the result back to MongoDB with `status: "completed"` or `status: "failed"`.
5. The user polls `GET /api/tasks/:id` (or fetches their task list) to see results.

---

## 🛠 Technology Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Frontend** | HTML / Vanilla JS | User interface, served via Nginx |
| **Backend** | Node.js + Express | REST API, authentication, task ingestion |
| **Worker** | Python 3 | Asynchronous task execution |
| **Primary Database** | MongoDB 6 | Task and user persistence |
| **Queue / Cache** | Redis 7 | Task queue, pub/sub, ephemeral state |
| **Containerisation** | Docker + Docker Compose | Local development environment |
| **Orchestration** | Kubernetes (+ HPA) | Production container orchestration |
| **GitOps** | Argo CD | Declarative continuous delivery |
| **CI/CD** | GitHub Actions | Test, build, push, deploy pipeline |
| **Ingress** | Kubernetes Ingress | External traffic routing |

---

## 📁 Project Structure

```
Task-Processing-Platform/
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # GitHub Actions pipeline
│
├── backend/                     # Node.js Express API
│   ├── src/
│   │   ├── routes/
│   │   │   ├── auth.js          # /api/auth/* endpoints
│   │   │   └── tasks.js         # /api/tasks/* endpoints
│   │   ├── models/
│   │   │   ├── User.js          # Mongoose user schema
│   │   │   └── Task.js          # Mongoose task schema + indexes
│   │   ├── middleware/
│   │   │   └── auth.js          # JWT verification middleware
│   │   ├── services/
│   │   │   └── queue.js         # Redis publish/enqueue logic
│   │   └── app.js               # Express app setup
│   ├── Dockerfile
│   └── package.json
│
├── frontend/                    # Static web frontend
│   ├── index.html               # Main application shell
│   ├── app.js                   # Client-side logic
│   ├── style.css
│   ├── nginx.conf               # Nginx config for serving
│   └── Dockerfile
│
├── worker/                      # Python async task processor
│   ├── worker.py                # Main worker loop (Redis consumer)
│   ├── tasks/                   # Task handler registry
│   │   └── processor.py         # Task execution logic
│   ├── requirements.txt
│   └── Dockerfile
│
├── infra/
│   └── k8s/                     # All Kubernetes manifests
│       ├── namespace.yaml        # staging / production namespaces
│       ├── configmap.yaml        # Non-secret environment config
│       ├── secret.yaml           # Secrets (base64-encoded)
│       ├── backend-deployment.yaml
│       ├── backend-service.yaml
│       ├── frontend-deployment.yaml
│       ├── worker-deployment.yaml
│       ├── worker-hpa.yaml       # Horizontal Pod Autoscaler
│       └── ingress.yaml          # Ingress routing rules
│
├── architecture.md              # Architecture notes and ADRs
├── docker-compose.yml           # Local development stack
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

Make sure the following are installed on your machine:

- [Docker](https://docs.docker.com/get-docker/) (v20+) and [Docker Compose](https://docs.docker.com/compose/install/) (v2+)
- [Node.js](https://nodejs.org/) v18+ (only needed if running backend outside Docker)
- [Python](https://www.python.org/) 3.10+ (only needed if running worker outside Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (for Kubernetes deployments)

### Local Development (Docker Compose)

Clone the repository and start the full stack with a single command:

```bash
git clone https://github.com/Sadhikari2642/Task-Processing-Platform.git
cd Task-Processing-Platform
docker-compose up --build
```

This starts five services:

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:3000 | Nginx serving static files |
| Backend API | http://localhost:4000 | Express REST API |
| MongoDB | `mongodb://localhost:27017` | Persisted via `mongo-data` volume |
| Redis | `redis://localhost:6379` | Task queue |
| Worker | — | Runs in background, no exposed port |

To run services individually (e.g., only the backend and its dependencies):

```bash
docker-compose up mongo redis backend
```

To rebuild after code changes:

```bash
docker-compose up --build --force-recreate
```

To tear down and remove volumes:

```bash
docker-compose down -v
```

### Environment Variables

The following environment variables are used across services. In Docker Compose they are injected directly; in Kubernetes they come from `ConfigMap` and `Secret` objects.

#### Backend

| Variable | Default (dev) | Description |
|----------|--------------|-------------|
| `MONGO_URI` | `mongodb://mongo:27017/tasks` | MongoDB connection string |
| `REDIS_URL` | `redis://redis:6379` | Redis connection string |
| `JWT_SECRET` | `devsecret` | **Change this in production** — used to sign/verify JWTs |
| `PORT` | `4000` | HTTP port for the Express server |

#### Worker

| Variable | Default (dev) | Description |
|----------|--------------|-------------|
| `MONGO_URI` | `mongodb://mongo:27017/tasks` | MongoDB connection string |
| `REDIS_URL` | `redis://redis:6379` | Redis connection string |
| `WORKER_CONCURRENCY` | `1` | Tasks processed simultaneously per pod |
| `MAX_RETRIES` | `3` | Retry attempts before dead-lettering a task |

> ⚠️ **Never commit real secrets.** For local dev the defaults are fine; for staging/production always use Kubernetes Secrets or an external secrets manager.

---

## 📡 API Reference

All endpoints are prefixed with `/api`. Authenticated endpoints require the header:

```
Authorization: Bearer <jwt_token>
```

### Authentication

#### `POST /api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response `201`:**
```json
{
  "message": "User registered successfully",
  "userId": "64f3a2b1c8d7e9f0a1b2c3d4"
}
```

---

#### `POST /api/auth/login`

Authenticate and receive a JWT.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response `200`:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "userId": "64f3a2b1c8d7e9f0a1b2c3d4"
}
```

---

### Tasks

#### `POST /api/tasks` 🔒 _Authenticated_

Submit a new task for processing.

**Request Body:**
```json
{
  "type": "data_processing",
  "payload": {
    "input": "...",
    "options": {}
  }
}
```

**Response `201`:**
```json
{
  "taskId": "64f3a2b1c8d7e9f0a1b2c3d5",
  "status": "queued",
  "createdAt": "2025-08-15T10:30:00.000Z"
}
```

---

#### `GET /api/tasks` 🔒 _Authenticated_

Retrieve all tasks for the authenticated user. Supports filtering by `status`.

**Query Parameters:**
- `status` — Filter by task status (`queued`, `processing`, `completed`, `failed`)
- `limit` — Number of results (default: `20`, max: `100`)
- `page` — Pagination page number (default: `1`)

**Response `200`:**
```json
{
  "tasks": [
    {
      "taskId": "64f3a2b1c8d7e9f0a1b2c3d5",
      "type": "data_processing",
      "status": "completed",
      "result": { "output": "..." },
      "createdAt": "2025-08-15T10:30:00.000Z",
      "completedAt": "2025-08-15T10:30:05.000Z"
    }
  ],
  "total": 42,
  "page": 1
}
```

---

#### `GET /api/tasks/:id` 🔒 _Authenticated_

Retrieve a single task by ID.

**Response `200`:**
```json
{
  "taskId": "64f3a2b1c8d7e9f0a1b2c3d5",
  "type": "data_processing",
  "status": "completed",
  "payload": { "input": "..." },
  "result": { "output": "..." },
  "createdAt": "2025-08-15T10:30:00.000Z",
  "completedAt": "2025-08-15T10:30:05.000Z",
  "attempts": 1
}
```

**Status Codes:**

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Task created |
| `400` | Bad request / validation error |
| `401` | Missing or invalid JWT |
| `403` | Task belongs to another user |
| `404` | Task not found |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

---

## ☸️ Deployment

### Kubernetes Deployment

All manifests are in `infra/k8s/`. Apply them in order:

```bash
# 1. Create namespaces (staging and production)
kubectl apply -f infra/k8s/namespace.yaml

# 2. Apply configuration and secrets
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/secret.yaml

# 3. Deploy backend
kubectl apply -f infra/k8s/backend-deployment.yaml
kubectl apply -f infra/k8s/backend-service.yaml

# 4. Deploy frontend
kubectl apply -f infra/k8s/frontend-deployment.yaml

# 5. Deploy workers with autoscaling
kubectl apply -f infra/k8s/worker-deployment.yaml
kubectl apply -f infra/k8s/worker-hpa.yaml

# 6. Configure ingress
kubectl apply -f infra/k8s/ingress.yaml
```

Or apply the entire `infra/k8s/` directory at once:

```bash
kubectl apply -f infra/k8s/
```

#### Verifying the Deployment

```bash
# Check all pods are running
kubectl get pods -n production

# Check services
kubectl get svc -n production

# Check HPA status for workers
kubectl get hpa -n production

# View logs for a worker
kubectl logs -n production -l app=worker --tail=100

# View backend logs
kubectl logs -n production -l app=backend --tail=100
```

#### Secrets Management

Before deploying, update `infra/k8s/secret.yaml` with your base64-encoded production values:

```bash
# Encode a secret value
echo -n "your-production-jwt-secret" | base64

# Encode MongoDB URI
echo -n "mongodb+srv://user:pass@cluster.mongodb.net/tasks" | base64
```

> 💡 For a production setup, consider using [External Secrets Operator](https://external-secrets.io/) or [Sealed Secrets](https://sealed-secrets.netlify.app/) to avoid storing base64 secrets in Git.

---

### GitOps with Argo CD

This project is designed for a GitOps workflow using [Argo CD](https://argo-cd.readthedocs.io/).

**Recommended setup:**

1. Maintain `infra/k8s/` in a dedicated **infra repository** (separate from the application code repository).
2. Install Argo CD in your cluster:
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```
3. Create an Argo CD `Application` pointing at your infra repo:
   ```yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: task-platform-production
     namespace: argocd
   spec:
     project: default
     source:
       repoURL: https://github.com/your-org/task-platform-infra
       targetRevision: main
       path: k8s/production
     destination:
       server: https://kubernetes.default.svc
       namespace: production
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
   ```
4. Argo CD will **auto-sync** any changes pushed to the infra repo's `main` branch into the cluster. No manual `kubectl apply` is needed in production.

---

### CI/CD Pipeline

The GitHub Actions workflow in `.github/workflows/ci-cd.yml` runs on every push to `main` and on pull requests:

```
Push to main / PR
       │
       ▼
  ┌─────────────────┐
  │   Run Tests      │
  │  (backend, worker│
  └────────┬────────┘
           │ (if tests pass)
           ▼
  ┌─────────────────────────────────┐
  │   Build Docker Images            │
  │   backend, frontend, worker      │
  └────────┬────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────┐
  │   Push to Container Registry    │
  │   (tagged with git SHA)         │
  └────────┬────────────────────────┘
           │  (on release / main merge)
           ▼
  ┌─────────────────────────────────┐
  │   Update Image Tags in          │
  │   Infra Repo (infra/k8s/)       │
  └────────┬────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────┐
  │   Argo CD detects change        │
  │   Auto-syncs to cluster         │
  └─────────────────────────────────┘
```

**Required GitHub Secrets:**

| Secret | Description |
|--------|-------------|
| `DOCKER_USERNAME` | Container registry username |
| `DOCKER_PASSWORD` | Container registry password / token |
| `INFRA_REPO_TOKEN` | GitHub PAT with write access to infra repo |
| `KUBE_CONFIG` | (Optional) kubeconfig for direct cluster access |

---

## 📈 Scaling & Performance

### Throughput Capacity

The platform is designed to handle **100,000+ tasks per day** (~1.16 tasks/second average). With burst capacity:

| Workers | Estimated throughput |
|---------|---------------------|
| 1 | ~1–5 tasks/sec (simple tasks) |
| 10 | ~10–50 tasks/sec |
| 100 | ~100–500 tasks/sec |

_Actual throughput depends on task complexity. The bottleneck is typically task execution time, not queue or database operations._

### Worker Autoscaling (HPA)

The Kubernetes HPA in `worker-hpa.yaml` automatically scales the worker deployment based on CPU utilisation or custom metrics:

```yaml
spec:
  minReplicas: 2
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

For queue-depth-based autoscaling (more responsive to actual load), consider using [KEDA](https://keda.sh/) with a Redis scaler:

```yaml
# KEDA ScaledObject example
triggers:
  - type: redis
    metadata:
      listName: tasks:queue
      listLength: "10"    # Scale up when queue depth exceeds 10 per worker
```

### Database Performance

MongoDB indexes are defined on the `Task` model for all common query patterns:

- `userId` — user-scoped task listing
- `status` — filtering by task state
- `createdAt` — chronological ordering and TTL archival

For 100k+ tasks/day the recommended MongoDB configuration:
- Use a replica set (3 nodes minimum) for read scaling and high availability
- Enable connection pooling in the backend (`poolSize: 10` is a reasonable default)
- Archive or TTL-delete completed tasks older than 30 days to control collection size

---

## 🔒 Reliability & Fault Tolerance

### Queue Durability

Workers use the **RPOPLPUSH pattern** (atomically moves task IDs from the main queue to a `tasks:processing` list) so that if a worker pod crashes mid-task, the task remains in `tasks:processing` and can be recovered by a watchdog process rather than being silently dropped.

### Retry with Exponential Backoff

Failed tasks are retried up to `MAX_RETRIES` times (default: 3) with exponential backoff:

```
Attempt 1: immediate
Attempt 2: 2s delay
Attempt 3: 4s delay
Attempt 4: 8s delay → move to dead-letter queue
```

### Dead-Letter Queue

Tasks that exceed `MAX_RETRIES` are moved to `tasks:dlq` in Redis. A separate monitoring process can inspect, re-queue, or alert on DLQ depth. This ensures failed tasks are never silently lost and can be investigated and replayed.

### Health Checks

Backend pods expose a `/health` endpoint for Kubernetes liveness and readiness probes:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 4000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 4000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## 🔐 Security

- **JWT Authentication** — All `/api/tasks` endpoints require a valid JWT signed with `JWT_SECRET`. Tokens expire and must be refreshed.
- **Input Validation** — Task payloads are validated on the backend before being persisted or enqueued.
- **Least-Privilege Containers** — Dockerfiles use non-root users where possible.
- **Secrets in Kubernetes** — No secrets are hardcoded; all sensitive values are injected via `Secret` objects or an external secrets manager.
- **Namespace Isolation** — Staging and production workloads run in separate Kubernetes namespaces with independent RBAC policies.
- **Network Policies** — Consider adding `NetworkPolicy` manifests to restrict pod-to-pod communication to only what is required (frontend → backend, backend → mongo/redis, worker → mongo/redis).

---

## 🗄 Database Design

### `users` Collection

```json
{
  "_id": "ObjectId",
  "email": "string (unique, indexed)",
  "passwordHash": "string (bcrypt)",
  "createdAt": "Date"
}
```

### `tasks` Collection

```json
{
  "_id": "ObjectId",
  "userId": "ObjectId (indexed)",
  "type": "string",
  "status": "string (queued|processing|completed|failed) (indexed)",
  "payload": "object",
  "result": "object (nullable)",
  "attempts": "number",
  "errorMessage": "string (nullable)",
  "createdAt": "Date (indexed)",
  "updatedAt": "Date",
  "completedAt": "Date (nullable)"
}
```

**Compound indexes** for common query patterns:

```javascript
// User's task list, filtered by status, sorted newest-first
{ userId: 1, status: 1, createdAt: -1 }

// Admin/monitoring: all tasks of a given status
{ status: 1, createdAt: -1 }
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** and ensure all tests pass:
   ```bash
   # Backend tests
   cd backend && npm test

   # Worker tests
   cd worker && python -m pytest
   ```
3. **Write or update tests** for any new functionality.
4. **Commit your changes** using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add task priority levels
   fix: handle Redis connection timeout gracefully
   docs: update API reference for task filtering
   ```
5. **Open a Pull Request** with a clear description of the change and why it's needed.

### Development Tips

- Run only the infrastructure services and develop the backend or worker locally:
  ```bash
  docker-compose up mongo redis          # Start dependencies
  cd backend && npm run dev              # Run backend with nodemon
  cd worker && python worker.py          # Run worker locally
  ```
- Use the `docker-compose.yml` `environment` section to override variables without modifying code.
- The `infra/k8s/` directory is the single source of truth for production configuration — any cluster changes should go through Git, not direct `kubectl` commands.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built with ❤️ · Node.js + Python + MongoDB + Redis + Kubernetes

</div>
