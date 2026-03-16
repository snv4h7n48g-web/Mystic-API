# Mystic API - Deployment Checklist

## ✅ Pre-Deployment Checklist

### AWS Setup
- [ ] AWS account created
- [ ] IAM user created with programmatic access
- [ ] IAM policy attached (bedrock:InvokeModel)
- [ ] Access key ID and secret key downloaded
- [ ] Bedrock console accessed
- [ ] Nova Lite model access enabled
- [ ] Nova Pro model access enabled
- [ ] Model access status shows "Access granted"

### Local Environment
- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Docker Desktop installed and running
- [ ] Git installed (if cloning from repo)
- [ ] Terminal/command line access

---

## 🚀 Deployment Steps (In Order)

### Step 1: Download/Clone Project
```bash
# If from Git
git clone <your-repo-url>
cd mystic-api

# Or extract ZIP file
unzip mystic-api.zip
cd mystic-api
```
**Status check:** ✅ Files present: `main.py`, `setup.sh`, `requirements.txt`

---

### Step 2: Make Scripts Executable
```bash
chmod +x setup.sh start.sh test.sh stop.sh verify_bedrock.py
```
**Status check:** ✅ Can run `./setup.sh --help` without permission errors

---

### Step 3: Run Setup Script
```bash
./setup.sh
```

**What this does:**
1. ✓ Checks Python version (3.11+)
2. ✓ Checks Docker installation
3. ✓ Creates virtual environment
4. ✓ Installs Python packages
5. ✓ Copies .env.example to .env
6. ✓ Prompts for AWS credentials
7. ✓ Starts PostgreSQL container
8. ✓ Tests database connection
9. ✓ Tests Bedrock API connection

**Expected output:**
```
============================================
  Setup Complete!
============================================

✓ Database: Running on localhost:5432
✓ API: Ready to start
```

**Status check:** ✅ No red "✗" errors in output

---

### Step 4: Configure AWS Credentials

If setup.sh prompts you or if you need to edit manually:

```bash
nano .env
# Or use your preferred editor: vim, code, etc.
```

**Required values:**
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...your_key_here
AWS_SECRET_ACCESS_KEY=wJal...your_secret_here
```

**Where to get these:**
1. AWS Console → IAM → Users → Your User
2. "Security credentials" tab
3. "Create access key"
4. Download CSV or copy values

**Status check:** ✅ File contains real AWS credentials (not "your_key_here")

---

### Step 5: Verify Bedrock Access
```bash
python3 verify_bedrock.py
```

**Expected output:**
```
1. Checking AWS Credentials
✓ AWS_ACCESS_KEY_ID: AKIA1234...
✓ AWS_SECRET_ACCESS_KEY: wJalrXUt...
✓ AWS_REGION: us-east-1

2. Testing Bedrock Service Access
✓ Bedrock service accessible
✓ Found 150+ foundation models

3. Checking Nova Model Availability
✓ Nova Lite found: us.amazon.nova-lite-v1:0
✓ Nova Pro found: us.amazon.nova-pro-v1:0

4. Testing Model Inference
✓ Inference successful!
  Response: Hello
  Input tokens: 12
  Output tokens: 2

✅ ALL CHECKS PASSED
```

**If you see errors:**
- ✗ AWS credentials → Check .env file
- ✗ Bedrock access → Check IAM permissions
- ✗ Nova models not found → Enable in Bedrock console
- ✗ Inference failed → Check model access status

**Status check:** ✅ All 4 checks passed with green ✓

---

### Step 6: Start API Server
```bash
./start.sh
```

**Expected output:**
```
✓ Starting FastAPI server...

API will be available at:
  - Main API: http://localhost:8000
  - Documentation: http://localhost:8000/docs
  - Health check: http://localhost:8000/health

Press Ctrl+C to stop the server

INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Status check:** 
✅ Server shows "startup complete"
✅ http://localhost:8000/health returns `{"ok": true}`

---

### Step 7: Run Integration Tests

**Open a NEW terminal** (keep server running in first terminal)

```bash
cd mystic-api
source venv/bin/activate  # Activate virtual environment
./test.sh
```

**Expected output:**
```
============================================
  MYSTIC API - BEDROCK INTEGRATION TEST
============================================

1. Testing Health Endpoint
✓ Health check passed

2. Creating Session
✓ Session created: abc123...

3. Updating Session with Birth Data
✓ Session updated with birth data

4. Generating Preview (Bedrock Nova Lite)
⏳ Calling Bedrock API... (this may take 5-10 seconds)
✓ Preview generated successfully

5. Generating Full Reading (Bedrock Nova Pro)
⏳ Calling Bedrock API... (this may take 10-15 seconds)
✓ Full reading generated successfully

6. Checking Cost Analytics
✓ Cost analytics retrieved

✅ ALL TESTS PASSED
```

