# AWS Deployment & Configuration Guide — dispatch (`dispatch`)

This document is a sequential execution guide. Read each section fully before doing anything in that section. By the end you will have a production-ready AWS environment that matches the architecture defined in [13_deployment_infrastructure.md](13_deployment_infrastructure.md).

**Tools you need on your machine before starting:**
- AWS CLI v2 (`aws --version`)
- Docker Desktop
- Terraform ≥ 1.7 (optional but recommended for IaC)
- `jq` (for JSON parsing in CLI examples)

---

## 0. Pre-Flight Checklist

Before touching AWS, complete these steps once.

### 0.1 AWS account
- Create a dedicated AWS account for `dispatch` (do not use a personal or shared root account).
- Enable MFA on the root account — lock the root credentials away; never use root for day-to-day work.
- Set the billing alarm: **AWS Console → Billing → Budgets → Create budget** → monthly cost budget at a threshold that alerts you at 50% and 90%.

### 0.2 IAM admin user
```bash
# Create an admin IAM user for yourself (not root)
aws iam create-user --user-name dispatch-admin

# Attach admin policy
aws iam attach-user-policy \
  --user-name dispatch-admin \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access keys (store them securely — you will never see the secret again)
aws iam create-access-key --user-name dispatch-admin

# Configure your local CLI profile
aws configure --profile dispatch
# Enter: Access Key ID, Secret Access Key, Region (e.g. us-east-1), Output: json
```

### 0.3 Choose a region
All resources for `dispatch` must live in **one region** (e.g., `us-east-1`). SES, SNS, RDS, ElastiCache, and ECS must all be in the same region. Set a shell variable you can reuse:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile dispatch)
```

---

## 1. VPC & Networking

Everything runs inside a single custom VPC. Never use the default VPC.

### 1.1 Create the VPC

```bash
# Create VPC with a /16 CIDR block
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=dispatch-vpc}]' \
  --query Vpc.VpcId --output text --profile dispatch --region $AWS_REGION)

echo "VPC: $VPC_ID"

# Enable DNS hostnames (required for RDS)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --profile dispatch
```

### 1.2 Subnets

You need **three subnet tiers**, each in **two Availability Zones** (6 subnets total):

| Tier | AZ-a CIDR | AZ-b CIDR | Purpose |
|---|---|---|---|
| Public | 10.0.1.0/24 | 10.0.2.0/24 | Load balancers only |
| Private | 10.0.10.0/24 | 10.0.11.0/24 | ECS tasks, NAT-egress |
| Data | 10.0.20.0/24 | 10.0.21.0/24 | RDS, ElastiCache |

```bash
# Get two AZs
AZ_A=$(aws ec2 describe-availability-zones --region $AWS_REGION \
  --query 'AvailabilityZones[0].ZoneName' --output text --profile dispatch)
AZ_B=$(aws ec2 describe-availability-zones --region $AWS_REGION \
  --query 'AvailabilityZones[1].ZoneName' --output text --profile dispatch)

# Public subnets
PUB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 \
  --availability-zone $AZ_A \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=dispatch-pub-a}]' \
  --query Subnet.SubnetId --output text --profile dispatch)

PUB_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 \
  --availability-zone $AZ_B \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=dispatch-pub-b}]' \
  --query Subnet.SubnetId --output text --profile dispatch)

# Private subnets
PRIV_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.10.0/24 \
  --availability-zone $AZ_A \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=dispatch-priv-a}]' \
  --query Subnet.SubnetId --output text --profile dispatch)

PRIV_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.11.0/24 \
  --availability-zone $AZ_B \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=dispatch-priv-b}]' \
  --query Subnet.SubnetId --output text --profile dispatch)

# Data subnets
DATA_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.20.0/24 \
  --availability-zone $AZ_A \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=dispatch-data-a}]' \
  --query Subnet.SubnetId --output text --profile dispatch)

DATA_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.21.0/24 \
  --availability-zone $AZ_B \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=dispatch-data-b}]' \
  --query Subnet.SubnetId --output text --profile dispatch)
```

### 1.3 Internet Gateway + NAT Gateway

```bash
# Internet Gateway (for public subnets and LBs)
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=dispatch-igw}]' \
  --query InternetGateway.InternetGatewayId --output text --profile dispatch)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID --profile dispatch

