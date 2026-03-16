# Mystic API - Windows Deployment Guide

## 🪟 Windows-Specific Instructions

You're on Windows, so the bash scripts (`.sh` files) won't work. Use the PowerShell scripts (`.ps1` files) instead.

---

## ⚡ Quick Start (Windows)

### Step 1: Open PowerShell as Administrator

Right-click PowerShell → "Run as Administrator"

### Step 2: Allow Script Execution

```powershell
# Allow running PowerShell scripts (one-time setup)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Navigate to Project Directory

```powershell
cd C:\Projects\mystic-app\mystic-api
```

### Step 4: Run Setup

```powershell
.\setup.ps1
```

This will:
- Check Python 3.11+ is installed
- Check Docker Desktop is running
- Create virtual environment
- Install dependencies
- Start PostgreSQL
- Test AWS Bedrock connection

### Step 5: Verify Bedrock Access

```powershell
.\verify.ps1
```

### Step 6: Start Server

```powershell
.\start.ps1
```

### Step 7: Run Tests (New PowerShell Window)

Open a **new** PowerShell window:

```powershell
cd C:\Projects\mystic-app\mystic-api
.\test.ps1
```

---

## 📋 Windows Command Reference

### Daily Commands

```powershell
# Start server
.\start.ps1

# Run tests (in another window)
.\test.ps1

# Verify AWS
.\verify.ps1

# Stop everything
.\stop.ps1
```

### Manual Commands

```powershell
# Check Python version
python --version

# Check if Docker is running
docker ps

# Start database only
docker-compose up -d

# View database logs
docker-compose logs -f

# Stop database
docker-compose down
```

---

## 🐛 Common Windows Issues

### Issue 1: "python3: command not found"

**Windows uses `python`, not `python3`**

```powershell
# Check Python
python --version

# Should show: Python 3.11.x or higher
```

If not installed:
1. Download from https://www.python.org/downloads/
2. **Important:** Check "Add Python to PATH" during installation
3. Restart PowerShell

---

### Issue 2: "Cannot be loaded because running scripts is disabled"

**Error:**
```
.\setup.ps1 : File C:\...\setup.ps1 cannot be loaded because running 
scripts is disabled on this system.
```

**Fix:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Issue 3: Docker not running

**Error:** "Cannot connect to Docker daemon"

**Fix:**
1. Open Docker Desktop application
2. Wait for Docker icon to show "running" (in system tray)
3. Retry command

---

### Issue 4: Port 8000 already in use

**Find and kill process:**

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

---

### Issue 5: Virtual environment issues

**Fix:**

```powershell
# Remove old venv
Remove-Item -Recurse -Force venv

# Run setup again
.\setup.ps1
```

---

## 🔧 Manual Virtual Environment (Windows)

If you need to run commands manually:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Your prompt will show (venv)
(venv) PS C:\Projects\mystic-app\mystic-api>

# Now run Python commands
python verify_bedrock.py
python test_api.py
uvicorn main:app --reload

# Deactivate when done
deactivate
```

---

## 📂 Windows File Paths

Windows uses backslashes `\` instead of forward slashes `/`:

```powershell
# Correct Windows path
C:\Projects\mystic-app\mystic-api

# Python still works with forward slashes in code
"/mnt/user-data/outputs"  # Works fine in Python
```

---

## 🎯 Complete Windows Workflow

### First Time Setup

```powershell
# 1. Open PowerShell as Administrator
# 2. Allow scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Navigate to project
cd C:\Projects\mystic-app\mystic-api

# 4. Run setup
.\setup.ps1

# 5. Edit .env file (add AWS credentials)
notepad .env

