# Architecture (brief)

- Worker scaling: Stateless Python workers consume Redis queue; scale horizontally via replicas/HPA.
- Throughput: 100k tasks/day ~ 1.16 tasks/sec; with 10 workers and Redis pipeline this is trivial; increase workers and DB pool for bursts.
- DB indexing: `userId`, `status`, `createdAt` indexed for queries and TTL/archival.
- Redis failure strategy: Durable queue (RPOPLPUSH pattern can be added), retries with backoff, dead-letter queue for failed tasks.
- Staging vs Prod: separate k8s namespaces and image tags; infra repo managed by GitOps (ArgoCD) with auto-sync.
