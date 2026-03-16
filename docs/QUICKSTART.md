# Mystic API - Quick Reference

## 🚀 Initial Setup (One Time Only)

```bash
# 1. Make scripts executable
chmod +x setup.sh start.sh test.sh stop.sh verify.sh

# 2. Run setup (creates venv, installs deps, starts database)
./setup.sh

# 3. When prompted, add your AWS credentials to .env file:
#    - AWS_ACCESS_KEY_ID
#    - AWS_SECRET_ACCESS_KEY
#    - AWS_REGION (use us-east-1)

# 4. Verify Bedrock access
./verify.sh
```

**Note:** You DON'T need to activate venv manually - the scripts handle it!

## ▶️ Daily Development

```bash
# Start server
./start.sh

# In another terminal - Run tests
./test.sh

# Verify AWS/Bedrock
./verify.sh

# Stop everything
./stop.sh
```

**No venv activation needed** - scripts handle it automatically!

## 🔧 Manual Commands

### When You DON'T Need to Activate venv

```bash
# These scripts handle venv automatically
./start.sh              # Start API
./test.sh               # Run tests
./verify.sh             # Check AWS
./stop.sh               # Stop services

# Start database only
docker-compose up -d

# View database logs
docker-compose logs -f

# Stop database
docker-compose down
```

### When You DO Need to Activate venv

For manual Python commands or development:

```bash
# Activate venv once per terminal session
source venv/bin/activate

# Now you can run Python commands
python3 verify_bedrock.py
python3 test_api.py
uvicorn main:app --reload --port 8001
pip install some-package

# When done
deactivate
```

### Alternative: Direct venv Path (No Activation)

```bash
# Run without activating
./venv/bin/python3 verify_bedrock.py
./venv/bin/uvicorn main:app --reload
```

**See VENV_GUIDE.md for complete details**

## 📍 Important URLs

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Database: localhost:5432

## 🧪 Test Single Endpoint

```bash
# Health check
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"client_type":"ios","locale":"en-AU"}'

# Update session (use session_id from above)
curl -X PATCH http://localhost:8000/v1/sessions/{SESSION_ID} \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1984-08-30",
    "birth_time": "09:06",
    "birth_location_text": "Melbourne, Australia",
    "question_intention": "Why do I feel this way?"
  }'

# Generate preview
curl -X POST http://localhost:8000/v1/sessions/{SESSION_ID}/preview

# Generate full reading
curl -X POST http://localhost:8000/v1/sessions/{SESSION_ID}/reading

# Check costs
curl http://localhost:8000/v1/sessions/{SESSION_ID}/cost
```

## 🐛 Troubleshooting

```bash
# AWS credentials not working?
python3 verify_bedrock.py

# Database not connecting?
docker-compose down && docker-compose up -d

# Port 8000 already in use?
lsof -ti:8000 | xargs kill -9

# Reset everything
./stop.sh
docker-compose down -v
rm -rf venv
./setup.sh
```

## 💰 Cost Monitoring

```bash
# Get session cost
curl http://localhost:8000/v1/sessions/{SESSION_ID}/cost

# Expected costs per reading:
# Preview (Nova Lite):  ~$0.06
# Full (Nova Pro):      ~$0.10
# Total:                ~$0.16
# Gross margin:         ~$0.85 (after $1.39 net revenue)
```

## 📊 Database Queries

```bash
# Connect to database
docker exec -it mystic_postgres psql -U mystic

# View all sessions
SELECT id, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 10;

# Check costs
SELECT 
    status, 
    COUNT(*) as count,
    AVG(preview_cost_usd) as avg_preview_cost,
    AVG(reading_cost_usd) as avg_reading_cost
FROM sessions 
GROUP BY status;

# Exit
\q
```

## ⚙️ Environment Variables (.env)

```env
# Required
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here

# Optional (defaults provided)
BEDROCK_PREVIEW_MODEL=us.amazon.nova-lite-v1:0
BEDROCK_FULL_MODEL=us.amazon.nova-pro-v1:0
DATABASE_URL=postgresql+psycopg2://mystic:mysticpass@localhost:5432/mystic
```

## 📁 Project Structure

```
mystic-api/
├── main.py                 # FastAPI application
├── bedrock_service.py      # AWS Bedrock client
├── astrology_engine.py     # Natal chart calculations
├── geocoding_service.py    # Location service
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # PostgreSQL container
├── .env                    # Configuration (create from .env.example)
│
├── setup.sh                # One-time setup
├── start.sh                # Start server
├── test.sh                 # Run tests
├── stop.sh                 # Stop containers
├── test_api.py             # Integration tests
├── verify_bedrock.py       # AWS verification
│
├── README.md               # Full documentation
└── DEPLOYMENT.md           # Deployment guide
```

## 🎯 Common Tasks

**Add new location to geocoding:**
Edit `geocoding_service.py`, add to `LOCATIONS` dict:
```python
"sydney, australia": (-33.8688, 151.2093),
```

**Change LLM model:**
Edit `.env`:
```env
BEDROCK_PREVIEW_MODEL=us.amazon.nova-micro-v1:0
```

**View API logs:**
```bash
# Server outputs logs to terminal where start.sh is running
# Or redirect: ./start.sh > api.log 2>&1
```

**Check what's using port 8000:**
```bash
lsof -i :8000
```

## 🚨 Emergency Fixes

**"Module not found" errors:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**"Database connection refused:"**
```bash
docker-compose down
docker-compose up -d
sleep 5
```

**"AWS Access Denied:"**
```bash
# Check credentials
cat .env | grep AWS

# Verify in AWS console
python3 verify_bedrock.py
```

**Complete reset:**
```bash
./stop.sh
docker-compose down -v
rm -rf venv __pycache__ .pytest_cache
./setup.sh
```

## 📞 Quick Help

| Issue | Command |
|-------|---------|
| Check if server running | `curl http://localhost:8000/health` |
| Check if database running | `docker ps \| grep postgres` |
| View database logs | `docker-compose logs -f` |
| Restart database | `docker-compose restart` |
| Check AWS config | `python3 verify_bedrock.py` |
| Run full test | `python3 test_api.py` |
| View API docs | Open http://localhost:8000/docs |

## ⏭️ Next Steps After Setup

1. ✅ **Test locally** - `./test.sh`
2. ⏭️ **Deploy to EC2** - See DEPLOYMENT.md
3. ⏭️ **Build iOS app** - Swift client
4. ⏭️ **Add IAP verification** - Apple in-app purchase
5. ⏭️ **Add rate limiting** - Redis integration
6. ⏭️ **Production database** - AWS RDS PostgreSQL
