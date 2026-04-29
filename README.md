# AI Task Processing Platform

Folders: `backend`, `frontend`, `worker`, `infra/k8s`.

Run locally with Docker Compose:

```bash
docker-compose up --build
```

Key endpoints: `POST /api/auth/login`, `POST /api/tasks` (authenticated).

Kubernetes deploy (example):

```bash
# apply namespace + infra
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/secret.yaml
kubectl apply -f infra/k8s/backend-deployment.yaml
kubectl apply -f infra/k8s/backend-service.yaml
kubectl apply -f infra/k8s/frontend-deployment.yaml
kubectl apply -f infra/k8s/worker-deployment.yaml
kubectl apply -f infra/k8s/worker-hpa.yaml
kubectl apply -f infra/k8s/ingress.yaml
```

Argo CD / GitOps:

- Push `infra/k8s` to a separate infra repo and configure Argo CD to auto-sync that repo/paths into clusters.
- CI will update image tags in the infra repo during releases (see `.github/workflows/ci-cd.yml`).
