# Palm Reading & Tiered Pricing API Documentation

## 📋 Overview

This document describes the palm reading and tiered pricing endpoints added to Mystic API.

---

## 🎯 **Tiered Pricing Model**

### Products Available

| Product ID | Name | Price | Features | Notes |
|------------|------|-------|----------|-------|
| `reading_basic_199` | Basic Reading | $1.99 | Astrology + Tarot | Entry tier |
| `reading_complete_299` | Complete Reading | $2.99 | Astrology + Tarot + Palm | Premium tier |
| `palm_addon_100` | Palm Add-on | $1.00 | Palm only | Requires Basic tier |

### Product Selection Flow

**Option 1: Choose Upfront**
```
User sees preview
  ↓
Choose tier:
  - Basic ($1.99)
  - Complete ($2.99) ← Upload palm first
  ↓
Pay
  ↓
Get reading (with palm if Complete)
```

**Option 2: Upsell After Basic**
```
User pays for Basic ($1.99)
  ↓
Sees reading
  ↓
Offered: "Add palm for $1 more"
  ↓
Upload palm → Pay $1 → Regenerate with palm
```

---

## 📸 **Palm Reading Flow**

### Complete Flow (for Complete tier)

```
1. Create session
2. Update with birth data
3. Choose "Complete" tier
4. Get pre-signed S3 upload URL
5. Upload palm image to S3 (from iOS)
6. Call analyze endpoint
7. Purchase product
8. Generate reading (includes palm)
```

---

## 🔌 **New API Endpoints**

### 1. Get Upload URL for Palm Image

**Endpoint:** `POST /v1/sessions/{session_id}/palm-upload-url`

**Purpose:** Generate pre-signed URL for direct S3 upload from iOS client

**Request:**
```http
POST /v1/sessions/abc-123/palm-upload-url?content_type=image/jpeg
```

**Response:**
```json
{
  "upload_url": "https://mystic-palm-images.s3.amazonaws.com/...",
  "upload_fields": {
    "key": "palms/abc-123/xyz.jpg",
    "Content-Type": "image/jpeg",
    "...": "..."
  },
  "expires_in": 300
}
```

**iOS Implementation:**
```swift
// 1. Get upload URL from API
let uploadData = await api.getPalmUploadURL(sessionId: sessionId)

// 2. Upload image directly to S3
let formData = MultipartFormData()
for (key, value) in uploadData.uploadFields {
    formData.append(value, withName: key)
}
formData.append(imageData, withName: "file")

// POST to uploadData.uploadURL
```

---

### 2. Analyze Palm Image

**Endpoint:** `POST /v1/sessions/{session_id}/palm-analyze`

**Purpose:** Analyze uploaded palm image using Claude Vision

**Requirements:**
- Palm image must be uploaded first
- User must have purchased Complete tier or Palm add-on

**Request:**
```http
POST /v1/sessions/abc-123/palm-analyze
Content-Type: application/json

{
  "handedness": "right",
  "is_dominant": true
}
```

**Response:**
```json
{
  "status": "analyzed",
  "palm_analysis": {
    "life_line": {
      "length": "long",
      "depth": "deep",
      "quality": "clear",
      "description": "Strong, continuous life line"
    },
    "heart_line": {
      "shape": "curved",
      "position": "high",
      "depth": "medium",
      "description": "Gentle curve toward index finger"
    },
    "head_line": {
      "angle": "sloping",
      "length": "long",
      "quality": "clear",
      "description": "Downward slope indicating creativity"
    },
    "fate_line": {
      "present": true,
      "clarity": "clear",
      "description": "Well-defined fate line"
    },
    "mounts": {
      "venus": "prominent",
      "jupiter": "developed",
      "saturn": "moderate",
      "apollo": "visible",
      "mercury": "medium",
      "luna": "full"
    },
    "hand_shape": {
      "type": "earth",
      "finger_length": "medium",
      "flexibility": "moderate"
    },
    "overall_impression": "Strong life force with creative tendencies and emotional depth"
  },
  "metadata": {
    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "input_tokens": 1523,
    "output_tokens": 287,
    "cost_usd": 0.048
  }
}
```

**Error Responses:**
- `400` - No palm image uploaded
- `403` - Palm feature not purchased
- `500` - Analysis failed

---

### 3. Get Available Products

**Endpoint:** `GET /v1/products`

**Purpose:** List all available products and pricing

**Response:**
```json
{
  "products": [
    {
      "id": "reading_basic_199",
      "name": "Astrology + Tarot Reading",
      "price_usd": 1.99,
      "features": ["astrology", "tarot"],
      "description": "Personalized astrology and tarot synthesis"
    },
    {
      "id": "reading_complete_299",
      "name": "Complete Reading (+ Palm)",
      "price_usd": 2.99,
      "features": ["astrology", "tarot", "palm"],
      "description": "Complete reading including AI palm analysis"
    },
    {
      "id": "palm_addon_100",
      "name": "Palm Reading Add-on",
      "price_usd": 1.00,
      "features": ["palm"],
      "description": "Add palm reading to existing basic reading"
    }
  ]
}
```

---

### 4. Record Purchase

**Endpoint:** `POST /v1/sessions/{session_id}/purchase`

**Purpose:** Record product purchase (will validate Apple IAP receipt in production)

**Request:**
```http
POST /v1/sessions/abc-123/purchase
Content-Type: application/json

{
  "product_id": "reading_complete_299",
  "transaction_id": "2000000123456789",
  "receipt_data": "base64_encoded_receipt"
}
```

