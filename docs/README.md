# Mystic API - AWS Bedrock Integration

Complete FastAPI backend with AWS Bedrock (Nova) integration for personalised astrology/tarot readings.

## Overview

This implementation provides:
- **Preview generation** (loss-leader) using Nova Lite (~$0.06 per call)
- **Full reading generation** using Nova Pro (~$0.10 per call)
- **Deterministic astrology** calculations (sun/moon/rising signs)
- **Tarot card** drawing with 24-hour lock
- **Cost tracking** for unit economics analysis
- **Session management** with PostgreSQL

## Architecture

```
User Input (birth data + question)
    ↓
Deterministic Calculations
    ├─ Astrology Engine (sun/moon/rising)
    ├─ Geocoding Service (location → lat/lon)
    └─ Tarot Draw (3-card spread)
    ↓
Preview Generation (Bedrock Nova Lite)
    ├─ Facts only (free to display)
    └─ LLM teaser (2-3 sentences)
    ↓
Payment Gate ($1.99)
    ↓
Full Reading Generation (Bedrock Nova Pro)
    └─ 7-section structured output
```

## Files

- **main.py** - FastAPI application with integrated endpoints
- **bedrock_service.py** - AWS Bedrock client for Nova models
- **astrology_engine.py** - Deterministic natal chart calculations
- **geocoding_service.py** - Location to coordinates conversion
- **.env.example** - Environment configuration template

## Setup

### 1. Prerequisites

```bash
# Python 3.11+
# PostgreSQL 16
# AWS Account with Bedrock access
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

Required environment variables:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_PREVIEW_MODEL=us.amazon.nova-lite-v1:0
BEDROCK_FULL_MODEL=us.amazon.nova-pro-v1:0
```

### 4. Start Database

```bash
docker-compose up -d
```

### 5. Run Application

```bash
uvicorn main:app --reload --port 8000
```

API will be available at: `http://localhost:8000`

## API Endpoints

### Session Management

**Create Session**
```http
POST /v1/sessions
Content-Type: application/json

{
  "client_type": "ios",
  "locale": "en-AU",
  "timezone": "Australia/Melbourne",
  "style": "grounded"
}
```

**Update Session Inputs**
```http
PATCH /v1/sessions/{session_id}
Content-Type: application/json

{
  "birth_date": "1984-08-30",
  "birth_time": "09:06",
  "birth_time_unknown": false,
  "birth_location_text": "Melbourne, Australia",
  "question_intention": "Why do I keep feeling responsible for everyone?"
}
```

### Reading Generation

**Generate Preview** (Loss-leader LLM call)
```http
POST /v1/sessions/{session_id}/preview

Response:
{
  "status": "preview_ready",
  "preview": {
    "astrology_facts": {
      "sun_sign": "Virgo",
      "moon_sign": "Scorpio",
      "rising_sign": "Capricorn",
      "dominant_element": "Earth",
      "dominant_planet": "Saturn",
      "top_aspects": [...]
    },
    "tarot": {
      "spread": "3-card",
      "cards": [
        {"card": "The Hermit", "position": "Past"},
        {"card": "Justice", "position": "Present"},
        {"card": "The Star", "position": "Guidance"}
      ]
    },
    "teaser_text": "Your Virgo Sun and Saturn dominance create...",
    "unlock_price": {"currency": "USD", "amount": 1.99},
    "llm_metadata": {
      "model": "us.amazon.nova-lite-v1:0",
      "input_tokens": 450,
      "output_tokens": 85
    }
  }
}
```

**Generate Full Reading** (Paid, after verification)
```http
POST /v1/sessions/{session_id}/reading

Response:
{
  "status": "complete",
  "reading": {
    "sections": [
      {
        "id": "opening_invocation",
        "text": "When multiple symbolic systems..."
      },
      {
        "id": "astrological_foundation",
        "text": "Your Virgo Sun in the 10th house..."
      },
      ...
    ],
    "full_text": "Complete concatenated reading...",
    "metadata": {
      "model": "us.amazon.nova-pro-v1:0",
      "input_tokens": 1200,
      "output_tokens": 950,
      "dominant_themes": ["responsibility", "transformation"]
    }
  }
}
```

**Get Cost Analytics**
```http
GET /v1/sessions/{session_id}/cost

Response:
{
  "session_id": "...",
  "preview_cost_usd": 0.06,
  "reading_cost_usd": 0.10,
  "total_cost_usd": 0.16
}
```

## Testing

### Test Complete Flow