# Elastic IP for NAT
EIP=$(aws ec2 allocate-address --domain vpc \
  --query AllocationId --output text --profile dispatch)

# NAT Gateway in public subnet a (one NAT for MVP; add second for HA in production)
NAT_ID=$(aws ec2 create-nat-gateway --subnet-id $PUB_A --allocation-id $EIP \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=dispatch-nat}]' \
  --query NatGateway.NatGatewayId --output text --profile dispatch)

# Wait for NAT to be available
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_ID --profile dispatch
echo "NAT ready: $NAT_ID"
```

### 1.4 Route tables

```bash
# Public route table → IGW
PUB_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=dispatch-public-rt}]' \
  --query RouteTable.RouteTableId --output text --profile dispatch)
aws ec2 create-route --route-table-id $PUB_RT --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID --profile dispatch
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_A --profile dispatch
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_B --profile dispatch

# Private route table → NAT
PRIV_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=dispatch-private-rt}]' \
  --query RouteTable.RouteTableId --output text --profile dispatch)
aws ec2 create-route --route-table-id $PRIV_RT --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_ID --profile dispatch
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_A --profile dispatch
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_B --profile dispatch
# Data subnets: no outbound internet route; they only talk within the VPC
```

### 1.5 Security Groups

Create one security group per service layer:

```bash
# --- ALB (public facing) ---
SG_ALB=$(aws ec2 create-security-group --group-name dispatch-alb-sg \
  --description "ALB - dispatch" --vpc-id $VPC_ID \
  --query GroupId --output text --profile dispatch)
aws ec2 authorize-security-group-ingress --group-id $SG_ALB \
  --ip-permissions '[{"IpProtocol":"tcp","FromPort":443,"ToPort":443,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]' \
  --profile dispatch

# --- ECS tasks ---
SG_ECS=$(aws ec2 create-security-group --group-name dispatch-ecs-sg \
  --description "ECS tasks - dispatch" --vpc-id $VPC_ID \
  --query GroupId --output text --profile dispatch)
# Allow inbound from ALB only
aws ec2 authorize-security-group-ingress --group-id $SG_ECS \
  --protocol tcp --port 8000 --source-group $SG_ALB --profile dispatch

# --- RDS PostgreSQL ---
SG_RDS=$(aws ec2 create-security-group --group-name dispatch-rds-sg \
  --description "RDS PostgreSQL - dispatch" --vpc-id $VPC_ID \
  --query GroupId --output text --profile dispatch)
aws ec2 authorize-security-group-ingress --group-id $SG_RDS \
  --protocol tcp --port 5432 --source-group $SG_ECS --profile dispatch

# --- ElastiCache Redis ---
SG_REDIS=$(aws ec2 create-security-group --group-name dispatch-redis-sg \
  --description "Redis - dispatch" --vpc-id $VPC_ID \
  --query GroupId --output text --profile dispatch)
aws ec2 authorize-security-group-ingress --group-id $SG_REDIS \
  --protocol tcp --port 6379 --source-group $SG_ECS --profile dispatch
```

---

## 2. RDS — PostgreSQL 15

### 2.1 DB subnet group

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name dispatch-db-subnet-group \
  --db-subnet-group-description "dispatch data tier" \
  --subnet-ids $DATA_A $DATA_B \
  --profile dispatch
```

### 2.2 Parameter group

```bash
aws rds create-db-parameter-group \
  --db-parameter-group-name dispatch-pg15 \
  --db-parameter-group-family postgres15 \
  --description "dispatch PostgreSQL 15 custom params" \
  --profile dispatch

# Key parameters for the platform
aws rds modify-db-parameter-group \
  --db-parameter-group-name dispatch-pg15 \
  --parameters \
    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" \
    "ParameterName=log_connections,ParameterValue=1,ApplyMethod=immediate" \
    "ParameterName=log_disconnections,ParameterValue=1,ApplyMethod=immediate" \
    "ParameterName=shared_preload_libraries,ParameterValue=pg_stat_statements,ApplyMethod=pending-reboot" \
  --profile dispatch
```

### 2.3 Create RDS instance

