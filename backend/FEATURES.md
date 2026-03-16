# Mystic API - Features Roadmap

**Last Updated:** 2026-01-31  
**Current Version:** 0.1.0 MVP  
**Status:** ✅ Core backend operational

---

## ✅ **COMPLETED (MVP v0.1)**

### Backend Core
- [x] FastAPI application with REST endpoints
- [x] PostgreSQL database integration
- [x] Session management (CRUD)
- [x] Docker Compose setup
- [x] AWS Bedrock integration (Nova Lite + Pro)
- [x] Cost tracking per session
- [x] Health check endpoint

### Astrology Engine
- [x] Deterministic sun sign calculation
- [x] Moon sign calculation (if birth time provided)
- [x] Rising sign calculation (if birth time provided)
- [x] Element dominance calculation
- [x] Basic aspects generation
- [x] Geocoding service (cached common cities)

### Tarot System
- [x] 78-card deck definition
- [x] 3-card spread (Past/Present/Guidance)
- [x] Random card drawing (cryptographically secure)
- [x] 24-hour draw lock per session

### Reading Generation
- [x] Preview generation (loss-leader hook)
- [x] Full reading generation (7-section schema)
- [x] LLM prompt orchestration
- [x] Schema validation
- [x] Response parsing

### Documentation
- [x] README.md (technical)
- [x] WINDOWS.md (Windows setup)
- [x] QUICKSTART.md (daily reference)
- [x] DEPLOYMENT.md (production guide)
- [x] VENV_GUIDE.md (environment setup)
- [x] Project structure organized

### Scripts
- [x] Windows PowerShell scripts (setup/start/test/verify/stop)
- [x] Unix bash scripts (setup/start/test/verify/stop)
- [x] Integration test suite

---

## 🚧 **IN PROGRESS**

*Nothing currently in progress*

---

## 📅 **PLANNED FEATURES**

### Priority 1: Core Product (Next Sprint)

#### P1.1: Apple In-App Purchase Integration
**Status:** 🔴 Not Started  
**Priority:** Critical  
**Effort:** Medium (3-5 days)  
**Description:**
- [ ] Receipt verification endpoint
- [ ] Apple Server-to-Server notifications
- [ ] Purchase validation before reading generation
- [ ] Product SKU management
- [ ] Sandbox testing support

**Dependencies:** None  
**Blocks:** iOS app payment flow

---

#### P1.2: Rate Limiting & Abuse Prevention
**Status:** 🔴 Not Started  
**Priority:** High  
**Effort:** Medium (2-3 days)  
**Description:**
- [ ] Redis integration
- [ ] Per-IP rate limiting (preview endpoint)
- [ ] Per-session rate limiting
- [ ] CAPTCHA integration (optional)
- [ ] Abuse detection (multiple sessions per device)

**Dependencies:** Redis setup  
**Blocks:** Production launch

---

#### P1.3: Advanced Astrology Engine
**Status:** 🔴 Not Started  
**Priority:** Medium  
**Effort:** High (5-7 days)  
**Description:**
- [ ] Integrate pyswisseph for accurate calculations
- [ ] House system calculations (Placidus/Koch)
- [ ] Detailed aspect calculations (orbs, applying/separating)
- [ ] Planetary dignities (domicile, exaltation, fall, detriment)
- [ ] Transit calculations (optional v2 feature)

**Dependencies:** pyswisseph library  
**Blocks:** Professional-grade accuracy

---

#### P1.4: External Geocoding API
**Status:** 🔴 Not Started  
**Priority:** Medium  
**Effort:** Small (1-2 days)  
**Description:**
- [ ] Google Maps Geocoding API integration
- [ ] OR Mapbox API integration
- [ ] Fallback to cached locations
- [ ] Error handling for unknown locations
- [ ] Cost optimization (cache results)

**Dependencies:** API key from Google/Mapbox  
**Blocks:** Accurate rising sign calculations

---

### Priority 2: Premium Features (Backlog)

#### P2.1: Tiered Pricing System
**Status:** 🔴 Not Started  
**Priority:** High  
**Effort:** Medium (3-4 days)  
**Description:**
- [ ] Product SKU definitions
  - Basic Reading: $1.99 (Astrology + Tarot)
  - Complete Reading: $2.99 (+ Palm)
  - Palm Add-on: $1.00
- [ ] Payment verification per tier
- [ ] Conditional feature access
- [ ] Upsell flow logic
- [ ] Cost tracking per tier

