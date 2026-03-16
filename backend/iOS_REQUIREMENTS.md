# Mystic iOS App - Requirements & Specifications

## 📱 Project Overview

**App Name:** Mystic  
**Platform:** iOS 16+  
**Language:** Swift / SwiftUI  
**Backend:** FastAPI with AWS Bedrock (already built)  
**Monetization:** In-App Purchase (IAP) - tiered pricing

---

## 🎯 MVP Scope

### Core Features Required

**1. User Flows**
- Anonymous reading purchase (no account required)
- Account creation (email/password + Apple Sign In)
- Login/logout
- Reading library (for authenticated users)
- Session linking (save anonymous purchases to account)

**2. Reading Generation Flow**
- Birth data input (date, time, location)
- Question/intention input
- Palm photo upload (for Complete tier)
- Preview display (free teaser)
- Payment (IAP - Basic $1.99 or Complete $2.99)
- Full reading display (7 sections)

**3. Visual Design**
- Dark mode first
- Obsidian/indigo/gold color palette
- Ritual/ceremonial feel (not gamified)
- Tarot card reveal animations
- Premium, minimal UI

---

## 🔌 Backend API (Already Built)

**Base URL:** `http://localhost:8000` (dev) / `https://api.mysticapp.com` (prod)

### Key Endpoints - See PALM_API.md and ACCOUNTS_API.md

**Sessions:** Create, update, preview, reading  
**Palm:** Upload URL, analyze  
**Products:** List, purchase  
**Auth:** Register, login, Apple Sign In  
**Library:** Reading history, user stats  

---

## 💰 Products & Pricing

| Product ID | Name | Price | Features |
|------------|------|-------|----------|
| `reading_basic_199` | Basic Reading | $1.99 | Astrology + Tarot |
| `reading_complete_299` | Complete Reading | $2.99 | + Palm analysis |
| `palm_addon_100` | Palm Add-on | $1.00 | Upgrade Basic |

---

## 📱 Screen Flow

**Anonymous Purchase:**
```
Launch → Intention → Birth Details → Choose Tier → 
(Palm Upload) → Preview → Payment → Reading → 
(Optional: Create Account)
```

**Authenticated:**
```
Login → Home/Library → New Reading → 
(same flow) → Auto-saved to library
```

---

## 🎨 Design Requirements

**Colors:**
- Background: `#0A0A0F` (near-black)
- Primary: `#4A4E8D` (indigo)
- Accent: `#D4AF37` (gold)
- Text: `#F5F5F0` (off-white)

**Fonts:**
- Headers: Cinzel (elegant serif)
- Body: SF Pro / Inter

**Animations:**
- Card reveal: 700ms, staggered
- No casino/game effects
- Ritual/ceremonial feel

---

## 🔐 Authentication

**Apple Sign In:** Primary method (required for iOS)  
**Email/Password:** Alternative  
**Token Storage:** iOS Keychain  
**Token Type:** JWT (30-day expiration)

---

## 📸 Camera Integration

**Palm Capture:**
- Guided overlay (hand outline)
- Natural light instructions
- Allow photo library alternative
- Compress to <2MB before upload
- Upload directly to S3 (pre-signed URL)

---

## 💳 In-App Purchase

**StoreKit 2:**
- 3 consumable products
- Show price in local currency
- Handle purchase failures gracefully
- Send transaction to backend for verification

---

## 🏗️ Recommended Architecture

**SwiftUI + Combine**  
**MVVM pattern**  
**Services:** APIClient, AuthManager, StoreKitManager  
**Keychain for secure storage**  

---

## 🚀 Development Phases

**Phase 1: Foundation (Week 1)**
- Project setup
- Data models
- APIClient
- Basic UI shell

**Phase 2: Core Flow (Week 2)**
- Reading generation screens
- API integration
- Preview/reading display

**Phase 3: Monetization (Week 3)**
- StoreKit integration
- Purchase flow
- Payment handling

**Phase 4: Accounts (Week 4)**
- Login/register
- Apple Sign In
- Reading library

**Phase 5: Polish (Week 5)**
- Animations
- Error handling
- Testing

---

## 📚 What to Upload to Next Chat

1. **This file** (iOS_REQUIREMENTS.md)
2. **PALM_API.md** (Backend API docs)
3. **ACCOUNTS_API.md** (Auth API docs)
4. **FEATURES.md** (Optional - full roadmap)

---

## 🎯 First Question for iOS Chat

"I need to build the iOS app for Mystic. Backend is complete and documented. 
I've never built iOS before. Let's start with project setup and core architecture."

---

**Backend Status:** ✅ Complete and tested  
**Ready for iOS:** ✅ Yes  
**Estimated iOS Timeline:** 4-6 weeks (first-time iOS dev)

Good luck! 🚀📱