```bash
# Generate a secure password and save it (you will put it in Secrets Manager next)
DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)
echo "SAVE THIS: $DB_PASSWORD"

aws rds create-db-instance \
  --db-instance-identifier dispatch-postgres \
  --db-instance-class db.t4g.medium \
  --engine postgres \
  --engine-version 15.6 \
  --master-username dispatch_admin \
  --master-user-password "$DB_PASSWORD" \
  --db-name dispatch \
  --vpc-security-group-ids $SG_RDS \
  --db-subnet-group-name dispatch-db-subnet-group \
  --db-parameter-group-name dispatch-pg15 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --no-publicly-accessible \
  --deletion-protection \
  --tags Key=Project,Value=dispatch \
  --profile dispatch

# Wait for available (takes ~5 minutes)
aws rds wait db-instance-available \
  --db-instance-identifier dispatch-postgres \
  --profile dispatch

# Get the endpoint
DB_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier dispatch-postgres \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text --profile dispatch)
echo "DB endpoint: $DB_ENDPOINT"
```

### 2.4 Create the application DB user

Connect to RDS from a bastion or from your ECS task and run:

```sql
-- Run once after instance is available
CREATE USER dispatch_app WITH PASSWORD '<app-password-from-secrets-manager>';
GRANT CONNECT ON DATABASE dispatch TO dispatch_app;
GRANT USAGE ON SCHEMA public TO dispatch_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dispatch_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO dispatch_app;

-- Audit log table: INSERT-only (from architecture docs)
-- After running migrations, restrict the audit_log table specifically:
REVOKE UPDATE, DELETE ON audit_log FROM dispatch_app;
```

---

## 3. ElastiCache — Redis 7

### 3.1 Subnet group

```bash
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name dispatch-redis-subnet \
  --cache-subnet-group-description "dispatch Redis" \
  --subnet-ids $DATA_A $DATA_B \
  --profile dispatch
```

### 3.2 Create Redis cluster

```bash
aws elasticache create-replication-group \
  --replication-group-id dispatch-redis \
  --replication-group-description "dispatch Celery broker + token bucket" \
  --engine redis \
  --engine-version 7.2 \
  --cache-node-type cache.t4g.small \
  --num-cache-clusters 2 \
  --cache-subnet-group-name dispatch-redis-subnet \
  --security-group-ids $SG_REDIS \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --automatic-failover-enabled \
  --tags Key=Project,Value=dispatch \
  --profile dispatch

# Wait and get endpoint
aws elasticache wait replication-group-available \
  --replication-group-id dispatch-redis --profile dispatch

REDIS_ENDPOINT=$(aws elasticache describe-replication-groups \
  --replication-group-id dispatch-redis \
  --query 'ReplicationGroups[0].NodeGroups[0].PrimaryEndpoint.Address' \
  --output text --profile dispatch)
echo "Redis: $REDIS_ENDPOINT"
```

> **Note:** The Redis endpoint uses TLS. Your `config.py` REDIS_URL must include `rediss://` (double-s) when `transit-encryption-enabled` is true.

---

## 4. S3 Buckets

Three buckets are needed for the platform.

### 4.1 Imports bucket (CSV uploads)

```bash
aws s3api create-bucket \
  --bucket dispatch-imports-$AWS_ACCOUNT_ID \
  --region $AWS_REGION \
  $([ "$AWS_REGION" != "us-east-1" ] && echo "--create-bucket-configuration LocationConstraint=$AWS_REGION") \
  --profile dispatch

# Block all public access
aws s3api put-public-access-block \
  --bucket dispatch-imports-$AWS_ACCOUNT_ID \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --profile dispatch

# Lifecycle: delete raw uploads after 30 days
aws s3api put-bucket-lifecycle-configuration \
  --bucket dispatch-imports-$AWS_ACCOUNT_ID \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "expire-raw-uploads",
      "Status": "Enabled",
      "Filter": {"Prefix": "raw/"},
      "Expiration": {"Days": 30}
    }]
  }' --profile dispatch
```

### 4.2 Archives bucket (event/message parquet archives)

