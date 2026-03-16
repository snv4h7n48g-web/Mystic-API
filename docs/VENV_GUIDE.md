# Virtual Environment (venv) Guide

## 🎯 Quick Answer

**For shell scripts (`.sh`):** You DON'T need to activate venv manually - they handle it
**For Python scripts (`.py`):** Use the wrapper scripts OR activate venv first

---

## ✅ Commands That Handle venv Automatically

These scripts activate the virtual environment for you:

```bash
./setup.sh      # Creates and activates venv
./start.sh      # Activates venv, starts server
./test.sh       # Activates venv, runs tests
./verify.sh     # Activates venv, checks AWS
./stop.sh       # No venv needed (just stops Docker)
```

**You just run them - no activation needed.**

---

## ⚠️ When You DO Need to Activate Manually

### Scenario 1: Running Python Scripts Directly

If you want to run Python scripts directly (not through wrapper scripts):

```bash
# Activate venv first
source venv/bin/activate

# Now run any Python command
python3 verify_bedrock.py
python3 test_api.py
python3 -m pip install some-package

# When done
deactivate
```

### Scenario 2: Interactive Python Development

```bash
# Activate venv
source venv/bin/activate

# Use Python interactively
python3
>>> import bedrock_service
>>> # Test code here

# Or use ipython
pip install ipython
ipython

# When done
deactivate
```

### Scenario 3: Running Uvicorn Manually

```bash
# Activate venv
source venv/bin/activate

# Start server with custom options
uvicorn main:app --reload --port 8001 --host 127.0.0.1

# When done
deactivate
```

### Scenario 4: Installing Additional Packages

```bash
# Activate venv
source venv/bin/activate

# Install packages
pip install some-new-package

# Update requirements
pip freeze > requirements.txt

# When done
deactivate
```

---

## 📋 Complete Command Reference

### Option 1: Using Wrapper Scripts (Recommended)

```bash
# Setup (creates venv)
./setup.sh

# Verify AWS
./verify.sh          # ← Use this instead of python3 verify_bedrock.py

# Start server
./start.sh

# Run tests
./test.sh            # ← Use this instead of python3 test_api.py

# Stop
./stop.sh
```

**Advantage:** You never think about venv activation

---

### Option 2: Manual Activation (More Control)

```bash
# Setup (creates venv)
./setup.sh

# Activate venv (do this once per terminal session)
source venv/bin/activate

# Now your prompt shows (venv)
(venv) $ python3 verify_bedrock.py
(venv) $ uvicorn main:app --reload
(venv) $ python3 test_api.py

# When done with this terminal
(venv) $ deactivate
```

**Advantage:** More control, can run multiple commands

---

### Option 3: Direct venv Path (No Activation)

```bash
# Run without activating
./venv/bin/python3 verify_bedrock.py
./venv/bin/python3 test_api.py
./venv/bin/uvicorn main:app --reload

# Install packages
./venv/bin/pip install some-package
```

**Advantage:** One-off commands, no activation needed

---

## 🔍 How to Tell if venv is Active

```bash
# Check if venv is active
which python3

# If active, you'll see:
/path/to/mystic-api/venv/bin/python3

# If NOT active, you'll see:
/usr/bin/python3  # (or /usr/local/bin/python3)

# Also, your prompt will show (venv) when active:
(venv) user@machine:~/mystic-api$
```

---

## 🎓 Understanding What Activation Does

When you activate venv:

```bash
source venv/bin/activate
```

This modifies your shell environment:
- `PATH` is prepended with `venv/bin`
- `python3` now points to `venv/bin/python3`
- `pip` now installs to `venv/lib/python3.11/site-packages`
- Your prompt shows `(venv)` prefix

When you run wrapper scripts like `./start.sh`:
- They have `source venv/bin/activate` inside them
- The activation only lasts for that script's execution
- Your main shell remains unaffected

---

## 🎯 Recommended Workflow

### Daily Development (Easiest)

```bash
# Terminal 1: Server
./start.sh

# Terminal 2: Testing
./test.sh

# That's it - no venv activation needed
```

### Development with Iteration (More Control)

```bash
# Terminal 1: Activate once, use many times
source venv/bin/activate
uvicorn main:app --reload

# Terminal 2: Activate once, use many times
source venv/bin/activate
python3 test_api.py
python3 verify_bedrock.py
# Edit code, rerun tests, etc.
```

### One-Off Commands (Quick)

```bash
# No activation needed
./venv/bin/python3 verify_bedrock.py
```

---

## 🐛 Common Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Cause:** Running Python without venv activated

**Fix Option 1 (Quick):**
```bash
./venv/bin/python3 your_script.py
```

**Fix Option 2 (For Session):**
```bash
source venv/bin/activate
python3 your_script.py
```

**Fix Option 3 (Use Wrapper):**
```bash
./test.sh  # or ./verify.sh
```

---

### Issue: "Command not found: uvicorn"

**Cause:** venv not activated

**Fix:**
```bash
source venv/bin/activate
uvicorn main:app --reload

# Or just use
./start.sh
```

---

### Issue: "pip installs packages globally"

**Cause:** venv not activated when running pip

**Fix:**
```bash
source venv/bin/activate
pip install package-name

# Or
./venv/bin/pip install package-name
```

---

## 📁 Updated File List

### Shell Scripts (No Manual Activation Needed)
- `setup.sh` ✅ Handles venv automatically
- `start.sh` ✅ Handles venv automatically
- `test.sh` ✅ Handles venv automatically
- `verify.sh` ✅ Handles venv automatically (NEW!)
- `stop.sh` ✅ No venv needed

### Python Scripts (Need Activation OR Use Wrapper)
- `verify_bedrock.py` → Use `./verify.sh` OR activate first
- `test_api.py` → Use `./test.sh` OR activate first
- `main.py` → Use `./start.sh` OR activate first

---

## ✅ Best Practice Summary

**For normal use:** Just use the shell scripts - forget about venv activation

**For development:** Activate venv once per terminal session, then work normally

**For one-off tasks:** Use `./venv/bin/python3` directly

---

## 🎯 Updated Quick Start

```bash
# 1. Run setup
./setup.sh

# 2. Verify AWS
./verify.sh          # ← NEW: wrapper script

# 3. Start server
./start.sh

# 4. Run tests
./test.sh

# Done - you never manually activated venv!
```

---

## 💡 Pro Tips

**Tip 1:** Add this to your `~/.bashrc` or `~/.zshrc` for quick venv activation:
```bash
alias venv='source venv/bin/activate'
```

Then just type `venv` to activate.

**Tip 2:** Most IDEs (VS Code, PyCharm) can auto-detect and use the venv:
- VS Code: Select interpreter → `./venv/bin/python3`
- PyCharm: Settings → Python Interpreter → Add → Existing Environment

**Tip 3:** Check if you're in the right venv:
```bash
python3 -c "import sys; print(sys.executable)"
# Should show: /path/to/mystic-api/venv/bin/python3
```

---

## 🚀 The Bottom Line

**99% of the time:** Use the shell scripts (`./start.sh`, `./test.sh`, etc.)

**Rare cases:** Need to activate manually for development/debugging

**Never needed:** Can always use `./venv/bin/python3` instead of activating