**Dependencies:** P1.1 (IAP integration)  
**Revenue Impact:** +50% ARPU

---

#### P2.2: Palm Reading - Image Upload
**Status:** 🔴 Not Started  
**Priority:** Medium  
**Effort:** Medium (3-4 days)  
**Description:**
- [ ] S3 bucket setup
- [ ] Pre-signed URL generation endpoint
- [ ] Image upload endpoint
- [ ] Image validation (size, format, content)
- [ ] Metadata storage (handedness, dominant hand)
- [ ] Image URL storage in session

**Dependencies:** AWS S3 setup  
**Blocks:** P2.3 (Palm AI Analysis)

---

#### P2.3: Palm Reading - AI Vision Analysis
**Status:** 🔴 Not Started  
**Priority:** Medium  
**Effort:** High (5-7 days)  
**Description:**
- [ ] Claude 3.5 Sonnet Vision integration
- [ ] Palm analysis prompt engineering
- [ ] Feature extraction (life line, heart line, head line, mounts)
- [ ] Structured output parsing
- [ ] Integration with reading generation
- [ ] Cost optimization (~$0.05 per analysis)

**Dependencies:** P2.2 (Image Upload), Claude Vision on Bedrock  
**Revenue Impact:** Premium tier justification

---

#### P2.4: RAG System (Knowledge Grounding)
**Status:** 🔴 Not Started  
**Priority:** Medium  
**Effort:** High (7-10 days)  
**Description:**
- [ ] Vector database setup (pgvector or Pinecone)
- [ ] Curate reference corpus
  - Astrology: Traditional texts, interpretations
  - Tarot: Card meanings, spreads, symbolism
  - Palmistry: Line interpretations, mount meanings
- [ ] Chunk and embed content
- [ ] Semantic retrieval implementation
- [ ] Integration with LLM prompts
- [ ] Query optimization

**Dependencies:** Vector database, curated content  
**Quality Impact:** Reduces hallucinations, increases depth

---

### Priority 3: Scale & Optimization (Future)

#### P3.1: Reading Caching & Optimization
**Status:** 🔴 Not Started  
**Priority:** Low  
**Effort:** Medium (2-3 days)  
**Description:**
- [ ] Cache astrology calculations by birth data hash
- [ ] Cache geocoding results
- [ ] LLM response caching (similar inputs)
- [ ] Database query optimization
- [ ] Redis caching layer

**Dependencies:** Redis  
**Cost Impact:** -20% infrastructure costs at scale

---

#### P3.2: Analytics & Monitoring
**Status:** 🔴 Not Started  
**Priority:** Medium  
**Effort:** Medium (3-4 days)  
**Description:**
- [ ] CloudWatch integration
- [ ] Cost tracking dashboard
- [ ] Conversion funnel metrics
- [ ] Error tracking (Sentry/Rollbar)
- [ ] Performance monitoring (APM)
- [ ] User behavior analytics

**Dependencies:** CloudWatch, analytics tool  
**Business Impact:** Data-driven optimization

---

#### P3.3: Follow-up Questions / Chat Mode
**Status:** 🔴 Not Started  
**Priority:** Low  
**Effort:** High (7-10 days)  
**Description:**
- [ ] Session-based chat interface
- [ ] Context retention from original reading
- [ ] Clarification questions
- [ ] Additional insights ($0.99 per follow-up)
- [ ] Token budget management
- [ ] Conversation history storage

**Dependencies:** None  
**Revenue Impact:** +$0.99 per 20% of users

---

#### P3.4: Relationship Compatibility Reading
**Status:** 🔴 Not Started  
**Priority:** Low  
**Effort:** High (5-7 days)  
**Description:**
- [ ] Two-person input flow
- [ ] Synastry calculations (chart comparison)
- [ ] Compatibility scoring
- [ ] Relationship insights
- [ ] Premium pricing ($4.99)

**Dependencies:** P1.3 (Advanced Astrology)  
**Revenue Impact:** New product line

---

#### P3.5: Monthly Subscription / Transit Updates
**Status:** 🔴 Not Started  
**Priority:** Low  
**Effort:** High (10-14 days)  
**Description:**
- [ ] Subscription product definition
- [ ] Transit calculations
- [ ] Monthly forecast generation
- [ ] Push notification system
- [ ] Subscription management
- [ ] Recurring billing

**Dependencies:** P1.1 (IAP), P1.3 (Advanced Astrology)  
**Revenue Impact:** Recurring revenue stream