# 6. Verify AWS
.\verify.ps1
```

### Daily Usage

**PowerShell Window 1 (Server):**
```powershell
cd C:\Projects\mystic-app\mystic-api
.\start.ps1
# Leave this running
```

**PowerShell Window 2 (Testing):**
```powershell
cd C:\Projects\mystic-app\mystic-api
.\test.ps1
```

---

## 🆚 Script Comparison: Windows vs Linux/Mac

| Task | Windows | Linux/Mac |
|------|---------|-----------|
| Setup | `.\setup.ps1` | `./setup.sh` |
| Start | `.\start.ps1` | `./start.sh` |
| Test | `.\test.ps1` | `./test.sh` |
| Verify | `.\verify.ps1` | `./verify.sh` |
| Stop | `.\stop.ps1` | `./stop.sh` |
| Python | `python` | `python3` |
| Venv activate | `.\venv\Scripts\Activate.ps1` | `source venv/bin/activate` |
| Venv python | `.\venv\Scripts\python.exe` | `./venv/bin/python3` |

---

## 💡 Windows Pro Tips

### Tip 1: Use Windows Terminal

Windows Terminal (from Microsoft Store) is better than classic PowerShell:
- Supports tabs
- Better colors
- Copy/paste works better

### Tip 2: Pin PowerShell to Taskbar

Right-click PowerShell → Pin to taskbar for quick access

### Tip 3: Use VS Code Terminal

Open project in VS Code → Terminal automatically uses correct directory

```powershell
# Open VS Code from PowerShell
code .
```

### Tip 4: WSL Alternative

If you prefer Linux commands, use WSL (Windows Subsystem for Linux):

```powershell
# Install WSL
wsl --install

# Then use bash scripts
cd /mnt/c/Projects/mystic-app/mystic-api
./setup.sh
```

---

## 🚨 Windows-Specific Troubleshooting

### Docker Desktop Issues

**Problem:** "Docker daemon not responding"

**Fix:**
1. Open Docker Desktop
2. Settings → General → "Use WSL 2 based engine" (enable)
3. Restart Docker Desktop

### Python PATH Issues

**Problem:** Python command not found after installation

**Fix:**
1. Search Windows for "Environment Variables"
2. Edit System Environment Variables
3. Add Python to PATH:
   - `C:\Users\YourName\AppData\Local\Programs\Python\Python311`
   - `C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts`
4. Restart PowerShell

### Antivirus Blocking Docker

Some antivirus software blocks Docker. Add exceptions for:
- Docker Desktop
- Docker daemon
- Your project directory

---

## ✅ Verification Checklist (Windows)

Run these commands to verify setup:

```powershell
# Python installed?
python --version
# Should show: Python 3.11.x

# Docker running?
docker ps
# Should show running containers or empty list

# Virtual environment created?
Test-Path venv
# Should show: True

# .env file configured?
Test-Path .env
# Should show: True

# Database running?
docker ps | Select-String "mystic_postgres"
# Should show the container

# API responding?
curl http://localhost:8000/health
# Should show: {"ok":true}
```

---

## 📞 Getting Help (Windows)

Before asking for help, provide:

```powershell
# Python version
python --version

# Docker version
docker --version

# PowerShell version
$PSVersionTable.PSVersion

# Check if scripts exist
Get-ChildItem *.ps1

# Check if venv exists
Test-Path venv
```

---

## 🎓 Next Steps

Once you have it working on Windows:

1. ✅ Local Windows deployment working
2. ⏭️ Consider WSL for Linux-style development
3. ⏭️ Deploy to cloud (AWS EC2/ECS)
4. ⏭️ Build iOS app

---

## 📝 Windows File List

**PowerShell Scripts (Use These!):**
- `setup.ps1` - Initial setup
- `start.ps1` - Start server
- `test.ps1` - Run tests
- `verify.ps1` - Check AWS
- `stop.ps1` - Stop services

**Bash Scripts (Don't Use on Windows!):**
- `setup.sh` - ❌ Won't work
- `start.sh` - ❌ Won't work
- `test.sh` - ❌ Won't work
- `verify.sh` - ❌ Won't work
- `stop.sh` - ❌ Won't work

**Python Scripts:**
- `main.py` - FastAPI app
- `bedrock_service.py` - Bedrock client
- `astrology_engine.py` - Calculations
- `geocoding_service.py` - Location service
- `test_api.py` - Integration tests
- `verify_bedrock.py` - AWS verification

**Configuration:**
- `.env` - Your AWS credentials
- `.env.example` - Template
- `requirements.txt` - Dependencies
- `docker-compose.yml` - Database

---

## 🎉 You're Ready!

Start with:

```powershell
.\setup.ps1
```

Then follow the prompts. Everything else is automated!