```bash
# 1. Create session
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "client_type": "ios",
    "locale": "en-AU",
    "timezone": "Australia/Melbourne",
    "style": "grounded"
  }'

# Save session_id from response

# 2. Update with user inputs
curl -X PATCH http://localhost:8000/v1/sessions/{session_id} \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1984-08-30",
    "birth_time": "09:06",
    "birth_location_text": "Melbourne, Australia",
    "question_intention": "Why do I keep feeling responsible for everyone?"
  }'

# 3. Generate preview (calls Bedrock)
curl -X POST http://localhost:8000/v1/sessions/{session_id}/preview

# 4. Generate full reading (calls Bedrock)
curl -X POST http://localhost:8000/v1/sessions/{session_id}/reading

# 5. Check costs
curl http://localhost:8000/v1/sessions/{session_id}/cost
```

## Cost Analysis

### Per Reading Economics

**Preview (All Users)**
- Model: Nova Lite
- Tokens: ~450 input + ~85 output
- Cost: ~$0.06 per preview
- Conversion rate: 15% (target)

**Full Reading (Paid Users)**
- Model: Nova Pro
- Tokens: ~1200 input + ~950 output
- Cost: ~$0.10 per reading

**Unit Economics**
```
Revenue:           $1.99
Apple cut (30%):  -$0.60
Net revenue:       $1.39

Costs:
  Preview (amortised): -$0.40  (100 users × $0.06 / 15 conversions)
  Full reading:        -$0.10
  Infrastructure:      -$0.04
  Total costs:         -$0.54

Gross margin:      $0.85 per paid user (61%)
```

## AWS Bedrock Configuration

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/us.amazon.nova-lite-v1:0",
        "arn:aws:bedrock:*::foundation-model/us.amazon.nova-pro-v1:0"
      ]
    }
  ]
}
```

### Model Access

Ensure Nova models are enabled in your AWS Bedrock console:
1. Navigate to AWS Bedrock Console
2. Select "Model access"
3. Request access to:
   - Amazon Nova Lite
   - Amazon Nova Pro

## Database Schema

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    status TEXT,
    client_type TEXT,
    locale TEXT,
    timezone TEXT,
    style TEXT,
    inputs JSONB,
    tarot JSONB,
    preview JSONB,
    reading JSONB,
    tarot_drawn_at TIMESTAMPTZ,
    tarot_lock_until TIMESTAMPTZ,
    preview_cost_usd NUMERIC(10, 6),
    reading_cost_usd NUMERIC(10, 6),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## Production Considerations

### Current MVP Limitations

1. **Astrology Engine**
   - Simplified calculations (not production-grade ephemeris)
   - Consider integrating `pyswisseph` for accurate planetary positions

2. **Geocoding Service**
   - Limited to cached common locations
   - Integrate Google Maps or Mapbox API for production

3. **RAG System**
   - Not yet implemented
   - Will require vector database (pgvector/Pinecone) + curated corpus

4. **Payment Verification**
   - `/reading` endpoint needs Apple IAP verification
   - Add receipt validation before generating full reading

5. **Rate Limiting**
   - Add Redis-based rate limiting per IP/device
   - Prevent preview spam

### Scaling Recommendations

**Database**
- Add indexes on `session.id`, `session.status`, `session.created_at`
- Consider read replicas for analytics queries

**Caching**
- Cache deterministic astrology calculations per birth data hash
- Cache geocoding results in Redis

**Monitoring**
- Track LLM costs per session in CloudWatch
- Alert on cost anomalies
- Monitor token usage trends

**Security**
- Add API authentication (JWT tokens)
- Implement CORS policies
- Add input validation and sanitization
- Encrypt sensitive session data

## Next Steps

### Priority 1 (MVP Completion)
- [ ] Add Apple IAP receipt verification
- [ ] Implement rate limiting
- [ ] Add proper error logging
- [ ] Create iOS SDK/client

### Priority 2 (Quality)
- [ ] Integrate pyswisseph for accurate astrology
- [ ] Add external geocoding API
- [ ] Implement output validation (check for generic phrases)
- [ ] Add A/B testing framework for prompts

### Priority 3 (Scale)
- [ ] Build RAG system with vector database
- [ ] Curate astrology/tarot reference corpus
- [ ] Add palm reading image analysis
- [ ] Implement follow-up questions upsell

## Support

For issues or questions about the integration:
- Check AWS Bedrock documentation: https://docs.aws.amazon.com/bedrock/
- Verify model access in Bedrock console
- Check CloudWatch logs for API errors

## License

Proprietary - All rights reserved