```bash
aws s3api create-bucket \
  --bucket dispatch-archives-$AWS_ACCOUNT_ID \
  --region $AWS_REGION \
  $([ "$AWS_REGION" != "us-east-1" ] && echo "--create-bucket-configuration LocationConstraint=$AWS_REGION") \
  --profile dispatch

aws s3api put-public-access-block \
  --bucket dispatch-archives-$AWS_ACCOUNT_ID \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --profile dispatch

# Enable versioning on archives bucket
aws s3api put-bucket-versioning \
  --bucket dispatch-archives-$AWS_ACCOUNT_ID \
  --versioning-configuration Status=Enabled \
  --profile dispatch

# Transition to Glacier after 90 days, delete after 365
aws s3api put-bucket-lifecycle-configuration \
  --bucket dispatch-archives-$AWS_ACCOUNT_ID \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "glacier-transition",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [{"Days": 90, "StorageClass": "GLACIER"}],
      "Expiration": {"Days": 365}
    }]
  }' --profile dispatch
```

### 4.3 ML artifacts bucket

```bash
aws s3api create-bucket \
  --bucket dispatch-ml-$AWS_ACCOUNT_ID \
  --region $AWS_REGION \
  $([ "$AWS_REGION" != "us-east-1" ] && echo "--create-bucket-configuration LocationConstraint=$AWS_REGION") \
  --profile dispatch

aws s3api put-public-access-block \
  --bucket dispatch-ml-$AWS_ACCOUNT_ID \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --profile dispatch

aws s3api put-bucket-versioning \
  --bucket dispatch-ml-$AWS_ACCOUNT_ID \
  --versioning-configuration Status=Enabled \
  --profile dispatch
```

---

## 5. AWS Secrets Manager

Store every secret here. Never hardcode credentials in environment variables or Dockerfiles.

```bash
# RDS master password (from §2.3)
aws secretsmanager create-secret \
  --name dispatch/prod/db-password \
  --description "RDS master password" \
  --secret-string "{\"password\":\"$DB_PASSWORD\"}" \
  --profile dispatch

# App DB password (set a different one for dispatch_app user)
APP_DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)
aws secretsmanager create-secret \
  --name dispatch/prod/db-app-password \
  --secret-string "{\"password\":\"$APP_DB_PASSWORD\",\"username\":\"dispatch_app\",\"host\":\"$DB_ENDPOINT\",\"port\":5432,\"dbname\":\"dispatch\"}" \
  --profile dispatch

# Django/FastAPI secret key
SECRET_KEY=$(openssl rand -hex 64)
aws secretsmanager create-secret \
  --name dispatch/prod/secret-key \
  --secret-string "{\"key\":\"$SECRET_KEY\"}" \
  --profile dispatch

# Add more secrets as needed (Cloudflare API token, SES SMTP credentials if used, etc.)
# aws secretsmanager create-secret --name dispatch/prod/cloudflare-token ...
```

**Referencing secrets in ECS task definitions:**

In your ECS task definition JSON, use the `secrets` key (not `environment`):
```json
"secrets": [
  {
    "name": "DB_PASSWORD",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:dispatch/prod/db-app-password:password::"
  }
]
```

> **Critical:** When a secret is rotated, ECS does not auto-update running tasks. You must force a new deployment: `aws ecs update-service --cluster dispatch --service dispatch-api --force-new-deployment`.

---

## 6. IAM Roles for ECS

### 6.1 ECS task execution role

This is the role ECS uses to pull images from ECR and read secrets from Secrets Manager.

```bash
# Create the role
aws iam create-role \
  --role-name dispatch-ecs-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' --profile dispatch

# Attach the managed execution policy
aws iam attach-role-policy \
  --role-name dispatch-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --profile dispatch

# Allow reading from Secrets Manager
aws iam put-role-policy \
  --role-name dispatch-ecs-execution-role \
  --policy-name dispatch-secrets-read \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:'"$AWS_REGION"':'"$AWS_ACCOUNT_ID"':secret:dispatch/*"
    }]
  }' --profile dispatch
```

### 6.2 ECS task role

This is what your *application code* uses (for S3, SES, SNS, etc.).