**Status check:** 
✅ All 6 tests show green ✓
✅ No timeout or connection errors
✅ Costs shown are ~$0.06 + ~$0.10

---

## 🎯 Verification Matrix

| Component | Check | Expected Result | Status |
|-----------|-------|----------------|--------|
| Python | `python3 --version` | 3.11+ | ⬜ |
| Docker | `docker --version` | 20.10+ | ⬜ |
| Virtual Env | `source venv/bin/activate` | No errors | ⬜ |
| Database | `docker ps \| grep postgres` | Container running | ⬜ |
| .env File | `cat .env` | Real AWS credentials | ⬜ |
| Bedrock | `python3 verify_bedrock.py` | All checks passed | ⬜ |
| API Health | `curl localhost:8000/health` | `{"ok":true}` | ⬜ |
| Full Test | `python3 test_api.py` | All tests passed | ⬜ |

---

## 📊 Test Results Interpretation

### Good Test Output
```
Preview Cost:  $0.000060 ✓ (Normal range: $0.04-$0.08)
Reading Cost:  $0.000100 ✓ (Normal range: $0.08-$0.12)
Total Cost:    $0.000160 ✓
Gross Margin:  $1.23 ✓ (61% margin)
```

### Warning Signs
```
Preview Cost:  $0.000000 ⚠ (Model may not have run)
Preview Cost:  $0.500000 ⚠ (Cost unexpectedly high - check model)
Response time: 60s ⚠ (Should be <15s for full reading)
```

---

## 🚨 Common Issues & Fixes

### Issue 1: "Permission denied: ./setup.sh"
**Fix:**
```bash
chmod +x *.sh *.py
```

### Issue 2: "Cannot connect to Docker daemon"
**Fix:**
1. Start Docker Desktop application
2. Wait for Docker icon to show "running"
3. Retry: `docker ps`

### Issue 3: "Access denied to Bedrock service"
**Fix:**
```bash
# 1. Check IAM permissions in AWS Console
# 2. Verify policy includes:
#    - bedrock:ListFoundationModels
#    - bedrock:InvokeModel
# 3. Re-download access keys if needed
# 4. Update .env file
# 5. Rerun: python3 verify_bedrock.py
```

### Issue 4: "Nova models not found"
**Fix:**
```bash
# 1. Go to: https://console.aws.amazon.com/bedrock/
# 2. Click "Model access" in left sidebar
# 3. Click "Manage model access" button
# 4. Check boxes for:
#    ✓ Amazon Nova Lite
#    ✓ Amazon Nova Pro
# 5. Click "Save changes"
# 6. Wait 30 seconds
# 7. Rerun: python3 verify_bedrock.py
```

### Issue 5: "Port 8000 already in use"
**Fix:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --reload --port 8001
```

### Issue 6: "Module 'boto3' not found"
**Fix:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📞 Support Checklist

Before asking for help, confirm:
- [ ] Python version is 3.11+
- [ ] Docker Desktop is running
- [ ] Virtual environment is activated
- [ ] .env file has real AWS credentials
- [ ] `verify_bedrock.py` passes all checks
- [ ] Database container is running
- [ ] No error messages in server logs

**Logs to check:**
```bash
# API server logs (terminal where start.sh is running)
# Database logs
docker-compose logs -f

# Python errors
# (shown in terminal where test.sh is running)
```

---

## ✅ Success Criteria

Deployment is successful when:
1. ✅ `verify_bedrock.py` shows all checks passed
2. ✅ `test_api.py` shows all 6 tests passed
3. ✅ Preview generates unique teaser in 5-10 seconds
4. ✅ Full reading generates 7 sections in 10-15 seconds
5. ✅ Costs are approximately $0.06 + $0.10 = $0.16
6. ✅ Can create multiple sessions without errors
7. ✅ API docs accessible at http://localhost:8000/docs

---

## 🎓 Next Phase: Production

Once local testing is successful:
1. ✅ **Local deployment working**
2. ⏭️ Deploy to AWS EC2 or ECS (see DEPLOYMENT.md)
3. ⏭️ Setup production database (RDS PostgreSQL)
4. ⏭️ Configure domain and SSL
5. ⏭️ Add monitoring (CloudWatch)
6. ⏭️ Build iOS client
7. ⏭️ Integrate Apple IAP

See **DEPLOYMENT.md** for production deployment guide.

---

## 📝 Deployment Sign-Off

**Deployed by:** _______________  
**Date:** _______________  
**Environment:** ☐ Local ☐ Staging ☐ Production  
**All tests passed:** ☐ Yes ☐ No  
**Ready for next phase:** ☐ Yes ☐ No  

**Notes:**
```

```
