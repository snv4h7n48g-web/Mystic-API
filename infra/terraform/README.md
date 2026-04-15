# Mystic AWS Terraform Scaffold

This directory provides a starter AWS deployment scaffold for the backend:

- VPC with public and private subnets
- ALB with health checks against `/health/ready`
- ECS Fargate service for the API
- RDS PostgreSQL
- S3 upload bucket
- CloudWatch logs
- CloudWatch alarms and dashboard
- ECS autoscaling
- Secrets Manager integration for runtime secrets

## Intended secret model

Inject these through ECS task definition secrets:

- `DB_PASSWORD`
- `JWT_SECRET_KEY`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- optional `APPLE_SHARED_SECRET`

The backend now also supports discrete DB env vars:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

This keeps the ECS config compatible with Secrets Manager without forcing a single prebuilt `DATABASE_URL` secret.

## Typical flow

1. Build and push the backend image to ECR.
2. Create Secrets Manager secrets for DB password, JWT secret, and Google Play service account JSON.
3. Copy `terraform.tfvars.example` to `terraform.tfvars` and fill in real values.
4. Run:

```powershell
terraform init
terraform plan
terraform apply
```

## Notes

- This scaffold is intentionally small and API-only. It does not yet provision a worker service, WAF, Route 53, ACM, or RTDN ingestion.
- Production should set `db_multi_az = true`, increase ECS capacity, and put HTTPS + WAF in front of the ALB.
- Alarm emails require subscription confirmation after `terraform apply`.