```bash
aws iam create-role \
  --role-name dispatch-ecs-task-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' --profile dispatch

# S3 access
aws iam put-role-policy \
  --role-name dispatch-ecs-task-role \
  --policy-name dispatch-s3-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject","s3:ListBucket"],
        "Resource": [
          "arn:aws:s3:::dispatch-imports-'"$AWS_ACCOUNT_ID"'",
          "arn:aws:s3:::dispatch-imports-'"$AWS_ACCOUNT_ID"'/*",
          "arn:aws:s3:::dispatch-archives-'"$AWS_ACCOUNT_ID"'",
          "arn:aws:s3:::dispatch-archives-'"$AWS_ACCOUNT_ID"'/*",
          "arn:aws:s3:::dispatch-ml-'"$AWS_ACCOUNT_ID"'",
          "arn:aws:s3:::dispatch-ml-'"$AWS_ACCOUNT_ID"'/*"
        ]
      }
    ]
  }' --profile dispatch

# SES send permissions (least privilege — sending only)
aws iam put-role-policy \
  --role-name dispatch-ecs-task-role \
  --policy-name dispatch-ses-send \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail",
        "ses:GetSendQuota",
        "ses:GetSendStatistics",
        "ses:ListIdentities",
        "ses:GetIdentityVerificationAttributes",
        "ses:GetIdentityDkimAttributes",
        "ses:CreateEmailIdentity",
        "ses:DeleteEmailIdentity",
        "ses:PutEmailIdentityDkimSigningAttributes",
        "ses:PutEmailIdentityMailFromAttributes",
        "ses:PutSuppressedDestination",
        "ses:GetSuppressedDestination",
        "ses:DeleteSuppressedDestination",
        "ses:ListSuppressedDestinations",
        "ses:CreateConfigurationSet",
        "ses:CreateConfigurationSetEventDestination"
      ],
      "Resource": "*"
    }]
  }' --profile dispatch

# SNS publish (for any platform-side SNS calls)
aws iam put-role-policy \
  --role-name dispatch-ecs-task-role \
  --policy-name dispatch-sns-publish \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["sns:Publish","sns:CreateTopic","sns:Subscribe","sns:ListSubscriptionsByTopic"],
      "Resource": "arn:aws:sns:'"$AWS_REGION"':'"$AWS_ACCOUNT_ID"':dispatch-*"
    }]
  }' --profile dispatch
```

---

## 7. ECR — Container Registry

One repository per service.

```bash
for SERVICE in api worker webhook scheduler; do
  aws ecr create-repository \
    --repository-name dispatch/$SERVICE \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    --profile dispatch
done

# Log Docker into ECR
aws ecr get-login-password --region $AWS_REGION --profile dispatch | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### 7.1 Build and push images

```bash
# From the repo root (after building your Docker images)
TAG=$(git rev-parse --short HEAD)

for SERVICE in api worker webhook scheduler; do
  docker build -f infra/Dockerfile.$SERVICE -t dispatch/$SERVICE:$TAG .
  docker tag dispatch/$SERVICE:$TAG \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/dispatch/$SERVICE:$TAG
  docker push \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/dispatch/$SERVICE:$TAG
done
```

---

## 8. ECS — Fargate Cluster & Services

### 8.1 Create the cluster

```bash
aws ecs create-cluster \
  --cluster-name dispatch \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
  --profile dispatch
```

### 8.2 CloudWatch log groups

```bash
for SERVICE in api worker webhook scheduler; do
  aws logs create-log-group \
    --log-group-name /ecs/dispatch/$SERVICE \
    --profile dispatch
  aws logs put-retention-policy \
    --log-group-name /ecs/dispatch/$SERVICE \
    --retention-in-days 30 \
    --profile dispatch
done
```

### 8.3 Task definition template

Save this as `infra/task-definition-api.json`, substituting the values:

```json
{
  "family": "dispatch-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/dispatch-ecs-execution-role",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/dispatch-ecs-task-role",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/dispatch/api:TAG",
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "environment": [
        {"name": "APP_ENV", "value": "production"},
        {"name": "AWS_REGION", "value": "us-east-1"}
      ],
      "secrets": [
        {"name": "DATABASE_URL",
         "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:dispatch/prod/db-app-password"},
        {"name": "SECRET_KEY",
         "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:dispatch/prod/secret-key:key::"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dispatch/api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/healthz || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      }
    }
  ]
}
```

Register the task definition:
```bash
aws ecs register-task-definition \
  --cli-input-json file://infra/task-definition-api.json \
  --profile dispatch
```

Create similar task definitions for `worker`, `webhook`, and `scheduler` — same pattern, different image and entry point.

### 8.4 Application Load Balancer

```bash
# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name dispatch-alb \
  --subnets $PUB_A $PUB_B \
  --security-groups $SG_ALB \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text --profile dispatch)

