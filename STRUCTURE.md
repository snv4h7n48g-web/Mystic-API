# Mystic API - Complete Project Structure

## 📦 Package Contents

**Total Files:** 27  
**Size:** 35 KB (compressed)

---

## 📂 Directory Tree

```
mystic-api/
│
├── README.md                           # Project overview & quick start
├── .gitignore                          # Git ignore rules
├── docker-compose.yml                  # PostgreSQL container config
│
├── backend/                            # Python application (8 files)
│   ├── main.py                         # FastAPI application
│   ├── bedrock_service.py              # AWS Bedrock client
│   ├── astrology_engine.py             # Natal chart calculations
│   ├── geocoding_service.py            # Location to coordinates
│   ├── test_api.py                     # Integration tests
│   ├── verify_bedrock.py               # AWS verification tool
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Environment template
│
├── scripts/                            # Automation scripts (10 files)
│   ├── windows/                        # PowerShell scripts for Windows
│   │   ├── setup.ps1                   # Initial setup
│   │   ├── start.ps1                   # Start server
│   │   ├── test.ps1                    # Run tests
│   │   ├── verify.ps1                  # Check AWS
│   │   └── stop.ps1                    # Stop services
│   │
│   └── unix/                           # Bash scripts for Linux/Mac
│       ├── setup.sh                    # Initial setup
│       ├── start.sh                    # Start server
│       ├── test.sh                     # Run tests
│       ├── verify.sh                   # Check AWS
│       └── stop.sh                     # Stop services
│
└── docs/                               # Documentation (6 files)
    ├── README.md                       # Technical documentation
    ├── WINDOWS.md                      # Windows-specific guide
    ├── QUICKSTART.md                   # Quick reference
    ├── DEPLOYMENT.md                   # Deployment guide
    ├── VENV_GUIDE.md                   # Virtual environment guide
    └── CHECKLIST.md                    # Setup checklist
```

---

## 🎯 Key Files

### Backend (Python Application)

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | ~400 | FastAPI app with all endpoints |
| `bedrock_service.py` | ~350 | AWS Bedrock integration (Nova Lite/Pro) |
| `astrology_engine.py` | ~300 | Sun/Moon/Rising calculations |
| `geocoding_service.py` | ~100 | Location service |
| `test_api.py` | ~350 | End-to-end integration tests |
| `verify_bedrock.py` | ~300 | AWS diagnostics tool |
| `requirements.txt` | ~10 | Python dependencies |
| `.env.example` | ~15 | Configuration template |

### Scripts (Automation)

| File | Purpose |
|------|---------|
| `setup.ps1/.sh` | One-time environment setup |
| `start.ps1/.sh` | Start API server |
| `test.ps1/.sh` | Run integration tests |
| `verify.ps1/.sh` | Check AWS/Bedrock access |
| `stop.ps1/.sh` | Stop services |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Technical architecture & API docs |
| `WINDOWS.md` | Windows-specific instructions |
| `QUICKSTART.md` | Daily command reference |
| `DEPLOYMENT.md` | Production deployment guide |
| `VENV_GUIDE.md` | Virtual environment explained |
| `CHECKLIST.md` | Step-by-step verification |

---

## 🚀 Installation

### Extract the Archive

**Windows:**
```powershell
# Extract to C:\Projects\
tar -xzf mystic-api-clean.tar.gz
cd mystic-api-clean
```

**Linux/Mac:**
```bash
# Extract to ~/projects/
tar -xzf mystic-api-clean.tar.gz
cd mystic-api-clean
```

### Follow Quick Start

Open `README.md` and follow the Quick Start section for your operating system.

---

## 🎓 Learning Path

**1. First Time (10 minutes):**
- Read root `README.md`
- Navigate to `backend/`
- Create virtual environment
- Install dependencies
- Configure `.env`
- Start database
- Start server

**2. Daily Use:**
- `cd backend`
- Activate venv
- `uvicorn main:app --reload`
- Test with `python test_api.py`

**3. Deep Dive:**
- Read `docs/README.md` for architecture
- Review `bedrock_service.py` for LLM integration
- Check `main.py` for API endpoints

---

## ✅ What's Included

**✅ Complete AWS Bedrock Integration**
- Preview generation (Nova Lite, ~$0.06)
- Full reading generation (Nova Pro, ~$0.10)
- Cost tracking per session

**✅ Deterministic Astrology Engine**
- Sun/Moon/Rising sign calculations
- Element dominance
- Basic aspects

**✅ FastAPI Backend**
- Session management
- Tarot card drawing
- Preview/reading endpoints
- Cost analytics

**✅ Complete Documentation**
- Quick start guides
- Windows/Linux/Mac instructions
- Troubleshooting
- Production deployment

**✅ Automation Scripts**
- Setup (creates venv, installs deps)
- Start (runs server)
- Test (integration tests)
- Verify (checks AWS)

---

## 📊 Tech Stack

- **Backend:** Python 3.11+ / FastAPI
- **Database:** PostgreSQL 16 (Docker)
- **LLM:** AWS Bedrock (Nova Lite + Nova Pro)
- **Deployment:** Docker Compose (local), AWS ECS (production)

---

## 💰 Cost Model

**Per Reading:**
- Preview: $0.06 (shown to all users)
- Full reading: $0.10 (after $1.99 payment)
- Infrastructure: $0.04
- **Total cost:** $0.16 per paid user

**Unit Economics:**
- Revenue (after Apple cut): $1.39
- Costs (amortized): -$0.54
- **Gross margin: $0.85 (61%)**

---

## 🎯 Next Steps After Setup

1. ✅ **Local deployment** (follow README.md)
2. ⏭️ Verify AWS Bedrock access
3. ⏭️ Test preview generation
4. ⏭️ Test full reading generation
5. ⏭️ Check cost tracking
6. ⏭️ Review unit economics

Then:
- Add Apple IAP verification
- Deploy to production (AWS)
- Build iOS client
- Scale to real users

---

## 📞 Support

All documentation is self-contained in the `docs/` directory.

**Quick Answers:**
- Windows setup → `docs/WINDOWS.md`
- Daily commands → `docs/QUICKSTART.md`
- AWS issues → Run `verify_bedrock.py`
- Deployment → `docs/DEPLOYMENT.md`

---

**Version:** 0.1.0  
**Created:** 2026-01-30  
**Ready to deploy:** Yes ✅
