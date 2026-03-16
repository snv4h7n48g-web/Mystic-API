# Mystic API - AWS Bedrock Integration

Complete FastAPI backend with AWS Bedrock (Nova) integration for personalized astrology/tarot readings.

---

## 📂 Project Structure

```
mystic-api/
├── backend/                      # Python application code
│   ├── main.py                   # FastAPI application
│   ├── bedrock_service.py        # AWS Bedrock client
│   ├── astrology_engine.py       # Natal chart calculations
│   ├── geocoding_service.py      # Location service
│   ├── test_api.py               # Integration tests
│   ├── verify_bedrock.py         # AWS verification
│   ├── requirements.txt          # Python dependencies
│   └── .env.example              # Environment template
│
├── scripts/
│   ├── windows/                  # PowerShell scripts for Windows
│   │   ├── setup.ps1
│   │   ├── start.ps1
│   │   ├── test.ps1
│   │   ├── verify.ps1
│   │   └── stop.ps1
│   │
│   └── unix/                     # Bash scripts for Linux/Mac
│       ├── setup.sh
│       ├── start.sh
│       ├── test.sh
│       ├── verify.sh
│       └── stop.sh
│
├── docs/                         # Documentation
│   ├── README.md                 # Technical documentation
│   ├── WINDOWS.md                # Windows-specific guide
│   ├── QUICKSTART.md             # Quick reference
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── VENV_GUIDE.md             # Virtual environment guide
│   └── CHECKLIST.md              # Setup checklist
│
├── docker-compose.yml            # PostgreSQL container
└── README.md                     # This file
```

---

## 🚀 Quick Start

### For Windows Users

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
copy .env.example .env
notepad .env  # Add your AWS credentials

# 6. Start database (from root directory)
cd ..
docker-compose up -d

# 7. Start API (from backend directory)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 8. Test (in another terminal)
cd backend
.\venv\Scripts\Activate.ps1
python test_api.py
```

### For Linux/Mac Users

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
nano .env  # Add your AWS credentials

# 6. Start database (from root directory)
cd ..
docker-compose up -d

# 7. Start API (from backend directory)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 8. Test (in another terminal)
cd backend
source venv/bin/activate
python test_api.py
```

---

## 📋 Prerequisites

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Docker Desktop** - [Download](https://docs.docker.com/get-docker/)
3. **AWS Account** with Bedrock access
4. **AWS Credentials** (Access Key ID + Secret Key)
5. **Nova Models** enabled in AWS Bedrock console

---

## ⚙️ AWS Setup

### 1. Get AWS Credentials

1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to IAM → Users → Create user
3. Attach policy: `AmazonBedrockFullAccess`
4. Create Access Key → Download credentials

### 2. Enable Nova Models

1. Go to [Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click "Model access" (left sidebar)
3. Click "Manage model access"
4. Enable:
   - ✅ Amazon Nova Lite
   - ✅ Amazon Nova Pro
5. Click "Save changes"
6. Wait for "Access granted" status

### 3. Configure .env File

Edit `backend/.env`:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
BEDROCK_PREVIEW_MODEL=us.amazon.nova-lite-v1:0
BEDROCK_FULL_MODEL=us.amazon.nova-pro-v1:0
```

---

## 🎯 API Endpoints

Once running, API is available at: **http://localhost:8000**

- **Health Check:** `GET /health`
- **API Docs:** `http://localhost:8000/docs`
- **Create Session:** `POST /v1/sessions`
- **Update Session:** `PATCH /v1/sessions/{session_id}`
- **Generate Preview:** `POST /v1/sessions/{session_id}/preview`
- **Generate Reading:** `POST /v1/sessions/{session_id}/reading`
- **Get Costs:** `GET /v1/sessions/{session_id}/cost`

---

## 💰 Cost Analysis

**Per Reading:**
- Preview (Nova Lite): ~$0.06
- Full Reading (Nova Pro): ~$0.10
- Total: ~$0.16 per paid user

**Unit Economics:**
- Revenue: $1.99
- Apple cut: -$0.60
- Net revenue: $1.39
- Costs: -$0.54 (amortized)
- **Gross margin: $0.85 (61%)**

---

## 📖 Documentation

All documentation is in the `docs/` directory:

- **WINDOWS.md** - Windows-specific instructions
- **QUICKSTART.md** - Daily command reference
- **DEPLOYMENT.md** - Production deployment guide
- **README.md** - Technical architecture details
- **VENV_GUIDE.md** - Virtual environment guide
- **CHECKLIST.md** - Step-by-step verification

---

## 🔧 Development Workflow

### Daily Development

**Terminal 1 (Database):**
```bash
docker-compose up -d
```

**Terminal 2 (API Server):**
```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
uvicorn main:app --reload
```

**Terminal 3 (Testing):**
```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
python test_api.py
```

---

## 🐛 Troubleshooting

### Python not found
- Install Python 3.11+ from python.org
- **Windows:** Check "Add Python to PATH" during installation
- **Mac:** `brew install python@3.11`
- **Linux:** `sudo apt install python3.11`

### Docker not running
- Start Docker Desktop application
- Wait for it to show "running" status

### AWS credentials error
- Check `.env` file has real credentials (not "your_key_here")
- Run `python verify_bedrock.py` to diagnose

### Port 8000 in use
- **Windows:** `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`
- **Linux/Mac:** `lsof -ti:8000 | xargs kill -9`

---

## ✅ Verification

Run these commands to verify setup:

```bash
# Check Python
python --version  # or python3 --version

# Check Docker
docker --version

# Check database
docker ps | grep postgres

# Check API (after starting)
curl http://localhost:8000/health

# Verify AWS
cd backend
python verify_bedrock.py  # or python3
```

---

## 🚀 Next Steps

1. ✅ **Local deployment** (you are here)
2. ⏭️ Add Apple IAP verification
3. ⏭️ Deploy to AWS EC2/ECS
4. ⏭️ Build iOS client
5. ⏭️ Add rate limiting (Redis)
6. ⏭️ Implement RAG system

See `docs/DEPLOYMENT.md` for production deployment guide.

---

## 📞 Support

- Review `docs/` for comprehensive guides
- Check `docs/CHECKLIST.md` for verification steps
- Run `verify_bedrock.py` for AWS diagnostics

---

## 📝 License

Proprietary - All rights reserved

---

**Version:** 0.1.0  
**Last Updated:** 2026-01-30  
**Platform:** AWS Bedrock + FastAPI + PostgreSQL