# Target group for API
TG_API=$(aws elbv2 create-target-group \
  --name dispatch-api-tg \
  --protocol HTTP --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /healthz \
  --query 'TargetGroups[0].TargetGroupArn' --output text --profile dispatch)

# HTTPS listener (requires an ACM certificate — see §8.5)
# aws elbv2 create-listener --load-balancer-arn $ALB_ARN \
#   --protocol HTTPS --port 443 \
#   --certificates CertificateArn=<ACM_CERT_ARN> \
#   --default-actions Type=forward,TargetGroupArn=$TG_API --profile dispatch
```

### 8.5 ACM Certificate

```bash
# Request a certificate for your domain
aws acm request-certificate \
  --domain-name "dispatch.yourdomain.com" \
  --validation-method DNS \
  --profile dispatch
# Follow the console output to add the CNAME validation record in your DNS provider.
```

### 8.6 ECS Services

```bash
# API service
aws ecs create-service \
  --cluster dispatch \
  --service-name dispatch-api \
  --task-definition dispatch-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration \
    "awsvpcConfiguration={subnets=[$PRIV_A,$PRIV_B],securityGroups=[$SG_ECS],assignPublicIp=DISABLED}" \
  --load-balancers \
    "targetGroupArn=$TG_API,containerName=api,containerPort=8000" \
  --health-check-grace-period-seconds 30 \
  --profile dispatch

# Worker service (no LB)
aws ecs create-service \
  --cluster dispatch \
  --service-name dispatch-worker \
  --task-definition dispatch-worker \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration \
    "awsvpcConfiguration={subnets=[$PRIV_A,$PRIV_B],securityGroups=[$SG_ECS],assignPublicIp=DISABLED}" \
  --profile dispatch

# Webhook service (needs its own target group and ALB listener rule)
# Follow the same pattern as the API service on port 8001
```

---

## 9. Amazon SES — Full Setup

This is the most critical section. Follow every step in order.

### 9.1 Sandbox status — check and request production

**By default, SES is in sandbox mode.** In sandbox you can only send to verified addresses, max 200/day, max 1/second.

**Step 1:** Check current sandbox status:
```
AWS Console → SES → Account dashboard → Sending
```
It will show whether you're in sandbox or production.

**Step 2:** Request production access:
```
AWS Console → SES → Account dashboard → Request production access
```
Fill in the form:
- **Mail type:** Marketing/Transactional
- **Website URL:** your platform URL
- **Use case description:** Write a clear description. Example:
  > "dispatch is an internal bulk-email platform used by our company to send marketing campaigns to our opt-in subscriber lists. We maintain a suppression list, implement hard-bounce and complaint processing, and comply with CAN-SPAM/GDPR. We expect to send approximately 10,000-75,000 emails per day initially."
- **Sending volume:** Your target for the next 24 hours and per month.

AWS typically responds within 24 hours. **Do not attempt high-volume sending in sandbox.**

### 9.2 Verify your sending domain

For each domain you send from:

```bash
DOMAIN="yoursendingdomain.com"

# Create the SES identity
aws sesv2 create-email-identity \
  --email-identity $DOMAIN \
  --dkim-signing-attributes SigningAttributesOrigin=AWS_SES \
  --profile dispatch

# Get the DKIM CNAME records to add to your DNS
aws sesv2 get-email-identity \
  --email-identity $DOMAIN \
  --query 'DkimAttributes.Tokens' \
  --output text --profile dispatch
```

This returns three tokens. Add three CNAME DNS records to your domain:
```
<token1>._domainkey.<domain>  CNAME  <token1>.dkim.amazonses.com
<token2>._domainkey.<domain>  CNAME  <token2>.dkim.amazonses.com
<token3>._domainkey.<domain>  CNAME  <token3>.dkim.amazonses.com
```

> DNS propagation can take up to 72 hours. SES will automatically verify once it detects the records.

### 9.3 Configure SPF

Add or merge this TXT record on your domain's DNS:
```
yoursendingdomain.com  TXT  "v=spf1 include:amazonses.com ~all"
```

> If a TXT record already exists, **add** `include:amazonses.com` to it. Never create duplicate TXT records.

### 9.4 Configure MAIL FROM (custom bounce domain)

This makes your bounce handling cleaner and improves deliverability:

```bash
aws sesv2 put-email-identity-mail-from-attributes \
  --email-identity $DOMAIN \
  --mail-from-domain "mail.$DOMAIN" \
  --behavior-on-mx-failure USE_DEFAULT_VALUE \
  --profile dispatch
