# Deployment & Infrastructure

---

## 11.1 AWS Topology

Single region (`us-east-1`) in v1. All components in a dedicated VPC with public and private subnets across three availability zones.

```
VPC: 10.0.0.0/16
  Public subnets:  10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24   (ALB)
  Private subnets: 10.0.10.0/24, 10.0.20.0/24, 10.0.30.0/24 (ECS, RDS)
  DB subnets:      10.0.40.0/24, 10.0.50.0/24, 10.0.60.0/24 (RDS Multi-AZ)

ECS clusters:
  dispatch-api         (6 replicas)
  dispatch-webhook     (4 replicas, scales with event volume)
  dispatch-send        (20–60 replicas, scales with queue depth)
  dispatch-events      (10 replicas)
  dispatch-scheduler   (1 replica — Celery Beat)

RDS:         dispatch-prod-db      (db.r6g.2xlarge, Multi-AZ, 1 read replica)
ElastiCache: dispatch-prod-redis   (cache.r6g.large, replicated)
S3:          dispatch-prod-imports, dispatch-prod-inbound, dispatch-prod-events-archive
SNS:         dispatch-prod-ses-events (topic, multiple subscriptions)
SES:         production access, dedicated IP pool x3
```

---

## 11.2 Environments

| Environment | Purpose | Data | Deployed via |
|---|---|---|---|
| `local` | Developer machine | Docker Compose, ephemeral | `make dev` |
| `ci` | Automated testing | Ephemeral per test run | GitHub Actions |
| `staging` | Pre-production validation | Anonymized copy of prod | Auto on merge to `main` |
| `production` | Live traffic | Production | Manual approval, canary |

---

## 11.3 IaC Strategy

- All infrastructure defined in Terraform (AWS provider)
- Modules: `vpc`, `rds`, `ecs-service`, `ses-identity`, `cloudflare-domain`
- State stored in S3 with DynamoDB locking
- Changes go through `plan` → PR review → `apply` (no direct apply to production)
- Environment-specific variables in `envs/staging.tfvars` and `envs/prod.tfvars`
- Domain provisioning runs outside Terraform — it's operational, not infrastructural