**Response:**
```json
{
  "status": "purchased",
  "product_id": "reading_complete_299",
  "transaction_id": "2000000123456789",
  "purchased_products": ["reading_complete_299"]
}
```

**Error Responses:**
- `400` - Invalid product ID
- `400` - Product already owned
- `400` - Missing prerequisite product
- `404` - Session not found

---

### 5. Get Revenue Breakdown

**Endpoint:** `GET /v1/sessions/{session_id}/revenue`

**Purpose:** Get complete revenue and profit analysis for session

**Response:**
```json
{
  "revenue": {
    "gross_total": 2.99,
    "net_total": 2.09,
    "apple_cut": 0.90,
    "breakdown": [
      {
        "product_id": "reading_complete_299",
        "name": "Complete Reading (+ Palm)",
        "gross": 2.99,
        "net": 2.09
      }
    ]
  },
  "costs": {
    "preview": 0.000030,
    "reading": 0.002550,
    "palm": 0.048000,
    "total": 0.050580
  },
  "profit": {
    "gross_profit": 2.04,
    "margin_percent": 97.6
  }
}
```

---

## 📊 **Updated User Flows**

### Flow 1: Basic Tier ($1.99)

```
POST /v1/sessions → {session_id}
PATCH /v1/sessions/{id} → birth data
POST /v1/sessions/{id}/preview → preview data
POST /v1/sessions/{id}/purchase → product: reading_basic_199
POST /v1/sessions/{id}/reading → full reading (no palm)
```

### Flow 2: Complete Tier ($2.99)

```
POST /v1/sessions → {session_id}
PATCH /v1/sessions/{id} → birth data
POST /v1/sessions/{id}/palm-upload-url → S3 upload URL
[iOS uploads image to S3]
POST /v1/sessions/{id}/preview → preview data
POST /v1/sessions/{id}/purchase → product: reading_complete_299
POST /v1/sessions/{id}/palm-analyze → palm features (Claude Vision)
POST /v1/sessions/{id}/reading → full reading (includes palm)
```

### Flow 3: Upsell to Palm ($1.00)

```
[User already purchased Basic tier and has reading]
POST /v1/sessions/{id}/palm-upload-url → S3 upload URL
[iOS uploads image to S3]
POST /v1/sessions/{id}/purchase → product: palm_addon_100
POST /v1/sessions/{id}/palm-analyze → palm features
POST /v1/sessions/{id}/reading → regenerated with palm
```

---

## 💰 **Cost Analysis by Tier**

### Basic Tier ($1.99)

| Component | Cost |
|-----------|------|
| Preview (Nova Lite) | $0.03 |
| Reading (Nova Pro) | $0.10 |
| Infrastructure | $0.04 |
| **Total Cost** | **$0.17** |
| **Net Revenue** | **$1.39** |
| **Gross Profit** | **$1.22 (88%)** |

### Complete Tier ($2.99)

| Component | Cost |
|-----------|------|
| Preview (Nova Lite) | $0.03 |
| Palm Analysis (Claude Vision) | $0.05 |
| Reading (Nova Pro) | $0.10 |
| Infrastructure | $0.04 |
| S3 Storage | $0.01 |
| **Total Cost** | **$0.23** |
| **Net Revenue** | **$2.09** |
| **Gross Profit** | **$1.86 (89%)** |

### Palm Add-on ($1.00)

| Component | Cost |
|-----------|------|
| Palm Analysis (Claude Vision) | $0.05 |
| Reading Regeneration (Nova Pro) | $0.10 |
| Infrastructure | $0.02 |
| S3 Storage | $0.01 |
| **Total Cost** | **$0.18** |
| **Net Revenue** | **$0.70** |
| **Gross Profit** | **$0.52 (74%)** |

---

## 🔒 **Security Considerations**

### Current Implementation (Dev/Testing)

⚠️ **WARNING:** The current `/purchase` endpoint does NOT verify Apple IAP receipts.

```python
# TODO: Add receipt verification
# For now, we trust the client (DEVELOPMENT ONLY)
```

### Production Requirements

Before launch, implement:

1. **Apple Receipt Validation**
```python
# Verify with Apple's servers
response = requests.post(
    "https://buy.itunes.apple.com/verifyReceipt",
    json={"receipt-data": receipt_data}
)
```

2. **Server-to-Server Notifications**
- Handle subscription renewals
- Handle refunds
- Handle subscription cancellations

3. **Transaction ID Verification**
- Check transaction hasn't been used before
- Prevent replay attacks

---

## 📝 **Database Schema Updates**

New fields in `sessions` table:

```sql
palm_image_url TEXT,              -- S3 object key
palm_analysis JSONB,              -- Claude Vision analysis result
purchased_products JSONB,         -- Array of product IDs
palm_cost_usd NUMERIC(10, 6)     -- Palm analysis cost
```

---

## 🧪 **Testing the Palm Reading Flow**

See `test_palm_api.py` for complete integration test including:
- Image upload
- Purchase verification
- Palm analysis
- Reading generation with palm

---

## 🚀 **Next Steps**

1. ✅ **API Complete** (you are here)
2. ⏭️ Create S3 bucket: `mystic-palm-images`
3. ⏭️ Test palm upload + analysis
4. ⏭️ Build iOS client integration
5. ⏭️ Add Apple IAP receipt verification
6. ⏭️ Deploy to production

---

**Version:** 0.2.0  
**Added:** Palm reading + Tiered pricing  
**Date:** 2026-01-31