```

Add these DNS records for `mail.yoursendingdomain.com`:
```
mail.yoursendingdomain.com  MX      10  feedback-smtp.us-east-1.amazonses.com
mail.yoursendingdomain.com  TXT     "v=spf1 include:amazonses.com ~all"
```

### 9.5 Configure DMARC

Add this TXT record on `_dmarc.yoursendingdomain.com`:
```
_dmarc.yoursendingdomain.com  TXT  "v=DMARC1; p=none; rua=mailto:dmarc-reports@yoursendingdomain.com; ruf=mailto:dmarc-reports@yoursendingdomain.com; pct=100"
```

Start with `p=none` (monitoring). After 30 days of clean data, change to `p=quarantine`, then `p=reject`.

### 9.6 Create a SES configuration set

One configuration set per sending domain. This is where SNS event routing is attached.

```bash
aws sesv2 create-configuration-set \
  --configuration-set-name dispatch-$DOMAIN \
  --profile dispatch

# Associate the domain identity with this config set
# (done automatically when you set the ConfigurationSetName on your SendEmail calls)
```

### 9.7 Create SNS topic for SES events

```bash
SNS_TOPIC_ARN=$(aws sns create-topic \
  --name dispatch-ses-events \
  --profile dispatch \
  --query TopicArn --output text)
echo "SNS Topic: $SNS_TOPIC_ARN"
```

### 9.8 Wire SES → SNS event destination

```bash
aws sesv2 create-configuration-set-event-destination \
  --configuration-set-name dispatch-$DOMAIN \
  --event-destination-name ses-to-sns \
  --event-destination '{
    "Enabled": true,
    "MatchingEventTypes": [
      "SEND", "REJECT", "BOUNCE", "COMPLAINT", "DELIVERY",
      "OPEN", "CLICK", "RENDERING_FAILURE", "DELIVERY_DELAY"
    ],
    "SnsDestination": {
      "TopicArn": "'"$SNS_TOPIC_ARN"'"
    }
  }' --profile dispatch
```

### 9.9 Subscribe your webhook to the SNS topic

After your webhook service is deployed and publicly accessible:

```bash
WEBHOOK_URL="https://webhook.yourdomain.com/sns"

aws sns subscribe \
  --topic-arn $SNS_TOPIC_ARN \
  --protocol https \
  --notification-endpoint $WEBHOOK_URL \
  --profile dispatch
```

SNS will immediately send a `SubscriptionConfirmation` message to your webhook URL. Your `apps/webhook/sns_verify.py` must fetch the `SubscribeURL` to confirm the subscription. Until it confirms, events will not be delivered.

**Verify the subscription is confirmed:**
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn $SNS_TOPIC_ARN \
  --query 'Subscriptions[*].{Endpoint:Endpoint,Status:SubscriptionArn}' \
  --profile dispatch
```
`SubscriptionArn` should show a real ARN (not `PendingConfirmation`).

### 9.10 Verify end-to-end

```bash
# Send a test email to a verified address (works in sandbox too)
aws sesv2 send-email \
  --from-email-address "test@$DOMAIN" \
  --destination "ToAddresses=you@youremail.com" \
  --content '{"Simple":{"Subject":{"Data":"Dispatch test"},"Body":{"Text":{"Data":"Test send"}}}}' \
  --configuration-set-name dispatch-$DOMAIN \
  --profile dispatch
```

Check your webhook logs — you should receive a `Delivery` event from SNS within 60 seconds.

### 9.11 Sending quota

After exiting sandbox, check your quota:
```bash
aws sesv2 get-account --profile dispatch \
  --query 'SendQuota'
```
Default production quota: 50,000 sends/day. For 75K+/day, request an increase:
```
AWS Console → SES → Account dashboard → Request increase
```

---

## 10. SES Account-Level Suppression List

Enable this once, globally. The platform syncs its own suppression list against this.

```bash
# Enable account-level suppression for bounces and complaints
aws sesv2 put-account-suppression-attributes \
  --suppressed-reasons BOUNCE COMPLAINT \
  --profile dispatch
```