---

### Priority 4: Production Infrastructure

#### P4.1: Production Deployment
**Status:** 🔴 Not Started  
**Priority:** High  
**Effort:** Medium (3-5 days)  
**Description:**
- [ ] AWS ECS/EC2 setup
- [ ] RDS PostgreSQL (production database)
- [ ] Load balancer configuration
- [ ] SSL/TLS certificates
- [ ] Domain setup (Route 53)
- [ ] CI/CD pipeline (GitHub Actions)

**Dependencies:** AWS account, domain  
**Blocks:** Public launch

---

#### P4.2: Security Hardening
**Status:** 🔴 Not Started  
**Priority:** High  
**Effort:** Medium (3-4 days)  
**Description:**
- [ ] API authentication (JWT tokens)
- [ ] CORS configuration
- [ ] Input validation & sanitization
- [ ] SQL injection prevention
- [ ] Secrets management (AWS Secrets Manager)
- [ ] DDoS protection (CloudFlare)

**Dependencies:** None  
**Blocks:** Production launch

---

#### P4.3: Backup & Disaster Recovery
**Status:** 🔴 Not Started  
**Priority:** Medium  
**Effort:** Small (1-2 days)  
**Description:**
- [ ] Automated database backups
- [ ] Point-in-time recovery setup
- [ ] S3 image backups
- [ ] Disaster recovery runbook
- [ ] Health check monitoring

**Dependencies:** Production infrastructure  
**Risk Mitigation:** Data loss prevention

---

## 🎨 **iOS App Features** (Separate Roadmap)

*To be defined by iOS development team*

Key integrations needed:
- Session creation API
- Birth data input API
- Preview display
- Payment flow (IAP)
- Reading display (7 sections)
- Palm photo upload
- Sharing/social features

---

## 📊 **Feature Priority Matrix**

### Critical Path to Launch
1. ✅ Core Backend (DONE)
2. 🔴 P1.1: Apple IAP Integration
3. 🔴 P1.2: Rate Limiting
4. 🔴 P4.1: Production Deployment
5. 🔴 P4.2: Security Hardening
6. 🟢 iOS App Development (parallel)

### Revenue Enhancers
1. 🔴 P2.1: Tiered Pricing (+50% ARPU)
2. 🔴 P2.3: Palm AI Vision (premium justification)
3. 🔴 P3.3: Follow-up Questions (+$0.99)
4. 🔴 P3.4: Relationship Compatibility (new product)
5. 🔴 P3.5: Subscription Model (recurring revenue)

### Quality Improvements
1. 🔴 P1.3: Advanced Astrology (professional accuracy)
2. 🔴 P2.4: RAG System (deeper insights)
3. 🔴 P3.1: Caching (cost reduction)
4. 🔴 P3.2: Analytics (optimization data)

---

## 📈 **Effort & Impact Estimates**

| Feature | Effort | Revenue Impact | Cost Impact | Priority |
|---------|--------|----------------|-------------|----------|
| Apple IAP | Medium | Critical | None | P1 |
| Rate Limiting | Medium | None | -$$ abuse | P1 |
| Tiered Pricing | Medium | +50% ARPU | None | P2 |
| Palm AI Vision | High | +30% conversion | +$0.05/read | P2 |
| RAG System | High | +Quality | +$$ setup | P2 |
| Advanced Astrology | High | +Quality | None | P1 |
| Production Deploy | Medium | Enables launch | +$$ infra | P4 |
| Security | Medium | Required | Minimal | P4 |

---

## 🎯 **Next Sprint Planning**

**Recommended next 3 features:**
1. **Apple IAP Integration** (blocks iOS launch)
2. **Rate Limiting** (prevents abuse)
3. **Production Deployment** (enables public launch)

**Estimated timeline:** 2-3 weeks

---

## 📝 **Notes**

- This is a living document - update as priorities change
- Mark items as 🔴 Not Started, 🟡 In Progress, ✅ Complete
- Add actual dates when starting/completing features
- Link to GitHub issues/PRs when available

---

**Status Legend:**
- ✅ Complete
- 🟡 In Progress
- 🔴 Not Started
- 🔵 Blocked
- ⏸️ Paused

**Priority Legend:**
- P1: Critical (launch blocker)
- P2: High (revenue/quality)
- P3: Medium (optimization)
- P4: Low (nice-to-have)

---

**Version History:**
- v0.1 (2026-01-31): MVP completed, roadmap created
