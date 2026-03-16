# Mystic API - Deployment Guide

## Quick Start (5 Minutes)

### Prerequisites

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Docker Desktop** - [Download](https://docs.docker.com/get-docker/)
3. **AWS Account** with Bedrock access - [Sign up](https://aws.amazon.com/)

### Step 1: Get AWS Credentials

1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **IAM** → **Users** → **Create user**
3. Attach policy: `AmazonBedrockFullAccess` (or custom policy below)
4. Create **Access Key** → Download credentials

**Custom IAM Policy** (minimal permissions):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 2: Enable Nova Models

1. Go to [Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click **Model access** (left sidebar)
3. Click **Manage model access**
4. Enable:
   - ✅ Amazon Nova Lite
   - ✅ Amazon Nova Pro
5. Click **Save changes**
6. Wait for status to show "Access granted" (~30 seconds)

### Step 3: Deploy Locally

```bash
# 1. Clone/download the project files
cd mystic-api

# 2. Run setup script (sets up everything)
chmod +x setup.sh start.sh test.sh stop.sh
./setup.sh

# Follow prompts to configure AWS credentials in .env file

# 3. Verify Bedrock access
chmod +x verify_bedrock.py
python3 verify_bedrock.py

# 4. Start the API server
./start.sh
```

The API will be available at: http://localhost:8000

### Step 4: Test the Integration

In a **new terminal**:

```bash
# Run integration tests
./test.sh
```

You should see:
```
✅ ALL TESTS PASSED
```

---

## Detailed Setup Steps

### Manual Setup (if scripts don't work)

#### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your AWS credentials:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
BEDROCK_PREVIEW_MODEL=us.amazon.nova-lite-v1:0
BEDROCK_FULL_MODEL=us.amazon.nova-pro-v1:0
```

#### 4. Start Database

```bash
docker-compose up -d
```

Wait 5 seconds for PostgreSQL to initialize.

#### 5. Verify Bedrock Access

```bash
python3 verify_bedrock.py
```

This will check:
- ✓ AWS credentials are valid
- ✓ Bedrock service is accessible
- ✓ Nova models are available
- ✓ Model inference works

#### 6. Start API Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 7. Test API (new terminal)

```bash
# Health check
curl http://localhost:8000/health

# Run full test suite
python3 test_api.py
```

---

## Troubleshooting

### Issue: "Access denied to Bedrock service"

**Solution:**
1. Check IAM permissions - user needs `bedrock:InvokeModel`
2. Verify credentials in `.env` are correct
3. Check AWS region is correct (us-east-1 recommended)

### Issue: "Nova models not found"

**Solution:**
1. Go to [Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click "Model access" → "Manage model access"
3. Enable Nova Lite and Nova Pro
4. Wait for "Access granted" status

### Issue: "Cannot connect to database"

**Solution:**
```bash
# Check if Docker is running
docker ps

# Restart database
docker-compose down
docker-compose up -d

# Wait 5 seconds and try again
```

### Issue: "ValidationException: Model not available in region"

**Solution:**
Nova models may not be available in all regions. Try these regions:
- `us-east-1` (N. Virginia) - **Recommended**
- `us-west-2` (Oregon)

Update `AWS_REGION` in `.env` and restart.

### Issue: Test shows "Preview generation failed"

**Solution:**
1. Run `python3 verify_bedrock.py` to diagnose
2. Check AWS CloudWatch logs for detailed errors
3. Verify Nova Lite model ID is correct in `.env`

---

## Production Deployment

### Option 1: AWS EC2

**1. Launch EC2 Instance**
```bash
# Ubuntu 22.04 LTS, t3.medium or larger
# Security group: Allow 8000, 5432 (internal only)
```

**2. Install Dependencies**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv docker.io docker-compose
sudo usermod -aG docker ubuntu
```

**3. Deploy Application**
```bash
git clone <your-repo>
cd mystic-api
./setup.sh
./start.sh
```

**4. Setup Nginx Reverse Proxy**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**5. Setup Systemd Service**
```ini
[Unit]
Description=Mystic API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/mystic-api
ExecStart=/home/ubuntu/mystic-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Option 2: AWS ECS (Container)

**1. Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Build and Push to ECR**
```bash
aws ecr create-repository --repository-name mystic-api
docker build -t mystic-api .
docker tag mystic-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/mystic-api:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/mystic-api:latest
```

**3. Create ECS Task Definition**
- Use Fargate
- Add environment variables from `.env`
- Use RDS PostgreSQL instead of Docker container

### Option 3: AWS Lambda (Serverless)

**Use Mangum adapter:**
```python
from mangum import Mangum
handler = Mangum(app)
```

Deploy via AWS SAM or Serverless Framework.

---

## Monitoring & Analytics

### Cost Tracking

Check per-session costs:
```bash
curl http://localhost:8000/v1/sessions/{session_id}/cost
```

Response:
```json
{
  "preview_cost_usd": 0.06,
  "reading_cost_usd": 0.10,
  "total_cost_usd": 0.16
}
```

### Database Queries

```sql
-- Total revenue potential
SELECT 
    COUNT(*) as total_sessions,
    COUNT(*) FILTER (WHERE status = 'preview_ready') as previews,
    COUNT(*) FILTER (WHERE status = 'complete') as paid_readings,
    SUM(preview_cost_usd) as total_preview_cost,
    SUM(reading_cost_usd) as total_reading_cost
FROM sessions;

-- Average costs
SELECT 
    AVG(preview_cost_usd) as avg_preview_cost,
    AVG(reading_cost_usd) as avg_reading_cost
FROM sessions 
WHERE preview_cost_usd IS NOT NULL;
```

### AWS CloudWatch

Monitor Bedrock API calls:
1. Go to CloudWatch Console
2. Metrics → Bedrock
3. Track:
   - InvocationCount
   - InvocationLatency
   - InputTokens / OutputTokens

---

## API Documentation

Once server is running, view interactive docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `setup.sh` | Initial setup - run once |
| `start.sh` | Start API server |
| `test.sh` | Run integration tests |
| `stop.sh` | Stop database containers |
| `verify_bedrock.py` | Check AWS/Bedrock config |

---

## Next Steps

1. ✅ **Local deployment working**
2. ⏭️ **Add Apple IAP verification** before `/reading` endpoint
3. ⏭️ **Implement rate limiting** (Redis)
4. ⏭️ **Deploy to production** (AWS EC2/ECS)
5. ⏭️ **Build iOS client** (Swift/SwiftUI)

---

## Support

**Common Issues:**
- Check logs: `docker-compose logs -f`
- Verify AWS credentials: `python3 verify_bedrock.py`
- Test database: `docker exec mystic_postgres pg_isready`

**AWS Documentation:**
- [Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
- [Nova Models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