---

## 11. Run Alembic Migrations

Once your RDS instance is reachable (from a bastion, or from an ECS one-off task):

```bash
# As a one-off ECS task using the migrations image
aws ecs run-task \
  --cluster dispatch \
  --task-definition dispatch-api \
  --launch-type FARGATE \
  --network-configuration \
    "awsvpcConfiguration={subnets=[$PRIV_A],securityGroups=[$SG_ECS],assignPublicIp=DISABLED}" \
  --overrides '{
    "containerOverrides": [{
      "name": "api",
      "command": ["alembic", "upgrade", "head"]
    }]
  }' --profile dispatch
```

Watch the logs in CloudWatch `/ecs/dispatch/api` to confirm the migration succeeded.

---

## 12. Post-Deployment Verification Checklist

Run through this after every fresh deployment.

| Check | Command / Action |
|---|---|
| API health | `curl https://dispatch.yourdomain.com/healthz` → `{"status":"ok"}` |
| Webhook health | `curl https://webhook.yourdomain.com/healthz` → `{"status":"ok"}` |
| DB migrations applied | `alembic current` matches `alembic heads` |
| Redis reachable | Worker logs show "Connected to Redis" |
| SES domain verified | `aws sesv2 get-email-identity --email-identity $DOMAIN --query 'VerifiedForSendingStatus'` → `true` |
| DKIM enabled | `aws sesv2 get-email-identity --email-identity $DOMAIN --query 'DkimAttributes.Status'` → `SUCCESS` |
| SNS subscription confirmed | See §9.9 |
| Test email received | See §9.10 |
| Bounce event received on webhook | Check CloudWatch logs after the test send |
| Suppression list synced | Hit `GET /suppression` and verify it matches SES account suppression |

---

## 13. Sending Limits by Phase

| Phase | Target volume | Action needed |
|---|---|---|
| MVP | 10K–75K/day | Request production access (§9.1) |
| Scale | 75K–300K/day | Request sending quota increase in SES console |
| 1M/Day | 1M+/day | Multi-region SES + dedicated IP pool (request dedicated IPs from SES console) |

To request dedicated IPs:
```
AWS Console → SES → Dedicated IPs → Request dedicated IPs
```
Dedicated IPs are allocated per region and should only be used once your warmup schedule (Sprint 15 backend) is running. Do not use dedicated IPs without warming them.

---

## 14. Cost Estimates (Reference Only)

| Service | Rough monthly cost at MVP (10–75K sends/day) |
|---|---|
| SES | ~$0.10 per 1,000 sends = $3–$22/month |
| RDS db.t4g.medium | ~$55/month |
| ElastiCache cache.t4g.small (×2) | ~$50/month |
| ECS Fargate (2 tasks × 4 services) | ~$40–$80/month |
| ALB | ~$22/month |
| NAT Gateway | ~$35/month (data dependent) |
| S3 | Negligible at MVP volumes |
| **Total estimate** | **~$200–$270/month at MVP** |

Costs scale with send volume, primarily via SES, Fargate task count, and NAT data transfer.

---

## Sources

- [Creating and verifying identities in Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html)
- [Easy DKIM in Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html)
- [Complying with DMARC in Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html)
- [Using a custom MAIL FROM domain](https://docs.aws.amazon.com/ses/latest/dg/mail-from.html)
- [Configuring Amazon SNS notifications for SES](https://docs.aws.amazon.com/ses/latest/dg/configure-sns-notifications.html)
- [Request production access (Moving out of SES sandbox)](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)
- [Managing your Amazon SES sending limits](https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas.html)
- [Amazon ECS task definitions for Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-tasks-services.html)
- [Pass Secrets Manager secrets through ECS environment variables](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)
- [Creating a node-based ElastiCache cluster for Redis](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/SubnetGroups.designing-cluster-pre.redis.html)
- [Controlling access with RDS security groups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.RDSSecurityGroups.html)
- [Setting an S3 Lifecycle configuration on a bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-set-lifecycle-configuration-intro.html)
- [Retaining multiple versions of objects with S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [Using Amazon ECR images with Amazon ECS](https://docs.aws.amazon.com/AmazonECR/latest/userguide/ECR_on_ECS.html)
