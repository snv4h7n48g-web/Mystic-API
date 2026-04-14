from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
import uuid
import json
import secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import os
import time
from dotenv import load_dotenv

# Import our services
from bedrock_service import get_bedrock_service
from generation import get_generation_orchestrator
from generation.validators import assess_section_safety, validate_product_payload
from astrology_engine import get_astrology_engine
from geocoding_service import get_geocoding_service
from palm_vision_service import get_palm_vision_service
from feng_shui_vision_service import get_feng_shui_vision_service
from s3_service import get_s3_service
from pricing import ProductSKU, get_product, has_feature, validate_purchase, calculate_revenue, PRODUCTS
from auth_service import get_auth_service
from user_service import get_user_service
from purchase_verification import get_purchase_verification_service
from auth_dependencies import get_current_user, get_current_user_optional, require_admin
from models import (
    UserCreate, UserLogin, AppleSignIn,
    USER_TABLE_SCHEMA, USER_SESSIONS_TABLE_SCHEMA, AUTH_TOKENS_TABLE_SCHEMA,
    COMPATIBILITY_TABLE_SCHEMA, BLESSING_OFFERINGS_TABLE_SCHEMA, FENG_SHUI_TABLE_SCHEMA
)
from fastapi.middleware.cors import CORSMiddleware


# Load environment variables
load_dotenv()

# =====================
# APP
# =====================

app = FastAPI(title="Mystic API", version="0.1")
APP_ENV = os.getenv("APP_ENV", "development").strip().lower() or "development"
IS_PRODUCTION = APP_ENV == "production"


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


USE_PERSONA_ORCHESTRATION = _env_flag("MYSTIC_USE_PERSONA_ORCHESTRATION", True)


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured:
        return configured
    if IS_PRODUCTION:
        raise RuntimeError("DATABASE_URL must be set when APP_ENV=production")
    return "postgresql+psycopg2://mystic:mysticpass@localhost:5432/mystic"


def _cors_allowed_origins() -> List[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if raw.strip():
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    if IS_PRODUCTION:
        return []
    return [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
    ]


def _cors_allowed_origin_regex() -> str | None:
    if IS_PRODUCTION:
        return None
    # Allow local frontend dev servers on arbitrary ports, including Vite/Next/etc.
    return r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_origin_regex=_cors_allowed_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# DATABASE
# =====================

DATABASE_URL = _database_url()
engine = create_engine(DATABASE_URL, future=True)


def init_db():
    with engine.begin() as conn:
        # Sessions table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sessions (
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
            palm_image_url TEXT,
            palm_analysis JSONB,
            purchased_products JSONB,
            tarot_drawn_at TIMESTAMPTZ,
            tarot_lock_until TIMESTAMPTZ,
            preview_cost_usd NUMERIC(10, 6),
            reading_cost_usd NUMERIC(10, 6),
            palm_cost_usd NUMERIC(10, 6),
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS preview_persona_id TEXT"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS reading_persona_id TEXT"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS preview_llm_profile_id TEXT"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS reading_llm_profile_id TEXT"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS preview_prompt_version TEXT"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS reading_prompt_version TEXT"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS preview_theme_tags JSONB"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS reading_theme_tags JSONB"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS continuity_source_session_id UUID"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS preview_headline TEXT"))
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS reading_headline TEXT"))

        # Users table
        conn.execute(text(USER_TABLE_SCHEMA))
        # Ensure profile columns exist for legacy databases
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_time TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_time_unknown BOOLEAN"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_location_text TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_location_normalized TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_location_verified BOOLEAN DEFAULT false"))
        
        # User-sessions link table
        conn.execute(text(USER_SESSIONS_TABLE_SCHEMA))
        
        # Auth tokens table
        conn.execute(text(AUTH_TOKENS_TABLE_SCHEMA))

        # Compatibility readings table
        conn.execute(text(COMPATIBILITY_TABLE_SCHEMA))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS preview_persona_id TEXT"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS reading_persona_id TEXT"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS preview_llm_profile_id TEXT"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS reading_llm_profile_id TEXT"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS preview_prompt_version TEXT"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS reading_prompt_version TEXT"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS preview_theme_tags JSONB"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS reading_theme_tags JSONB"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS preview_headline TEXT"))
        conn.execute(text("ALTER TABLE compatibility_readings ADD COLUMN IF NOT EXISTS reading_headline TEXT"))

        # Blessing offerings table
        conn.execute(text(BLESSING_OFFERINGS_TABLE_SCHEMA))

        # Feng Shui analyses table
        conn.execute(text(FENG_SHUI_TABLE_SCHEMA))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS preview_persona_id TEXT"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS analysis_persona_id TEXT"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS preview_llm_profile_id TEXT"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS analysis_llm_profile_id TEXT"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS preview_prompt_version TEXT"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS analysis_prompt_version TEXT"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS preview_theme_tags JSONB"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS analysis_theme_tags JSONB"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS preview_headline TEXT"))
        conn.execute(text("ALTER TABLE feng_shui_analyses ADD COLUMN IF NOT EXISTS analysis_headline TEXT"))

        # Verified purchase ledger for account-wide entitlements and restore flows
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS purchase_transactions (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            product_id TEXT NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            original_transaction_id TEXT,
            platform TEXT,
            provider TEXT,
            environment TEXT,
            resource_type TEXT,
            resource_id TEXT,
            status TEXT DEFAULT 'verified',
            entitlement_active BOOLEAN DEFAULT false,
            receipt_present BOOLEAN DEFAULT false,
            verification_detail TEXT,
            raw JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_purchase_transactions_user ON purchase_transactions(user_id, created_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_purchase_transactions_product ON purchase_transactions(product_id, created_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_purchase_transactions_original ON purchase_transactions(original_transaction_id)"))


if not _env_flag("SKIP_DB_INIT", False):
    init_db()

# =====================
# MODELS
# =====================

class SessionCreate(BaseModel):
    client_type: str = "ios"
    locale: str = "en-AU"
    timezone: str = "Australia/Melbourne"
    style: str = "grounded"


class SessionUpdate(BaseModel):
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_time_unknown: Optional[bool] = None
    birth_location_text: Optional[str] = None
    question_intention: Optional[str] = None
    selected_tier: Optional[str] = None
    flow_type: Optional[str] = None
    bundle_id: Optional[str] = None
    bundle_step: Optional[str] = None
    bundle_steps_completed: Optional[List[str]] = None
    test_mode: Optional[bool] = None


class UserProfileUpdate(BaseModel):
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_time_unknown: Optional[bool] = None
    birth_location_text: Optional[str] = None
    birth_location_normalized: Optional[str] = None
    birth_location_verified: Optional[bool] = None


class LocationValidationRequest(BaseModel):
    location_text: str


class CompatibilityCreate(BaseModel):
    person1: Dict[str, Any]
    person2: Dict[str, Any]


class CompatibilityUpdate(BaseModel):
    person1: Optional[Dict[str, Any]] = None
    person2: Optional[Dict[str, Any]] = None


class BlessingOfferingRequest(BaseModel):
    amount_usd: float
    session_id: Optional[str] = None


class PurchaseRequest(BaseModel):
    product_id: str
    transaction_id: str
    receipt_data: Optional[str] = None
    platform: str = "ios"


class SubscriptionActivateRequest(BaseModel):
    product_id: str
    transaction_id: str
    receipt_data: Optional[str] = None
    platform: str = "ios"


class FengShuiCreate(BaseModel):
    analysis_type: str


class FengShuiUpdate(BaseModel):
    room_purpose: Optional[str] = None
    user_goals: Optional[str] = None
    compass_direction: Optional[str] = None
    image_urls: Optional[List[str]] = None


# =====================
# DB HELPERS
# =====================

def db_insert_session(row: dict):
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO sessions (
                id, status, client_type, locale, timezone, style,
                inputs, tarot, preview, reading,
                palm_image_url, palm_analysis, purchased_products,
                tarot_drawn_at, tarot_lock_until,
                preview_cost_usd, reading_cost_usd, palm_cost_usd
            )
            VALUES (
                :id, :status, :client_type, :locale, :timezone, :style,
                CAST(:inputs AS jsonb),
                CAST(:tarot AS jsonb),
                CAST(:preview AS jsonb),
                CAST(:reading AS jsonb),
                :palm_image_url,
                CAST(:palm_analysis AS jsonb),
                CAST(:purchased_products AS jsonb),
                :tarot_drawn_at,
                :tarot_lock_until,
                :preview_cost_usd,
                :reading_cost_usd,
                :palm_cost_usd
            )
            """),
            row
        )


def db_update_session(session_id: str, **fields):
    sets = []
    params = {"id": session_id}
    jsonb_fields = {
        "inputs",
        "tarot",
        "preview",
        "reading",
        "palm_analysis",
        "purchased_products",
        "preview_theme_tags",
        "reading_theme_tags",
    }

    for k, v in fields.items():
        if k in jsonb_fields:
            sets.append(f"{k} = CAST(:{k} AS jsonb)")
            params[k] = json.dumps(v)
        else:
            sets.append(f"{k} = :{k}")
            params[k] = v

    if not sets:
        return

    sql = f"UPDATE sessions SET {', '.join(sets)} WHERE id = :id"
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def db_update_user_profile(user_id: str, **fields):
    allowed = {
        "birth_date",
        "birth_time",
        "birth_time_unknown",
        "birth_location_text",
        "birth_location_normalized",
        "birth_location_verified",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return

    set_parts = []
    params = {"id": user_id}
    for key, value in updates.items():
        if key == "birth_date":
            set_parts.append("birth_date = CAST(:birth_date AS date)")
        else:
            set_parts.append(f"{key} = :{key}")
        params[key] = value

    sql = f"UPDATE users SET {', '.join(set_parts)} WHERE id = :id"
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def db_get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM sessions WHERE id = :id"),
            {"id": session_id}
        ).mappings().first()

    return dict(row) if row else None


def db_get_session_owner_id(session_id: str) -> Optional[str]:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT user_id FROM user_sessions WHERE session_id = :session_id LIMIT 1"),
            {"session_id": session_id},
        ).mappings().first()
    if not row or not row.get("user_id"):
        return None
    return str(row["user_id"])


def _user_matches_owner(user: Optional[dict], owner_id: Optional[str]) -> bool:
    if not owner_id:
        return True
    if not user:
        return False
    if (user.get("role") or "").lower() == "admin":
        return True
    return str(user.get("id")) == str(owner_id)


def _assert_session_access(session_id: str, user: Optional[dict]) -> Optional[str]:
    owner_id = db_get_session_owner_id(session_id)
    if not _user_matches_owner(user, owner_id):
        raise HTTPException(403, "You do not have access to this session")
    return owner_id


def _assert_record_access(
    record: Optional[Dict[str, Any]],
    user: Optional[dict],
    resource_name: str,
) -> Optional[str]:
    owner_id = str(record.get("user_id")) if record and record.get("user_id") else None
    if not _user_matches_owner(user, owner_id):
        raise HTTPException(403, f"You do not have access to this {resource_name}")
    return owner_id


def db_create_compatibility(user_id: Optional[str]) -> str:
    compat_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO compatibility_readings (
                id, user_id, person1_data, person2_data, preview, reading, purchased
            )
            VALUES (
                :id, :user_id, CAST(:person1_data AS jsonb),
                CAST(:person2_data AS jsonb), CAST(:preview AS jsonb),
                CAST(:reading AS jsonb), :purchased
            )
            """),
            {
                "id": compat_id,
                "user_id": user_id,
                "person1_data": json.dumps({}),
                "person2_data": json.dumps({}),
                "preview": json.dumps(None),
                "reading": json.dumps(None),
                "purchased": False
            }
        )
    return compat_id


def db_get_compatibility(compat_id: str) -> Optional[Dict[str, Any]]:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM compatibility_readings WHERE id = :id"),
            {"id": compat_id}
        ).mappings().first()
    return dict(row) if row else None


def db_update_compatibility(compat_id: str, **fields):
    sets = []
    params = {"id": compat_id}
    jsonb_fields = {
        "person1_data",
        "person2_data",
        "preview",
        "reading",
        "preview_theme_tags",
        "reading_theme_tags",
    }

    for k, v in fields.items():
        if k in jsonb_fields:
            sets.append(f"{k} = CAST(:{k} AS jsonb)")
            params[k] = json.dumps(v)
        else:
            sets.append(f"{k} = :{k}")
            params[k] = v

    if not sets:
        return

    sql = f"UPDATE compatibility_readings SET {', '.join(sets)} WHERE id = :id"
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def db_create_feng_shui(user_id: Optional[str], analysis_type: str) -> str:
    analysis_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO feng_shui_analyses (
                id, user_id, analysis_type, image_urls, preview, analysis, purchased, product_id, cost_usd
            )
            VALUES (
                :id, :user_id, :analysis_type, CAST(:image_urls AS jsonb),
                CAST(:preview AS jsonb), CAST(:analysis AS jsonb),
                :purchased, :product_id, :cost_usd
            )
            """),
            {
                "id": analysis_id,
                "user_id": user_id,
                "analysis_type": analysis_type,
                "image_urls": json.dumps([]),
                "preview": json.dumps(None),
                "analysis": json.dumps(None),
                "purchased": False,
                "product_id": None,
                "cost_usd": 0.0
            }
        )
    return analysis_id


def db_get_feng_shui(analysis_id: str) -> Optional[Dict[str, Any]]:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM feng_shui_analyses WHERE id = :id"),
            {"id": analysis_id}
        ).mappings().first()
    return dict(row) if row else None


def db_update_feng_shui(analysis_id: str, **fields):
    sets = []
    params = {"id": analysis_id}
    jsonb_fields = {
        "image_urls",
        "preview",
        "analysis",
        "preview_theme_tags",
        "analysis_theme_tags",
    }

    for k, v in fields.items():
        if k in jsonb_fields:
            sets.append(f"{k} = CAST(:{k} AS jsonb)")
            params[k] = json.dumps(v)
        else:
            sets.append(f"{k} = :{k}")
            params[k] = v

    if not sets:
        return

    sql = f"UPDATE feng_shui_analyses SET {', '.join(sets)} WHERE id = :id"
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def db_record_purchase_transaction(
    *,
    user_id: Optional[str],
    product_id: str,
    transaction_id: str,
    original_transaction_id: Optional[str],
    platform: str,
    provider: str,
    environment: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    entitlement_active: bool = False,
    verification_detail: Optional[str] = None,
    receipt_present: bool = False,
    raw: Optional[Dict[str, Any]] = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO purchase_transactions (
                id, user_id, product_id, transaction_id, original_transaction_id,
                platform, provider, environment, resource_type, resource_id,
                status, entitlement_active, receipt_present, verification_detail,
                raw, created_at, updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:user_id AS uuid),
                :product_id,
                :transaction_id,
                :original_transaction_id,
                :platform,
                :provider,
                :environment,
                :resource_type,
                :resource_id,
                'verified',
                :entitlement_active,
                :receipt_present,
                :verification_detail,
                CAST(:raw AS jsonb),
                now(),
                now()
            )
            ON CONFLICT (transaction_id) DO UPDATE SET
                user_id = COALESCE(EXCLUDED.user_id, purchase_transactions.user_id),
                product_id = EXCLUDED.product_id,
                original_transaction_id = COALESCE(EXCLUDED.original_transaction_id, purchase_transactions.original_transaction_id),
                platform = EXCLUDED.platform,
                provider = EXCLUDED.provider,
                environment = EXCLUDED.environment,
                resource_type = COALESCE(EXCLUDED.resource_type, purchase_transactions.resource_type),
                resource_id = COALESCE(EXCLUDED.resource_id, purchase_transactions.resource_id),
                status = 'verified',
                entitlement_active = EXCLUDED.entitlement_active,
                receipt_present = EXCLUDED.receipt_present,
                verification_detail = EXCLUDED.verification_detail,
                raw = EXCLUDED.raw,
                updated_at = now()
            """),
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "product_id": product_id,
                "transaction_id": transaction_id,
                "original_transaction_id": original_transaction_id,
                "platform": platform,
                "provider": provider,
                "environment": environment,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "entitlement_active": entitlement_active,
                "receipt_present": receipt_present,
                "verification_detail": verification_detail,
                "raw": json.dumps(raw or {}),
            },
        )


def db_get_user_purchase_transactions(user_id: str) -> List[Dict[str, Any]]:
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
            SELECT *
            FROM purchase_transactions
            WHERE user_id = CAST(:user_id AS uuid)
            ORDER BY created_at DESC, updated_at DESC
            """),
            {"user_id": user_id},
        ).mappings().all()
    return [dict(row) for row in rows]


# =====================
# TAROT
# =====================

TAROT_DECK = [
    "The Fool","The Magician","The High Priestess","The Empress","The Emperor",
    "The Hierophant","The Lovers","The Chariot","Strength","The Hermit",
    "Wheel of Fortune","Justice","The Hanged One","Death","Temperance",
    "The Devil","The Tower","The Star","The Moon","The Sun","Judgement","The World",
    "Ace of Wands","Two of Wands","Three of Wands","Four of Wands","Five of Wands",
    "Six of Wands","Seven of Wands","Eight of Wands","Nine of Wands","Ten of Wands",
    "Page of Wands","Knight of Wands","Queen of Wands","King of Wands",
    "Ace of Cups","Two of Cups","Three of Cups","Four of Cups","Five of Cups",
    "Six of Cups","Seven of Cups","Eight of Cups","Nine of Cups","Ten of Cups",
    "Page of Cups","Knight of Cups","Queen of Cups","King of Cups",
    "Ace of Swords","Two of Swords","Three of Swords","Four of Swords",
    "Five of Swords","Six of Swords","Seven of Swords","Eight of Swords",
    "Nine of Swords","Ten of Swords","Page of Swords","Knight of Swords",
    "Queen of Swords","King of Swords",
    "Ace of Pentacles","Two of Pentacles","Three of Pentacles","Four of Pentacles",
    "Five of Pentacles","Six of Pentacles","Seven of Pentacles","Eight of Pentacles",
    "Nine of Pentacles","Ten of Pentacles","Page of Pentacles","Knight of Pentacles",
    "Queen of Pentacles","King of Pentacles"
]


def draw_tarot(card_count: int = 3):
    if card_count <= 0:
        return []

    random = secrets.SystemRandom()
    positions = ["Past", "Present", "Guidance"]
    if card_count == 1:
        positions = ["Card"]
    elif card_count > len(positions):
        positions = [f"Card {idx + 1}" for idx in range(card_count)]
    else:
        positions = positions[:card_count]

    cards = random.sample(TAROT_DECK, card_count)
    return [
        {
            "card": card,
            "position": positions[idx],
            "orientation": "reversed" if random.choice((False, True)) else "upright",
        }
        for idx, card in enumerate(cards)
    ]


# =====================
# ROUTES
# =====================

@app.get("/health")
def health():
    return {"ok": True}


def _normalize_location_display(location_text: str) -> str:
    parts = [part.strip() for part in location_text.split(",") if part.strip()]
    return ", ".join(part.title() for part in parts)


def _location_format_ok(location_text: str) -> bool:
    parts = [part.strip() for part in location_text.split(",") if part.strip()]
    if len(parts) < 2:
        return False
    for part in parts:
        if len(part) < 2:
            return False
        if not any(ch.isalpha() for ch in part):
            return False
    return True


def _safe_zoneinfo(tz_name: Optional[str]) -> Optional[ZoneInfo]:
    if not tz_name:
        return None
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return None


def _local_date(dt: datetime, tz_name: Optional[str]) -> datetime.date:
    tz = _safe_zoneinfo(tz_name)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if tz is None:
        return dt.astimezone(timezone.utc).date()
    return dt.astimezone(tz).date()


def _is_lunar_new_year_season(today: Optional[datetime] = None) -> bool:
    if today is None:
        today = datetime.now(timezone.utc)
    month = today.month
    day = today.day
    if month == 1 and day >= 20:
        return True
    if month == 2 and day <= 28:
        return True
    return False


def _parse_generated_at(payload: Optional[dict]) -> Optional[datetime]:
    if not isinstance(payload, dict):
        return None
    raw = payload.get("generated_at")
    if not raw and isinstance(payload.get("metadata"), dict):
        raw = payload["metadata"].get("generated_at")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return None


def _extract_preview(session: dict) -> Optional[dict]:
    preview = session.get("preview")
    return preview if isinstance(preview, dict) else None


def _extract_reading(session: dict) -> Optional[dict]:
    reading = session.get("reading")
    return reading if isinstance(reading, dict) else None


def _find_latest_response_today(
    sessions: List[dict],
    tz_name: Optional[str]
) -> Optional[dict]:
    today = _local_date(datetime.now(timezone.utc), tz_name)
    latest = None

    for sess in sessions:
        preview = _extract_preview(sess)
        reading = _extract_reading(sess)

        for kind, payload in (("reading", reading), ("preview", preview)):
            generated_at = _parse_generated_at(payload)
            if not generated_at:
                continue
            if _local_date(generated_at, tz_name) != today:
                continue
            if latest is None or generated_at > latest["generated_at"]:
                latest = {
                    "kind": kind,
                    "payload": payload,
                    "session_id": sess.get("id"),
                    "generated_at": generated_at,
                }

    return latest


def _find_latest_reading(sessions: List[dict]) -> Optional[dict]:
    latest = None
    for sess in sessions:
        reading = _extract_reading(sess)
        if not reading:
            continue
        generated_at = _parse_generated_at(reading)
        if not generated_at:
            # Fallback to session created_at if reading has no timestamp
            created_at = sess.get("created_at")
            if isinstance(created_at, datetime):
                generated_at = created_at
            else:
                continue
        if latest is None or generated_at > latest["generated_at"]:
            latest = {
                "payload": reading,
                "session_id": sess.get("id"),
                "generated_at": generated_at,
            }
    return latest


def _is_test_user(user: Optional[dict]) -> bool:
    if not user:
        return False
    role = (user.get("role") or "").lower()
    email = (user.get("email") or "").lower()
    return role in ("admin", "test") or email.endswith("@mystic.test")


def _llm_limit_disabled(session: dict, user: Optional[dict]) -> bool:
    if os.getenv("MYSTIC_DISABLE_LLM_LIMIT", "").lower() in ("1", "true", "yes"):
        return True
    return _is_test_user(user)


def _subscription_active(subscription: dict) -> bool:
    if not subscription:
        return False
    status = (subscription.get("status") or "").lower()
    if status == "active":
        return True
    if status == "canceled":
        renews_at = subscription.get("renews_at")
        if renews_at:
            try:
                return datetime.fromisoformat(renews_at) > datetime.now(timezone.utc)
            except ValueError:
                return False
    return False


def _get_user_subscription(user: Optional[dict]) -> dict:
    if not user:
        return {}
    metadata = user.get("metadata") or {}
    return metadata.get("subscription") or {}


def _has_active_subscription(user: Optional[dict]) -> bool:
    return _subscription_active(_get_user_subscription(user))


def _verified_products_for_user(user: Optional[dict]) -> List[str]:
    if not user:
        return []
    user_id = str(user.get("id") or "").strip()
    if not user_id:
        return []

    products: List[str] = []
    for row in db_get_user_purchase_transactions(user_id):
        if row.get("status") != "verified":
            continue
        product_id = (row.get("product_id") or "").strip()
        if not product_id:
            continue
        if row.get("entitlement_active") is False and PRODUCTS.get(product_id, {}).get("is_subscription"):
            continue
        products.append(product_id)
    return products


def _user_has_any_product(user: Optional[dict], product_ids: List[str]) -> bool:
    if not user:
        return False
    owned = set(_verified_products_for_user(user))
    return any(product_id in owned for product_id in product_ids)


def _compatibility_included_for_user(user: Optional[dict]) -> bool:
    if _has_active_subscription(user):
        return True
    return _user_has_any_product(user, [
        ProductSKU.COMPATIBILITY,
        ProductSKU.BUNDLE_LIFE_HARMONY,
    ])


def _feng_shui_included_for_user(user: Optional[dict], product_id: Optional[str]) -> bool:
    if _has_active_subscription(user):
        return True
    desired = (product_id or "").strip()
    if not desired:
        return False
    candidates = [desired]
    if desired == ProductSKU.FENG_SHUI_SINGLE:
        candidates.append(ProductSKU.BUNDLE_NEW_BEGINNINGS)
    if desired == ProductSKU.FENG_SHUI_FULL:
        candidates.append(ProductSKU.BUNDLE_LIFE_HARMONY)
    return _user_has_any_product(user, candidates)


def _user_has_feature_access(
    user: Optional[dict],
    purchased_products: Optional[List[str]],
    feature: str,
) -> bool:
    if _has_active_subscription(user):
        return True
    return has_feature(purchased_products or [], feature)


def _reading_includes_palm(reading: dict) -> bool:
    metadata = reading.get("metadata") if isinstance(reading, dict) else None
    if isinstance(metadata, dict):
        return metadata.get("includes_palm") is True
    return False


def _payload_flow_type(kind: str, payload: Optional[dict]) -> str:
    if not isinstance(payload, dict):
        return "combined"
    if kind == "preview":
        return (payload.get("flow_type") or "combined").strip().lower()
    if kind == "reading":
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            return (metadata.get("flow_type") or "combined").strip().lower()
    return "combined"


def _extract_person_data(raw: Optional[dict]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    return raw


def _zodiac_compatibility(a: Dict[str, str], b: Dict[str, str]) -> Dict[str, Any]:
    animal_a = a.get("animal")
    animal_b = b.get("animal")
    element_a = a.get("element")
    element_b = b.get("element")
    harmonious_pairs = {
        ("Rat", "Dragon"), ("Rat", "Monkey"),
        ("Ox", "Snake"), ("Ox", "Rooster"),
        ("Tiger", "Horse"), ("Tiger", "Dog"),
        ("Rabbit", "Goat"), ("Rabbit", "Pig"),
        ("Dragon", "Monkey"), ("Snake", "Rooster"),
        ("Horse", "Dog"), ("Goat", "Pig"),
    }
    pair = (animal_a, animal_b)
    pair_rev = (animal_b, animal_a)
    harmony = "supportive" if pair in harmonious_pairs or pair_rev in harmonious_pairs else "neutral"
    if animal_a == animal_b:
        harmony = "resonant"
    return {
        "person1": a,
        "person2": b,
        "harmony": harmony,
        "element_pair": f"{element_a} / {element_b}"
    }


def _feng_shui_product_for_type(analysis_type: str) -> str:
    mapping = {
        "single_room": ProductSKU.FENG_SHUI_SINGLE,
        "full_home": ProductSKU.FENG_SHUI_FULL,
        "floor_plan": ProductSKU.FENG_SHUI_FLOOR,
    }
    return mapping.get(analysis_type, ProductSKU.FENG_SHUI_SINGLE)


def _max_images_for_type(analysis_type: str) -> int:
    return {
        "single_room": 2,
        "full_home": 5,
        "floor_plan": 1,
    }.get(analysis_type, 2)


def _feng_shui_rate_limit(user: Optional[dict]) -> bool:
    if user and _is_test_user(user):
        return True
    return False


def _image_format_from_key(object_key: str) -> str:
    lower = object_key.lower()
    if lower.endswith(".png"):
        return "png"
    return "jpeg"


def _validate_upload_content_type(content_type: str) -> str:
    normalized = (content_type or "").strip().lower()
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if normalized not in allowed:
        raise HTTPException(400, "Unsupported content_type. Use image/jpeg, image/png, or image/webp")
    return normalized


def _flow_type(inputs: Dict[str, Any]) -> str:
    return (inputs.get("flow_type") or "combined").strip().lower()


def _flow_uses_astrology(flow_type: str) -> bool:
    return flow_type in {
        "combined",
        "sun_moon_solo",
        "daily_horoscope",
        "lunar_new_year_solo",
    }


def _flow_uses_tarot(flow_type: str) -> bool:
    return flow_type in {"combined", "tarot_solo"}


def _current_lunar_year_context() -> Dict[str, Any]:
    current_year = datetime.now(timezone.utc).year
    zodiac = get_astrology_engine().calculate_chinese_zodiac(current_year)
    return {
        "year": current_year,
        "zodiac": zodiac,
        "label": f"{current_year}: Year of the {zodiac['combined']}",
    }


def _expected_tarot_card_count(flow_type: str) -> int:
    return 1 if flow_type == "tarot_solo" else 3


def _tarot_matches_flow(session: Optional[Dict[str, Any]], flow_type: str) -> bool:
    tarot = (session or {}).get("tarot") if isinstance(session, dict) else None
    if not isinstance(tarot, dict):
        return False
    cards = tarot.get("cards") or []
    return len(cards) == _expected_tarot_card_count(flow_type)


def _build_astrology_profile_for_user(user: dict) -> Optional[Dict[str, Any]]:
    birth_date = user.get("birth_date")
    if not birth_date:
        return None

    astro_engine = get_astrology_engine()
    birth_date_value = birth_date.isoformat() if hasattr(birth_date, "isoformat") else str(birth_date)
    birth_time = user.get("birth_time")
    birth_time_unknown = user.get("birth_time_unknown") is True
    birth_location = user.get("birth_location_normalized") or user.get("birth_location_text")

    chart = astro_engine.generate_chart(
        birth_date=birth_date_value,
        birth_time=birth_time,
        birth_time_unknown=birth_time_unknown,
    )
    profile = astro_engine.generate_persistent_profile(chart, birth_location=birth_location)

    return {
        "sun_sign": chart.get("sun_sign"),
        "moon_sign": chart.get("moon_sign"),
        "rising_sign": chart.get("rising_sign"),
        "dominant_element": chart.get("dominant_element"),
        "dominant_modality": chart.get("dominant_modality"),
        "chart": chart,
        "profile": profile,
        "birth_profile_complete": bool(birth_location and chart.get("sun_sign")),
    }


def _flow_is_free(flow_type: str) -> bool:
    return flow_type == "blessing_solo"


def _session_content_contract(session: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    session = session or {}
    inputs = session.get("inputs") or {}
    purchased = session.get("purchased_products") or []
    bundle_product = _bundle_product_for_inputs(inputs)
    flow_type = _flow_type(inputs)
    selected_tier = (inputs.get("selected_tier") or "").lower()
    palm_analysis = session.get("palm_analysis")

    include_palm = False
    if flow_type == "palm_solo":
        include_palm = palm_analysis is not None
    elif flow_type == "combined":
        include_palm = (
            palm_analysis is not None and (
                selected_tier == "complete"
                or ProductSKU.PALM_ADDON in purchased
                or (
                    bundle_product is not None
                    and "palm" in (bundle_product.get("features") or [])
                )
            )
        )

    include_lunar_forecast = (
        flow_type == "lunar_new_year_solo"
        or ProductSKU.LUNAR_FORECAST in purchased
        or (
            bundle_product is not None
            and "lunar_forecast" in (bundle_product.get("features") or [])
        )
    )

    return {
        "flow_type": flow_type,
        "include_palm": include_palm,
        "include_lunar_forecast": include_lunar_forecast,
    }


def _content_contract_signature(contract: Optional[Dict[str, Any]]) -> str:
    contract = contract or {}
    normalized = {
        "flow_type": (contract.get("flow_type") or "combined").strip().lower(),
        "include_palm": contract.get("include_palm") is True,
        "include_lunar_forecast": contract.get("include_lunar_forecast") is True,
    }
    return json.dumps(normalized, sort_keys=True)


def _payload_content_contract(kind: str, payload: Optional[dict]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "flow_type": "combined",
            "include_palm": False,
            "include_lunar_forecast": False,
        }

    raw_contract: Optional[Dict[str, Any]] = None
    if kind == "preview":
        candidate = payload.get("content_contract")
        if isinstance(candidate, dict):
            raw_contract = candidate
    elif kind == "reading":
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            candidate = metadata.get("content_contract")
            if isinstance(candidate, dict):
                raw_contract = candidate
            if raw_contract is None:
                raw_contract = {
                    "flow_type": metadata.get("flow_type"),
                    "include_palm": metadata.get("includes_palm") is True,
                    "include_lunar_forecast": metadata.get("lunar_forecast") is not None,
                }

    raw_contract = raw_contract or {}
    return {
        "flow_type": (raw_contract.get("flow_type") or _payload_flow_type(kind, payload)).strip().lower(),
        "include_palm": raw_contract.get("include_palm") is True,
        "include_lunar_forecast": raw_contract.get("include_lunar_forecast") is True,
    }


def _bundle_product_for_inputs(inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    bundle_id = (inputs.get("bundle_id") or "").strip()
    if not bundle_id:
        return None

    product = PRODUCTS.get(bundle_id)
    if not product:
        return None

    if not product.get("is_bundle"):
        return None

    return product


def _bundle_progress_summary(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    inputs = session.get("inputs") or {}
    bundle_product = _bundle_product_for_inputs(inputs)
    if not bundle_product:
        return None

    steps = [str(step) for step in bundle_product.get("bundle_steps", []) if str(step).strip()]
    completed_raw = inputs.get("bundle_steps_completed") or []
    completed = [str(step) for step in completed_raw if str(step).strip()] if isinstance(completed_raw, list) else []
    current_step = (inputs.get("bundle_step") or "").strip()

    next_step = None
    for step in steps:
        if step not in completed:
            next_step = step
            break

    return {
        "bundle_id": bundle_product.get("id"),
        "bundle_name": bundle_product.get("name"),
        "bundle_steps": steps,
        "bundle_steps_completed": completed,
        "completed_count": len([step for step in steps if step in completed]),
        "total_steps": len(steps),
        "current_step": current_step or next_step,
        "next_step": next_step,
        "complete": next_step is None and bool(steps),
        "session_id": str(session.get("id")),
        "question_intention": (inputs.get("question_intention") or "").strip(),
        "updated_from_status": session.get("status"),
    }


def _required_session_product_id(session: Optional[Dict[str, Any]]) -> Optional[str]:
    if not session:
        return None

    preview = session.get("preview")
    if isinstance(preview, dict):
        preview_product_id = (preview.get("product_id") or "").strip()
        if preview_product_id:
            return preview_product_id

    inputs = session.get("inputs") or {}
    flow_type = _flow_type(inputs)
    if _flow_is_free(flow_type):
        return None

    bundle_product = _bundle_product_for_inputs(inputs)
    if bundle_product and flow_type == "combined":
        return bundle_product["id"]

    if flow_type == "lunar_new_year_solo":
        return ProductSKU.LUNAR_FORECAST

    selected_tier = (inputs.get("selected_tier") or "").lower()
    if selected_tier == "complete":
        return ProductSKU.READING_COMPLETE

    return ProductSKU.READING_BASIC


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _verify_purchase_or_raise(
    *,
    product_id: str,
    transaction_id: str,
    receipt_data: Optional[str],
    is_subscription: bool = False,
    platform: str = "ios",
):
    verifier = get_purchase_verification_service()
    try:
        return verifier.verify_purchase(
            product_id=product_id,
            transaction_id=transaction_id,
            receipt_data=receipt_data,
            platform=platform,
            is_subscription=is_subscription,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(501, str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(501, str(exc)) from exc


def _session_has_paid_reading_access(
    session: Optional[Dict[str, Any]],
    user: Optional[dict],
) -> bool:
    if _has_active_subscription(user):
        return True

    required_product_id = _required_session_product_id(session)
    if not required_product_id:
        return True

    purchased = (session or {}).get("purchased_products") or []
    if required_product_id in purchased:
        return True

    owned_products = _verified_products_for_user(user)
    if required_product_id in owned_products:
        return True

    required_product = PRODUCTS.get(required_product_id)
    if not required_product:
        return False

    required_features = {
        feature
        for feature in required_product.get("features", [])
        if feature not in {"bundle", "subscription", "all_access", "daily"}
    }
    if not required_features:
        return False

    return any(
        has_feature(candidate_products, feature)
        for candidate_products in (purchased, owned_products)
        for feature in required_features
    )


@app.post("/v1/locations/validate")
def validate_location(payload: LocationValidationRequest):
    """
    Validate location text format and attempt to verify via cached geocoding.
    Accepts global input and encourages city + region/country specificity.
    """
    location_text = payload.location_text.strip()
    if len(location_text) < 3:
        return {
            "valid": False,
            "verified": False,
            "normalized": None,
            "reason": "too_short",
            "message": "Enter city and country (and state/region if applicable)."
        }

    format_ok = _location_format_ok(location_text)
    normalized = _normalize_location_display(location_text) if format_ok else None
    geo_service = get_geocoding_service()
    match = geo_service.geocode(location_text)

    if match is not None:
        lat, lon = match
        return {
            "valid": True,
            "verified": True,
            "normalized": normalized or location_text,
            "lat": lat,
            "lon": lon,
            "reason": "verified_cache",
            "message": "Location verified."
        }

    if not format_ok:
        return {
            "valid": False,
            "verified": False,
            "normalized": None,
            "reason": "format_invalid",
            "message": "Please include city and country (and state/region if applicable)."
        }

    return {
        "valid": True,
        "verified": False,
        "normalized": normalized or location_text,
        "reason": "unverified_format",
        "message": "Location looks good. Include state/region if needed."
    }


@app.get("/v1/locations/suggest")
def suggest_locations(q: str, limit: int = 6):
    """Return location suggestions for autocomplete."""
    geocoding_service = get_geocoding_service()
    suggestions = geocoding_service.suggest_locations(q, limit=limit)
    return {"suggestions": suggestions}


@app.post("/v1/sessions")
def create_session(payload: SessionCreate):
    session_id = str(uuid.uuid4())

    row = {
        "id": session_id,
        "status": "draft",
        "client_type": payload.client_type,
        "locale": payload.locale,
        "timezone": payload.timezone,
        "style": payload.style,
        "inputs": json.dumps({}),
        "tarot": json.dumps(None),
        "preview": json.dumps(None),
        "reading": json.dumps(None),
        "palm_image_url": None,
        "palm_analysis": json.dumps(None),
        "purchased_products": json.dumps([]),
        "tarot_drawn_at": None,
        "tarot_lock_until": None,
        "preview_cost_usd": None,
        "reading_cost_usd": None,
        "palm_cost_usd": None,
    }

    db_insert_session(row)
    return {"session_id": session_id}


@app.patch("/v1/sessions/{session_id}")
def update_session(
    session_id: str,
    payload: SessionUpdate,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)

    inputs = session["inputs"] or {}
    inputs.update(payload.dict(exclude_none=True))
    db_update_session(session_id, inputs=inputs)

    return {"ok": True}


@app.get("/v1/sessions/{session_id}")
def get_session(
    session_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    _assert_session_access(session_id, user)
    return session


@app.post("/v1/sessions/{session_id}/tarot")
def generate_tarot(
    session_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)

    now = datetime.now(timezone.utc)

    flow_type = _flow_type(session.get("inputs") or {})
    if (
        session["tarot"]
        and session["tarot_lock_until"]
        and now < session["tarot_lock_until"]
        and _tarot_matches_flow(session, flow_type)
    ):
        return {
            "tarot": session["tarot"],
            "locked_until": session["tarot_lock_until"]
        }

    tarot = {
        "spread": "daily-card" if flow_type == "tarot_solo" else "3-card",
        "cards": draw_tarot(_expected_tarot_card_count(flow_type)),
    }
    lock_until = now + timedelta(hours=24)

    db_update_session(
        session_id,
        tarot=tarot,
        tarot_drawn_at=now,
        tarot_lock_until=lock_until
    )

    return {
        "tarot": tarot,
        "locked_until": lock_until
    }


@app.post("/v1/sessions/{session_id}/preview")
def generate_preview(
    session_id: str,
    daily: bool = False,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Generate preview with real astrology calculation and LLM teaser.
    This is the loss-leader call that converts users.
    """
    request_started_at = time.perf_counter()
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)

    if daily:
        if not user:
            raise HTTPException(401, "Authentication required for daily readings")
        if not _subscription_active(_get_user_subscription(user)):
            raise HTTPException(402, "Active subscription required for daily readings")

    # Validate required inputs
    inputs = session.get("inputs") or {}
    flow_type = _flow_type(inputs)
    if not inputs.get("question_intention"):
        raise HTTPException(400, "Missing required input: question_intention")
    if _flow_uses_astrology(flow_type) and not inputs.get("birth_date"):
        raise HTTPException(400, "Missing required input: birth_date")

    # If preview already exists, return it (no new LLM call).
    if session.get("preview"):
        preview_existing = session["preview"]
        if _has_active_subscription(user):
            if isinstance(preview_existing, dict):
                preview_existing = dict(preview_existing)
                preview_existing["unlock_price"] = {"currency": "USD", "amount": 0.0}
                entitlements = preview_existing.get("entitlements") or {}
                if not isinstance(entitlements, dict):
                    entitlements = {}
                entitlements["subscription_active"] = True
                preview_existing["entitlements"] = entitlements
        if session.get("status") != "preview_ready":
            db_update_session(session_id, status="preview_ready")
        completed_at = time.perf_counter()
        return {
            "status": "preview_ready",
            "preview": preview_existing,
            "timing": _build_route_timing(
                request_started_at=request_started_at,
                completed_at=completed_at,
                first_output_at=completed_at,
            ),
        }

    # Ensure tarot is drawn only for tarot-based flows and redraw if the stored
    # spread no longer matches the active flow (for example, switching from
    # tarot solo back into the full combined reading path).
    if _flow_uses_tarot(flow_type) and not _tarot_matches_flow(session, flow_type):
        generate_tarot(session_id, user)
        session = db_get_session(session_id)

    # Daily consistency (account + anonymous): return same-day result if it exists.
    # Do not reuse same-day previews/readings across non-daily flows.
    if flow_type == "daily_horoscope":
        tz_name = session.get("timezone")
        sessions_to_check = [session]
        current_contract_signature = _content_contract_signature(
            _session_content_contract(session)
        )
        if user:
            user_service = get_user_service()
            linked_sessions = user_service.get_user_sessions(user_id=str(user["id"]), limit=1000)
            sessions_to_check = linked_sessions + [session]

        latest_today = _find_latest_response_today(sessions_to_check, tz_name)
        if latest_today:
            latest_signature = _content_contract_signature(
                _payload_content_contract(
                    latest_today["kind"],
                    latest_today.get("payload"),
                )
            )
            if latest_signature != current_contract_signature:
                latest_today = None
        if latest_today:
            if latest_today["kind"] == "preview":
                db_update_session(
                    session_id,
                    preview=latest_today["payload"],
                    status="preview_ready",
                )
                completed_at = time.perf_counter()
                return {
                    "status": "preview_ready",
                    "preview": latest_today["payload"],
                    "timing": _build_route_timing(
                        request_started_at=request_started_at,
                        completed_at=completed_at,
                        first_output_at=completed_at,
                    ),
                }
            if latest_today["kind"] == "reading":
                for sess in sessions_to_check:
                    if str(sess.get("id")) == str(latest_today["session_id"]):
                        existing_preview = _extract_preview(sess)
                        if existing_preview:
                            db_update_session(
                                session_id,
                                preview=existing_preview,
                                status="preview_ready",
                            )
                            completed_at = time.perf_counter()
                            return {
                                "status": "preview_ready",
                                "preview": existing_preview,
                                "timing": _build_route_timing(
                                    request_started_at=request_started_at,
                                    completed_at=completed_at,
                                    first_output_at=completed_at,
                                ),
                            }

    try:
        generation_started_at = time.perf_counter()
        # Get services
        astro_engine = get_astrology_engine()
        geo_service = get_geocoding_service()
        bedrock = get_bedrock_service()

        # Geocode location
        location_text = inputs.get("birth_location_text", "")
        lat, lon = geo_service.geocode_with_fallback(location_text)

        astrology_facts: Dict[str, Any] = {}
        if _flow_uses_astrology(flow_type):
            astrology_facts = astro_engine.generate_chart(
                birth_date=inputs["birth_date"],
                birth_time=inputs.get("birth_time"),
                birth_time_unknown=inputs.get("birth_time_unknown", False),
                latitude=lat,
                longitude=lon
            )

        tarot_cards: List[Dict[str, str]] = []
        tarot_payload = {"spread": "none", "cards": []}
        if _flow_uses_tarot(flow_type):
            tarot_payload = session["tarot"] or tarot_payload
            tarot_cards = tarot_payload.get("cards") or []

        # Get palm features if analyzed
        palm_features = None
        palm_analysis = session.get("palm_analysis")
        if palm_analysis:
            # Convert palm analysis to simple feature list for preview
            palm_features = [
                {"feature": "life_line", "value": palm_analysis.get("life_line", {}).get("length", "unknown")},
                {"feature": "heart_line", "value": palm_analysis.get("heart_line", {}).get("shape", "unknown")},
                {"feature": "head_line", "value": palm_analysis.get("head_line", {}).get("angle", "unknown")}
            ]

        # Generate preview teaser using Bedrock
        if USE_PERSONA_ORCHESTRATION:
            orchestrator = get_generation_orchestrator()
            subscription_included = _has_active_subscription(user)
            bundle_product = _bundle_product_for_inputs(inputs)
            if subscription_included:
                unlock_amount = 0.0
                product_id = ProductSKU.DAILY_ASTRO_TAROT
            elif flow_type == "blessing_solo":
                unlock_amount = 0.0
                product_id = ""
            elif bundle_product and flow_type == "combined":
                unlock_amount = float(bundle_product.get("price_usd", 0.0))
                product_id = bundle_product["id"]
            elif flow_type == "lunar_new_year_solo":
                unlock_amount = 1.00
                product_id = ProductSKU.LUNAR_FORECAST
            else:
                selected_tier = (inputs.get("selected_tier") or "").lower()
                if selected_tier == "complete":
                    unlock_amount = 2.99
                    product_id = ProductSKU.READING_COMPLETE
                else:
                    unlock_amount = 1.99
                    product_id = ProductSKU.READING_BASIC

            orchestration_result = orchestrator.build_session_preview_result(
                session=session,
                user=user,
                astrology_facts=astrology_facts,
                tarot_payload=tarot_payload,
                unlock_price={"currency": "USD", "amount": unlock_amount},
                product_id=product_id,
                entitlements={"subscription_active": subscription_included},
            )
            llm_result = {
                "teaser_text": orchestration_result.payload["teaser_text"],
                "input_tokens": orchestration_result.input_tokens,
                "output_tokens": orchestration_result.output_tokens,
                "cost_usd": orchestration_result.cost_usd,
                "model": orchestration_result.metadata.model_id,
                "meta": {
                    "persona_id": orchestration_result.metadata.persona_id,
                    "llm_profile_id": orchestration_result.metadata.llm_profile_id,
                    "prompt_version": orchestration_result.metadata.prompt_version,
                    "theme_tags": orchestration_result.metadata.theme_tags,
                    "headline": orchestration_result.metadata.headline,
                },
            }
        else:
            llm_result = bedrock.generate_preview_teaser(
                question=inputs["question_intention"],
                astrology_facts=astrology_facts,
                tarot_cards=tarot_cards,
                palm_facts=palm_features,
                flow_type=flow_type,
            )

        # Determine pricing and product based on tier, bundle, or subscription.
        subscription_included = _has_active_subscription(user)
        bundle_product = _bundle_product_for_inputs(inputs)
        if subscription_included:
            unlock_amount = 0.0
            product_id = ProductSKU.DAILY_ASTRO_TAROT
        elif flow_type == "blessing_solo":
            unlock_amount = 0.0
            product_id = ""
        elif bundle_product and flow_type == "combined":
            unlock_amount = float(bundle_product.get("price_usd", 0.0))
            product_id = bundle_product["id"]
        elif flow_type == "lunar_new_year_solo":
            unlock_amount = 1.00
            product_id = ProductSKU.LUNAR_FORECAST
        else:
            selected_tier = (inputs.get("selected_tier") or "").lower()
            if selected_tier == "complete":
                unlock_amount = 2.99
                product_id = ProductSKU.READING_COMPLETE
            else:
                unlock_amount = 1.99
                product_id = ProductSKU.READING_BASIC

        # Build preview response
        generated_at = datetime.now(timezone.utc).isoformat()
        preview = {
            "flow_type": flow_type,
            "astrology_facts": astrology_facts,
            "tarot": tarot_payload,
            "teaser_text": llm_result["teaser_text"],
            "unlock_price": {"currency": "USD", "amount": unlock_amount},
            "product_id": product_id,
            "content_contract": _session_content_contract(session),
            "generated_at": generated_at,
            "seasonal": {
                "lunar_new_year": _is_lunar_new_year_season()
            },
            "entitlements": {
                "subscription_active": subscription_included,
            },
            "llm_metadata": {
                "model": llm_result["model"],
                "input_tokens": llm_result["input_tokens"],
                "output_tokens": llm_result["output_tokens"]
            }
        }
        if isinstance(llm_result.get("meta"), dict):
            preview["meta"] = llm_result["meta"]

        # Update session
        session_updates = {
            "preview": preview,
            "status": "preview_ready",
            "preview_cost_usd": llm_result["cost_usd"],
        }
        if isinstance(llm_result.get("meta"), dict):
            meta = llm_result["meta"]
            session_updates.update(
                preview_persona_id=meta.get("persona_id"),
                preview_llm_profile_id=meta.get("llm_profile_id"),
                preview_prompt_version=meta.get("prompt_version"),
                preview_theme_tags=meta.get("theme_tags") or [],
                preview_headline=meta.get("headline"),
            )
        db_update_session(session_id, **session_updates)

        completed_at = time.perf_counter()
        return {
            "status": "preview_ready",
            "preview": preview,
            "timing": _build_route_timing(
                request_started_at=request_started_at,
                generation_started_at=generation_started_at,
                first_output_at=completed_at,
                completed_at=completed_at,
            ),
        }

    except Exception as e:
        raise HTTPException(500, f"Preview generation failed: {str(e)}")


def _serialize_sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _build_route_timing(
    *,
    request_started_at: float,
    generation_started_at: Optional[float] = None,
    first_output_at: Optional[float] = None,
    completed_at: Optional[float] = None,
) -> Dict[str, float]:
    completed_at = completed_at or time.perf_counter()
    generation_started_at = generation_started_at or request_started_at
    first_output_at = first_output_at or request_started_at

    return {
        "total_request_time_ms": round(max(0.0, (completed_at - request_started_at) * 1000), 2),
        "queue_time_ms": round(max(0.0, (generation_started_at - request_started_at) * 1000), 2),
        "model_time_ms": round(max(0.0, (completed_at - generation_started_at) * 1000), 2),
        "time_to_first_output_ms": round(max(0.0, (first_output_at - request_started_at) * 1000), 2),
    }


def _reading_product_key(reading: Dict[str, Any]) -> Optional[str]:
    metadata = reading.get("metadata") if isinstance(reading.get("metadata"), dict) else {}
    validation = metadata.get("validation") if isinstance(metadata.get("validation"), dict) else {}
    product_key = (validation.get("product_key") or "").strip()
    if product_key:
        return product_key

    flow_type = (metadata.get("flow_type") or reading.get("flow_type") or "combined").strip().lower()
    return {
        "combined": "full_reading",
        "tarot_solo": "tarot",
        "daily_horoscope": "daily",
        "lunar_new_year_solo": "lunar",
        "compatibility": "compatibility",
        "feng_shui": "feng_shui",
    }.get(flow_type)



def _post_completion_validation_audit(reading: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    metadata = reading.get("metadata") if isinstance(reading.get("metadata"), dict) else {}
    existing = metadata.get("validation") if isinstance(metadata.get("validation"), dict) else None
    if existing is not None:
        return existing

    product_key = _reading_product_key(reading)
    if not product_key:
        return None

    validation = validate_product_payload(product_key, reading)
    return {
        "product_key": validation.product_key,
        "valid": validation.valid,
        "passed": validation.passed,
        "issues": validation.issues,
        "retry_hint": validation.retry_hint,
        "attempts": 1,
    }



def _iter_reading_section_events(
    reading: Dict[str, Any],
    session_id: str,
    *,
    include_started: bool = True,
    timing: Optional[Dict[str, Any]] = None,
):
    sections = reading.get("sections") or []
    metadata = reading.get("metadata") if isinstance(reading.get("metadata"), dict) else {}
    emitted_count = 0
    rejected_sections: list[dict[str, Any]] = []
    if include_started:
        started_payload = {
            "session_id": session_id,
            "section_count": len(sections),
            "flow_type": metadata.get("flow_type"),
            "generated_at": metadata.get("generated_at"),
        }
        if timing is not None:
            started_payload["timing"] = timing
        yield _serialize_sse_event("reading_started", started_payload)
    for index, section in enumerate(sections):
        safety = assess_section_safety(section)
        if not safety.passed:
            rejected_sections.append({
                "id": safety.section_id,
                "issues": safety.issues,
                "index": index,
                "order": index + 1,
            })
            yield _serialize_sse_event(
                "section_rejected",
                {
                    "session_id": session_id,
                    "index": index,
                    "order": index + 1,
                    "total": len(sections),
                    "section_id": safety.section_id,
                    "issues": safety.issues,
                },
            )
            continue
        emitted_count += 1
        yield _serialize_sse_event(
            "section_completed",
            {
                "session_id": session_id,
                "index": index,
                "order": index + 1,
                "total": len(sections),
                "section": section,
            },
        )

    validation_audit = _post_completion_validation_audit(reading)
    if emitted_count == 0:
        failed_payload = {
            "session_id": session_id,
            "status_code": 422,
            "detail": "No safe sections were available to stream",
            "rejected_sections": rejected_sections,
            "validation": validation_audit,
        }
        if timing is not None:
            failed_payload["timing"] = timing
        yield _serialize_sse_event("reading_failed", failed_payload)
        return

    completed_payload = {
        "session_id": session_id,
        "section_count": len(sections),
        "emitted_section_count": emitted_count,
        "rejected_sections": rejected_sections,
        "validation": validation_audit,
        "reading": reading,
    }
    if timing is not None:
        completed_payload["timing"] = timing
    yield _serialize_sse_event("reading_completed", completed_payload)


def _build_session_reading_response(
    session_id: str,
    user: Optional[dict],
    daily: bool = False,
) -> Dict[str, Any]:
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)

    if daily:
        if not user:
            raise HTTPException(401, "Authentication required for daily readings")
        if not _subscription_active(_get_user_subscription(user)):
            raise HTTPException(402, "Active subscription required for daily readings")

    if session.get("reading"):
        if not _session_has_paid_reading_access(session, user):
            raise HTTPException(402, "Reading purchase required")
        return {"status": "complete", "reading": session["reading"]}

    preview = session.get("preview")
    if not preview:
        raise HTTPException(400, "Preview must be generated first")

    inputs = session.get("inputs") or {}
    flow_type = _flow_type(inputs)
    content_contract = _session_content_contract(session)
    current_contract_signature = _content_contract_signature(content_contract)

    tz_name = session.get("timezone")
    sessions_to_check = [session]
    if user:
        user_service = get_user_service()
        linked_sessions = user_service.get_user_sessions(user_id=str(user["id"]), limit=1000)
        sessions_to_check = linked_sessions + [session]

    latest_today = _find_latest_response_today(sessions_to_check, tz_name)
    if latest_today and latest_today["kind"] == "reading":
        latest_signature = _content_contract_signature(
            _payload_content_contract("reading", latest_today.get("payload"))
        )
        if latest_signature == current_contract_signature:
            source_session = next(
                (
                    candidate
                    for candidate in sessions_to_check
                    if candidate.get("id") == latest_today.get("session_id")
                ),
                session,
            )
            if _session_has_paid_reading_access(source_session, user):
                return {"status": "complete", "reading": latest_today["payload"]}

    if not _session_has_paid_reading_access(session, user):
        raise HTTPException(402, "Reading purchase required")

    try:
        bedrock = get_bedrock_service()

        preview = session.get("preview") or {}
        astrology_facts = preview["astrology_facts"]
        tarot_cards = preview["tarot"]["cards"]
        tarot_payload = preview.get("tarot") or {"spread": "none", "cards": tarot_cards}

        inputs = session.get("inputs") or {}
        question = inputs["question_intention"]
        style = session.get("style", "grounded")

        palm_features = None
        palm_analysis = session.get("palm_analysis")
        if palm_analysis:
            palm_features = [
                {"feature": "life_line", "value": f"{palm_analysis.get('life_line', {}).get('length', 'unknown')} - {palm_analysis.get('life_line', {}).get('description', '')}"},
                {"feature": "heart_line", "value": f"{palm_analysis.get('heart_line', {}).get('shape', 'unknown')} - {palm_analysis.get('heart_line', {}).get('description', '')}"},
                {"feature": "head_line", "value": f"{palm_analysis.get('head_line', {}).get('angle', 'unknown')} - {palm_analysis.get('head_line', {}).get('description', '')}"},
                {"feature": "overall", "value": palm_analysis.get('overall_impression', '')},
            ]

        if latest_today and latest_today.get("kind") == "reading" and palm_analysis:
            existing_reading = latest_today["payload"]
            if _reading_includes_palm(existing_reading):
                return {"status": "complete", "reading": existing_reading}

        astro_engine = get_astrology_engine()
        includes_palm = content_contract["include_palm"]
        purchased = session.get("purchased_products") or []
        subscription_included = _has_active_subscription(user)
        deep_access = (
            _user_has_feature_access(user, purchased, "deep")
            or inputs.get("deep_access") is True
        )

        if USE_PERSONA_ORCHESTRATION:
            orchestrator = get_generation_orchestrator()
            orchestration_result = orchestrator.build_session_reading_result(
                session=session,
                user=user,
                astrology_facts=astrology_facts,
                tarot_payload=tarot_payload,
                palm_features=palm_features,
                include_palm=includes_palm,
                deep_access=deep_access,
                content_contract=content_contract,
            )
            llm_result = {
                "sections": orchestration_result.payload["sections"],
                "full_text": orchestration_result.payload["full_text"],
                "model": orchestration_result.metadata.model_id,
                "input_tokens": orchestration_result.input_tokens,
                "output_tokens": orchestration_result.output_tokens,
                "cost_usd": orchestration_result.cost_usd,
                "meta": {
                    "persona_id": orchestration_result.metadata.persona_id,
                    "llm_profile_id": orchestration_result.metadata.llm_profile_id,
                    "prompt_version": orchestration_result.metadata.prompt_version,
                    "theme_tags": orchestration_result.metadata.theme_tags,
                    "headline": orchestration_result.metadata.headline,
                    "continuity_source_session_id": orchestration_result.metadata.continuity_source_session_id,
                },
            }
            reading = orchestration_result.payload
        else:
            llm_result = bedrock.generate_full_reading(
                question=question,
                astrology_facts=astrology_facts,
                tarot_cards=tarot_cards,
                palm_facts=palm_features,
                style=style,
                flow_type=flow_type,
                include_palm=includes_palm,
            )

            generated_at = datetime.now(timezone.utc).isoformat()
            reading = {
                "sections": llm_result["sections"],
                "full_text": llm_result["full_text"],
                "metadata": {
                    "dominant_themes": ["responsibility", "transformation"],
                    "tone": f"{style}-introspective",
                    "confidence": "medium",
                    "personalisation_score": 0.85,
                    "model": llm_result["model"],
                    "input_tokens": llm_result["input_tokens"],
                    "output_tokens": llm_result["output_tokens"],
                    "generated_at": generated_at,
                    "includes_palm": includes_palm,
                    "deep_access": deep_access,
                    "flow_type": flow_type,
                    "content_contract": content_contract,
                },
            }

        lunar_included = (
            flow_type != "lunar_new_year_solo"
            and content_contract["include_lunar_forecast"] is True
        )
        if lunar_included:
            try:
                birth_year = int((inputs.get("birth_date") or "").split("-")[0])
            except Exception:
                birth_year = None

            if birth_year:
                user_zodiac = astro_engine.calculate_chinese_zodiac(birth_year)
                current_year = datetime.now(timezone.utc).year
                year_zodiac = astro_engine.calculate_chinese_zodiac(current_year)
                year_label = f"{current_year}: Year of the {year_zodiac['combined']}"

                lunar_result = bedrock.generate_lunar_forecast(
                    question=question,
                    zodiac=user_zodiac,
                    year_label=year_label,
                )

                reading["sections"].append({
                    "id": "lunar_forecast",
                    "text": lunar_result["text"],
                    "title": f"YOUR YEAR AHEAD ({year_label})",
                })
                reading["full_text"] = (
                    f"{reading['full_text']}\n\n---LUNAR_FORECAST---\n{lunar_result['text']}\n"
                )
                reading["metadata"]["lunar_forecast"] = {
                    "year_label": year_label,
                    "zodiac": user_zodiac,
                    "model": lunar_result["model"],
                    "input_tokens": lunar_result["input_tokens"],
                    "output_tokens": lunar_result["output_tokens"],
                    "cost_usd": lunar_result["cost_usd"],
                }

        reading["metadata"]["subscription_active"] = subscription_included

        reading_updates = {
            "reading": reading,
            "status": "complete",
            "reading_cost_usd": llm_result["cost_usd"],
        }
        if isinstance(llm_result.get("meta"), dict):
            meta = llm_result["meta"]
            reading_updates.update(
                reading_persona_id=meta.get("persona_id"),
                reading_llm_profile_id=meta.get("llm_profile_id"),
                reading_prompt_version=meta.get("prompt_version"),
                reading_theme_tags=meta.get("theme_tags") or [],
                reading_headline=meta.get("headline"),
                continuity_source_session_id=meta.get("continuity_source_session_id"),
            )
        db_update_session(session_id, **reading_updates)

        return {"status": "complete", "reading": reading}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Reading generation failed: {str(e)}")


@app.post("/v1/sessions/{session_id}/reading")
def generate_reading(
    session_id: str,
    daily: bool = False,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Generate full reading with complete LLM synthesis.
    Only callable after payment verification.
    """
    request_started_at = time.perf_counter()
    generation_started_at = time.perf_counter()
    response = _build_session_reading_response(session_id=session_id, user=user, daily=daily)
    completed_at = time.perf_counter()
    response["timing"] = _build_route_timing(
        request_started_at=request_started_at,
        generation_started_at=generation_started_at,
        first_output_at=completed_at,
        completed_at=completed_at,
    )
    return response


@app.get("/v1/sessions/{session_id}/reading/stream")
def stream_reading(
    session_id: str,
    daily: bool = False,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    def event_stream():
        request_started_at = time.perf_counter()
        first_output_at = time.perf_counter()
        generation_started_at = request_started_at
        yield _serialize_sse_event(
            "reading_started",
            {
                "session_id": session_id,
                "streaming": True,
            },
        )
        try:
            generation_started_at = time.perf_counter()
            response = _build_session_reading_response(session_id=session_id, user=user, daily=daily)
            reading = response.get("reading") or {}
            completed_at = time.perf_counter()
            yield from _iter_reading_section_events(
                reading=reading,
                session_id=session_id,
                include_started=False,
                timing=_build_route_timing(
                    request_started_at=request_started_at,
                    generation_started_at=generation_started_at,
                    first_output_at=first_output_at,
                    completed_at=completed_at,
                ),
            )
        except HTTPException as exc:
            yield _serialize_sse_event(
                "reading_failed",
                {
                    "session_id": session_id,
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "timing": _build_route_timing(
                        request_started_at=request_started_at,
                        generation_started_at=generation_started_at,
                        first_output_at=first_output_at,
                    ),
                },
            )
        except Exception as exc:
            yield _serialize_sse_event(
                "reading_failed",
                {
                    "session_id": session_id,
                    "status_code": 500,
                    "detail": str(exc),
                    "timing": _build_route_timing(
                        request_started_at=request_started_at,
                        generation_started_at=generation_started_at,
                        first_output_at=first_output_at,
                    ),
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/v1/sessions/{session_id}/cost")
def get_session_cost(
    session_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """Get cost breakdown for a session (for analytics)."""
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)

    preview_cost = float(session.get("preview_cost_usd") or 0)
    reading_cost = float(session.get("reading_cost_usd") or 0)
    palm_cost = float(session.get("palm_cost_usd") or 0)

    return {
        "session_id": session_id,
        "preview_cost_usd": preview_cost,
        "reading_cost_usd": reading_cost,
        "palm_cost_usd": palm_cost,
        "total_cost_usd": preview_cost + reading_cost + palm_cost
    }


@app.post("/v1/sessions/{session_id}/blessing")
def generate_blessing(session_id: str):
    """Generate a short blessing for a session."""
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    inputs = session.get("inputs") or {}
    question = inputs.get("question_intention") or "A personal reading"
    reading = session.get("reading") or {}
    raw_metadata = reading.get("metadata") if isinstance(reading, dict) else {}
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_themes = metadata.get("dominant_themes")
    if isinstance(raw_themes, list) and raw_themes:
        themes = [str(item) for item in raw_themes if str(item).strip()]
    elif isinstance(raw_themes, str) and raw_themes.strip():
        themes = [raw_themes.strip()]
    else:
        themes = ["clarity", "growth"]

    bedrock = get_bedrock_service()
    result = bedrock.generate_blessing(question=question, themes=themes)

    return {
        "blessing_text": result["blessing_text"],
        "metadata": {
            "model": result["model"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "cost_usd": result["cost_usd"]
        }
    }


@app.post("/v1/blessings/offering")
def record_blessing_offering(
    payload: BlessingOfferingRequest,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """Record a blessing offering (optional donation)."""
    offering_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO blessing_offerings (
                id, user_id, session_id, amount_usd
            )
            VALUES (
                :id, :user_id, :session_id, :amount_usd
            )
            """),
            {
                "id": offering_id,
                "user_id": str(user["id"]) if user else None,
                "session_id": payload.session_id,
                "amount_usd": payload.amount_usd
            }
        )

    return {
        "status": "recorded",
        "offering_id": offering_id
    }


# =====================
# COMPATIBILITY READING ENDPOINTS
# =====================

@app.post("/v1/compatibility")
def create_compatibility(payload: CompatibilityCreate, user: Optional[dict] = Depends(get_current_user_optional)):
    compat_id = db_create_compatibility(str(user["id"]) if user else None)
    db_update_compatibility(
        compat_id,
        person1_data=payload.person1,
        person2_data=payload.person2
    )
    return {"compatibility_id": compat_id}


@app.patch("/v1/compatibility/{compat_id}")
def update_compatibility(
    compat_id: str,
    payload: CompatibilityUpdate,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    compat = db_get_compatibility(compat_id)
    if not compat:
        raise HTTPException(404, "Compatibility session not found")

    _assert_record_access(compat, user, "compatibility reading")

    updates = {}
    if payload.person1 is not None:
        updates["person1_data"] = payload.person1
    if payload.person2 is not None:
        updates["person2_data"] = payload.person2
    db_update_compatibility(compat_id, **updates)
    return {"status": "updated"}


@app.post("/v1/compatibility/{compat_id}/preview")
def generate_compatibility_preview(
    compat_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    compat = db_get_compatibility(compat_id)
    if not compat:
        raise HTTPException(404, "Compatibility session not found")

    _assert_record_access(compat, user, "compatibility reading")

    existing_preview = compat.get("preview")
    if existing_preview:
        if _has_active_subscription(user) and isinstance(existing_preview, dict):
            existing_preview = dict(existing_preview)
            existing_preview["unlock_price"] = {"currency": "USD", "amount": 0.0}
            entitlements = existing_preview.get("entitlements") or {}
            if not isinstance(entitlements, dict):
                entitlements = {}
            entitlements["subscription_active"] = True
            existing_preview["entitlements"] = entitlements
        return {"status": "preview_ready", "preview": existing_preview}

    person1 = _extract_person_data(compat.get("person1_data"))
    person2 = _extract_person_data(compat.get("person2_data"))

    astro_engine = get_astrology_engine()
    geo_service = get_geocoding_service()
    bedrock = get_bedrock_service()

    def build_chart(person: Dict[str, Any]) -> Dict[str, Any]:
        location_text = person.get("birth_location_text") or ""
        lat, lon = geo_service.geocode_with_fallback(location_text)
        return astro_engine.generate_chart(
            birth_date=person["birth_date"],
            birth_time=person.get("birth_time"),
            birth_time_unknown=person.get("birth_time_unknown", False),
            latitude=lat,
            longitude=lon
        )

    chart1 = build_chart(person1)
    chart2 = build_chart(person2)
    synastry = astro_engine.calculate_synastry(chart1, chart2)

    birth_year_1 = int(person1["birth_date"].split("-")[0])
    birth_year_2 = int(person2["birth_date"].split("-")[0])
    zodiac1 = astro_engine.calculate_chinese_zodiac(birth_year_1)
    zodiac2 = astro_engine.calculate_chinese_zodiac(birth_year_2)
    zodiac_harmony = _zodiac_compatibility(zodiac1, zodiac2)

    included = _compatibility_included_for_user(user)
    entitlements = {
        "subscription_active": _has_active_subscription(user),
        "bundle_active": _user_has_any_product(user, [ProductSKU.BUNDLE_LIFE_HARMONY]),
        "included": included,
    }

    preview = None
    if USE_PERSONA_ORCHESTRATION:
        try:
            orchestrator = get_generation_orchestrator()
            orchestration_result = orchestrator.build_compatibility_preview_result(
                compat=compat,
                user=user,
                person1=person1,
                person2=person2,
                chart1=chart1,
                chart2=chart2,
                zodiac1=zodiac1,
                zodiac2=zodiac2,
                synastry=synastry,
                zodiac_harmony=zodiac_harmony,
                entitlements=entitlements,
            )
            preview = orchestration_result.payload
            preview["product_id"] = ProductSKU.COMPATIBILITY
            preview["generated_at"] = datetime.now(timezone.utc).isoformat()
            preview["llm_metadata"] = {
                "model": orchestration_result.metadata.model_id,
                "input_tokens": orchestration_result.input_tokens,
                "output_tokens": orchestration_result.output_tokens,
            }
            db_update_compatibility(
                compat_id,
                preview=preview,
                preview_persona_id=orchestration_result.metadata.persona_id,
                preview_llm_profile_id=orchestration_result.metadata.llm_profile_id,
                preview_prompt_version=orchestration_result.metadata.prompt_version,
                preview_theme_tags=orchestration_result.metadata.theme_tags,
                preview_headline=orchestration_result.metadata.headline,
            )
        except Exception as exc:
            print(f"Compatibility preview orchestration failed for {compat_id}: {exc}")

    if preview is None:
        llm_result = bedrock.generate_compatibility_preview(
            person1={"profile": person1, "chart": chart1},
            person2={"profile": person2, "chart": chart2},
            synastry=synastry,
            zodiac_compatibility=zodiac_harmony
        )

        preview = {
            "teaser_text": llm_result["teaser_text"],
            "person1": {"profile": person1, "chart": chart1, "zodiac": zodiac1},
            "person2": {"profile": person2, "chart": chart2, "zodiac": zodiac2},
            "synastry": synastry,
            "unlock_price": {"currency": "USD", "amount": 0.0 if included else 3.99},
            "product_id": ProductSKU.COMPATIBILITY,
            "entitlements": entitlements,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "llm_metadata": {
                "model": llm_result["model"],
                "input_tokens": llm_result["input_tokens"],
                "output_tokens": llm_result["output_tokens"]
            }
        }

        db_update_compatibility(compat_id, preview=preview)
    return {"status": "preview_ready", "preview": preview}


@app.post("/v1/compatibility/{compat_id}/purchase")
def record_compatibility_purchase(
    compat_id: str,
    payload: PurchaseRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    compat = db_get_compatibility(compat_id)
    if not compat:
        raise HTTPException(404, "Compatibility session not found")

    _assert_record_access(compat, user, "compatibility reading")

    if payload.product_id != ProductSKU.COMPATIBILITY:
        raise HTTPException(400, "Invalid compatibility product")

    if _compatibility_included_for_user(user):
        return {
            "status": "included_by_entitlement",
            "product_id": ProductSKU.COMPATIBILITY,
            "transaction_id": payload.transaction_id,
            "subscription_active": _has_active_subscription(user),
            "bundle_active": _user_has_any_product(user, [ProductSKU.BUNDLE_LIFE_HARMONY]),
        }

    verification = _verify_purchase_or_raise(
        product_id=payload.product_id,
        transaction_id=payload.transaction_id,
        receipt_data=payload.receipt_data,
        platform=payload.platform,
    )

    db_update_compatibility(compat_id, purchased=True)
    db_record_purchase_transaction(
        user_id=str(user["id"]) if user else None,
        product_id=payload.product_id,
        transaction_id=verification.transaction_id,
        original_transaction_id=verification.original_transaction_id,
        platform=payload.platform,
        provider=verification.provider,
        environment=verification.environment,
        resource_type="compatibility",
        resource_id=compat_id,
        entitlement_active=verification.entitlement_active,
        verification_detail=verification.detail,
        receipt_present=bool((payload.receipt_data or "").strip()),
        raw=verification.raw,
    )
    return {
        "status": "purchased",
        "product_id": ProductSKU.COMPATIBILITY,
        "transaction_id": payload.transaction_id,
        "verification": {
            "provider": verification.provider,
            "environment": verification.environment,
            "entitlement_active": verification.entitlement_active,
            "original_transaction_id": verification.original_transaction_id,
        },
    }


@app.post("/v1/compatibility/{compat_id}/reading")
def generate_compatibility_reading(
    compat_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    compat = db_get_compatibility(compat_id)
    if not compat:
        raise HTTPException(404, "Compatibility session not found")

    _assert_record_access(compat, user, "compatibility reading")

    if not compat.get("purchased") and not _compatibility_included_for_user(user):
        raise HTTPException(402, "Compatibility purchase required")

    if compat.get("reading"):
        return {"status": "complete", "reading": compat["reading"]}

    person1 = _extract_person_data(compat.get("person1_data"))
    person2 = _extract_person_data(compat.get("person2_data"))

    astro_engine = get_astrology_engine()
    geo_service = get_geocoding_service()
    bedrock = get_bedrock_service()

    def build_chart(person: Dict[str, Any]) -> Dict[str, Any]:
        location_text = person.get("birth_location_text") or ""
        lat, lon = geo_service.geocode_with_fallback(location_text)
        return astro_engine.generate_chart(
            birth_date=person["birth_date"],
            birth_time=person.get("birth_time"),
            birth_time_unknown=person.get("birth_time_unknown", False),
            latitude=lat,
            longitude=lon
        )

    chart1 = build_chart(person1)
    chart2 = build_chart(person2)
    synastry = astro_engine.calculate_synastry(chart1, chart2)

    birth_year_1 = int(person1["birth_date"].split("-")[0])
    birth_year_2 = int(person2["birth_date"].split("-")[0])
    zodiac1 = astro_engine.calculate_chinese_zodiac(birth_year_1)
    zodiac2 = astro_engine.calculate_chinese_zodiac(birth_year_2)
    zodiac_harmony = _zodiac_compatibility(zodiac1, zodiac2)

    reading = None
    if USE_PERSONA_ORCHESTRATION:
        try:
            orchestrator = get_generation_orchestrator()
            orchestration_result = orchestrator.build_compatibility_reading_result(
                compat=compat,
                user=user,
                person1=person1,
                person2=person2,
                chart1=chart1,
                chart2=chart2,
                synastry=synastry,
                zodiac_harmony=zodiac_harmony,
            )
            reading = orchestration_result.payload
            reading["metadata"].update(
                {
                    "model": orchestration_result.metadata.model_id,
                    "input_tokens": orchestration_result.input_tokens,
                    "output_tokens": orchestration_result.output_tokens,
                }
            )
            db_update_compatibility(
                compat_id,
                reading=reading,
                reading_persona_id=orchestration_result.metadata.persona_id,
                reading_llm_profile_id=orchestration_result.metadata.llm_profile_id,
                reading_prompt_version=orchestration_result.metadata.prompt_version,
                reading_theme_tags=orchestration_result.metadata.theme_tags,
                reading_headline=orchestration_result.metadata.headline,
            )
        except Exception as exc:
            print(f"Compatibility reading orchestration failed for {compat_id}: {exc}")

    if reading is None:
        llm_result = bedrock.generate_compatibility_reading(
            person1={"profile": person1, "chart": chart1},
            person2={"profile": person2, "chart": chart2},
            synastry=synastry,
            zodiac_compatibility=zodiac_harmony
        )

        reading = {
            "sections": llm_result["sections"],
            "full_text": llm_result["full_text"],
            "metadata": {
                "model": llm_result["model"],
                "input_tokens": llm_result["input_tokens"],
                "output_tokens": llm_result["output_tokens"],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }

        db_update_compatibility(compat_id, reading=reading)
    return {"status": "complete", "reading": reading}


# =====================
# FENG SHUI ENDPOINTS
# =====================

@app.post("/v1/feng-shui")
def create_feng_shui(payload: FengShuiCreate, user: Optional[dict] = Depends(get_current_user_optional)):
    analysis_id = db_create_feng_shui(str(user["id"]) if user else None, payload.analysis_type)
    return {"analysis_id": analysis_id}


@app.patch("/v1/feng-shui/{analysis_id}")
def update_feng_shui(
    analysis_id: str,
    payload: FengShuiUpdate,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    analysis = db_get_feng_shui(analysis_id)
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    _assert_record_access(analysis, user, "feng shui analysis")

    updates = {}
    if payload.room_purpose is not None:
        updates["room_purpose"] = payload.room_purpose
    if payload.user_goals is not None:
        updates["user_goals"] = payload.user_goals
    if payload.compass_direction is not None:
        updates["compass_direction"] = payload.compass_direction
    if payload.image_urls is not None:
        updates["image_urls"] = payload.image_urls
    db_update_feng_shui(analysis_id, **updates)
    return {"status": "updated"}


@app.post("/v1/feng-shui/{analysis_id}/upload-urls")
def get_feng_shui_upload_urls(
    analysis_id: str,
    count: int = 1,
    content_type: str = "image/jpeg",
    user: Optional[dict] = Depends(get_current_user_optional),
):
    analysis = db_get_feng_shui(analysis_id)
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    _assert_record_access(analysis, user, "feng shui analysis")

    analysis_type = analysis.get("analysis_type") or "single_room"
    max_images = _max_images_for_type(analysis_type)
    if count < 1 or count > max_images:
        raise HTTPException(400, f"Image count must be between 1 and {max_images}")

    safe_content_type = _validate_upload_content_type(content_type)

    s3 = get_s3_service()
    uploads = []
    for _ in range(count):
        presigned = s3.generate_presigned_upload_url(
            session_id=analysis_id,
            content_type=safe_content_type,
            prefix="fengshui"
        )
        uploads.append(presigned)

    return {"uploads": uploads}


@app.post("/v1/feng-shui/{analysis_id}/preview")
def generate_feng_shui_preview(
    analysis_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    analysis = db_get_feng_shui(analysis_id)
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    _assert_record_access(analysis, user, "feng shui analysis")

    preview = analysis.get("preview")
    if preview:
        included = _feng_shui_included_for_user(user, preview.get("product_id") if isinstance(preview, dict) else None)
        if included and isinstance(preview, dict):
            preview = dict(preview)
            preview["unlock_price"] = {"currency": "USD", "amount": 0.0}
            entitlements = preview.get("entitlements") or {}
            if not isinstance(entitlements, dict):
                entitlements = {}
            entitlements["subscription_active"] = _has_active_subscription(user)
            entitlements["bundle_active"] = _user_has_any_product(user, [
                ProductSKU.BUNDLE_NEW_BEGINNINGS,
                ProductSKU.BUNDLE_LIFE_HARMONY,
            ])
            entitlements["included"] = True
            preview["entitlements"] = entitlements
        return {"status": "preview_ready", "preview": preview}

    analysis_type = analysis.get("analysis_type") or "single_room"
    product_id = _feng_shui_product_for_type(analysis_type)
    price_map = {
        ProductSKU.FENG_SHUI_SINGLE: 4.99,
        ProductSKU.FENG_SHUI_FULL: 9.99,
        ProductSKU.FENG_SHUI_FLOOR: 2.99,
    }

    included = _feng_shui_included_for_user(user, product_id)
    entitlements = {
        "subscription_active": _has_active_subscription(user),
        "bundle_active": _user_has_any_product(user, [
            ProductSKU.BUNDLE_NEW_BEGINNINGS,
            ProductSKU.BUNDLE_LIFE_HARMONY,
        ]),
        "included": included,
    }

    if USE_PERSONA_ORCHESTRATION:
        orchestrator = get_generation_orchestrator()
        orchestration_result = orchestrator.build_feng_shui_preview_result(
            analysis=analysis,
            user=user,
            entitlements=entitlements,
            product_id=product_id,
            price_amount=price_map[product_id],
        )
        preview_payload = orchestration_result.payload
        preview_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        db_update_feng_shui(
            analysis_id,
            preview=preview_payload,
            product_id=product_id,
            preview_persona_id=orchestration_result.metadata.persona_id,
            preview_llm_profile_id=orchestration_result.metadata.llm_profile_id,
            preview_prompt_version=orchestration_result.metadata.prompt_version,
            preview_theme_tags=orchestration_result.metadata.theme_tags,
            preview_headline=orchestration_result.metadata.headline,
        )
    else:
        preview_payload = {
            "teaser_text": "Your space suggests a few high-impact shifts. Unlock the full analysis for detailed recommendations.",
            "analysis_type": analysis_type,
            "unlock_price": {
                "currency": "USD",
                "amount": 0.0 if included else price_map[product_id],
            },
            "product_id": product_id,
            "entitlements": entitlements,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        db_update_feng_shui(analysis_id, preview=preview_payload, product_id=product_id)
    return {"status": "preview_ready", "preview": preview_payload}


@app.post("/v1/feng-shui/{analysis_id}/purchase")
def record_feng_shui_purchase(
    analysis_id: str,
    payload: PurchaseRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    analysis = db_get_feng_shui(analysis_id)
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    _assert_record_access(analysis, user, "feng shui analysis")

    expected_product_id = analysis.get("product_id") or _feng_shui_product_for_type(
        analysis.get("analysis_type") or "single_room"
    )
    if payload.product_id != expected_product_id:
        raise HTTPException(400, "Invalid product for this Feng Shui analysis")

    if _feng_shui_included_for_user(user, payload.product_id):
        return {
            "status": "included_by_entitlement",
            "product_id": payload.product_id,
            "transaction_id": payload.transaction_id,
            "subscription_active": _has_active_subscription(user),
            "bundle_active": _user_has_any_product(user, [
                ProductSKU.BUNDLE_NEW_BEGINNINGS,
                ProductSKU.BUNDLE_LIFE_HARMONY,
            ]),
        }

    verification = _verify_purchase_or_raise(
        product_id=payload.product_id,
        transaction_id=payload.transaction_id,
        receipt_data=payload.receipt_data,
        platform=payload.platform,
    )

    db_update_feng_shui(analysis_id, purchased=True, product_id=payload.product_id)
    db_record_purchase_transaction(
        user_id=str(user["id"]) if user else None,
        product_id=payload.product_id,
        transaction_id=verification.transaction_id,
        original_transaction_id=verification.original_transaction_id,
        platform=payload.platform,
        provider=verification.provider,
        environment=verification.environment,
        resource_type="feng_shui",
        resource_id=analysis_id,
        entitlement_active=verification.entitlement_active,
        verification_detail=verification.detail,
        receipt_present=bool((payload.receipt_data or "").strip()),
        raw=verification.raw,
    )
    return {
        "status": "purchased",
        "product_id": payload.product_id,
        "transaction_id": payload.transaction_id,
        "verification": {
            "provider": verification.provider,
            "environment": verification.environment,
            "entitlement_active": verification.entitlement_active,
            "original_transaction_id": verification.original_transaction_id,
        },
    }


@app.post("/v1/feng-shui/{analysis_id}/analysis")
def generate_feng_shui_analysis(
    analysis_id: str,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    analysis = db_get_feng_shui(analysis_id)
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    _assert_record_access(analysis, user, "feng shui analysis")

    if not analysis.get("purchased") and not _feng_shui_included_for_user(user, analysis.get("product_id")):
        raise HTTPException(402, "Purchase required")

    if analysis.get("analysis"):
        return {"status": "complete", "analysis": analysis["analysis"]}

    if not _feng_shui_rate_limit(user):
        if user:
            user_service = get_user_service()
            sessions_today = user_service.get_user_sessions(user_id=str(user["id"]), limit=200)
            if len(sessions_today) > 5:
                raise HTTPException(429, "Rate limit exceeded")

    image_keys = analysis.get("image_urls") or []
    if not image_keys:
        raise HTTPException(400, "No images uploaded")

    context = {
        "analysis_type": analysis.get("analysis_type"),
        "room_purpose": analysis.get("room_purpose"),
        "user_goals": analysis.get("user_goals"),
        "compass_direction": analysis.get("compass_direction"),
    }

    vision_service = get_feng_shui_vision_service()
    bedrock = get_bedrock_service()
    s3 = get_s3_service()

    images = []
    for key in image_keys:
        try:
            image_bytes = s3.get_image_bytes(key)
            images.append({
                "format": _image_format_from_key(key),
                "bytes": image_bytes
            })
        except Exception as e:
            raise HTTPException(500, f"Failed to load image: {str(e)}")

    vision_result = vision_service.analyze_images(
        images=images,
        context=context
    )

    if USE_PERSONA_ORCHESTRATION:
        try:
            orchestrator = get_generation_orchestrator()
            orchestration_result = orchestrator.build_feng_shui_analysis_result(
                analysis=analysis,
                user=user,
                vision_result=vision_result,
            )
        except Exception as exc:
            message = str(exc).lower()
            if 'throttl' in message or 'rate limit' in message or 'too many requests' in message:
                raise HTTPException(
                    503,
                    'Analysis capacity is temporarily tight. Please try again in a moment.'
                )
            raise
        analysis_payload = orchestration_result.payload
        analysis_payload["metadata"].update(
            {
                "model": orchestration_result.metadata.model_id,
                "input_tokens": orchestration_result.input_tokens,
                "output_tokens": orchestration_result.output_tokens,
                "cost_usd": orchestration_result.cost_usd,
            }
        )
        llm_cost = orchestration_result.cost_usd
        db_update_feng_shui(
            analysis_id,
            analysis=analysis_payload,
            cost_usd=float(analysis.get("cost_usd") or 0) + llm_cost + vision_result["cost_usd"],
            analysis_persona_id=orchestration_result.metadata.persona_id,
            analysis_llm_profile_id=orchestration_result.metadata.llm_profile_id,
            analysis_prompt_version=orchestration_result.metadata.prompt_version,
            analysis_theme_tags=orchestration_result.metadata.theme_tags,
            analysis_headline=orchestration_result.metadata.headline,
        )
    else:
        llm_result = bedrock.generate_feng_shui_analysis(
            context=context,
            vision_analysis=vision_result
        )

        analysis_payload = {
            "sections": llm_result["sections"],
            "full_text": llm_result["full_text"],
            "metadata": {
                "model": llm_result["model"],
                "input_tokens": llm_result["input_tokens"],
                "output_tokens": llm_result["output_tokens"],
                "cost_usd": llm_result["cost_usd"],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }

        total_cost = float(analysis.get("cost_usd") or 0) + llm_result["cost_usd"] + vision_result["cost_usd"]
        db_update_feng_shui(analysis_id, analysis=analysis_payload, cost_usd=total_cost)
    return {"status": "complete", "analysis": analysis_payload}


# =====================
# PALM READING ENDPOINTS
# =====================

@app.post("/v1/sessions/{session_id}/palm-upload-url")
def get_palm_upload_url(
    session_id: str,
    content_type: str = "image/jpeg",
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Generate pre-signed URL for palm image upload.
    Client uploads directly to S3 using this URL.
    """
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)
    
    try:
        safe_content_type = _validate_upload_content_type(content_type)
        s3_service = get_s3_service()
        upload_data = s3_service.generate_presigned_upload_url(
            session_id=session_id,
            content_type=safe_content_type
        )
        
        # Store the object key for later retrieval
        db_update_session(session_id, palm_image_url=upload_data["object_key"])
        
        return {
            "upload_url": upload_data["upload_url"],
            "upload_fields": upload_data["upload_fields"],
            "expires_in": upload_data["expires_in"]
        }
        
    except Exception as e:
        raise HTTPException(500, f"Failed to generate upload URL: {str(e)}")


@app.post("/v1/sessions/{session_id}/palm-analyze")
def analyze_palm(
    session_id: str,
    handedness: str = Body("right", embed=True),
    is_dominant: bool = Body(True, embed=True),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Analyze palm image using Claude Vision.
    Requires Complete tier purchase or Palm add-on.
    """
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)

    normalized_handedness = handedness.strip().lower()
    if normalized_handedness not in {"left", "right"}:
        raise HTTPException(400, "handedness must be 'left' or 'right'")
    handedness = normalized_handedness
    
    # Check if palm image uploaded
    if not session.get("palm_image_url"):
        raise HTTPException(400, "No palm image uploaded")
    
    # Check if user has purchased palm feature or selected Complete tier
    purchased = session.get("purchased_products") or []
    inputs = session.get("inputs") or {}
    selected_tier = (inputs.get("selected_tier") or "").lower()
    if selected_tier != "complete" and not _user_has_feature_access(user, purchased, "palm"):
        raise HTTPException(403, "Palm reading requires Complete tier or add-on purchase")
    
    # Check if already analyzed
    if session.get("palm_analysis"):
        return {
            "status": "already_analyzed",
            "palm_analysis": session["palm_analysis"]
        }
    
    try:
        # Get image from S3
        s3_service = get_s3_service()
        image_bytes = s3_service.get_image_bytes(session["palm_image_url"])
        
        # Analyze with Claude Vision
        palm_service = get_palm_vision_service()
        analysis_result = palm_service.analyze_palm(
            image_data=image_bytes,
            handedness=handedness,
            is_dominant=is_dominant
        )
        
        # Store analysis and cost
        db_update_session(
            session_id,
            palm_analysis=analysis_result["features"],
            palm_cost_usd=analysis_result["cost_usd"]
        )
        
        return {
            "status": "analyzed",
            "palm_analysis": analysis_result["features"],
            "metadata": {
                "model": analysis_result["model"],
                "input_tokens": analysis_result["input_tokens"],
                "output_tokens": analysis_result["output_tokens"],
                "cost_usd": analysis_result["cost_usd"]
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"Palm analysis failed: {str(e)}")


# =====================
# PRICING & PURCHASE ENDPOINTS
# =====================

@app.get("/v1/products")
def get_products():
    """Get available products and pricing."""
    verifier = get_purchase_verification_service()
    return {
        "purchase_verification": {
            "ios_ready": verifier.verification_ready("ios"),
            "android_ready": verifier.verification_ready("android"),
            "dev_bypass_enabled": verifier.allow_dev_bypass,
        },
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "price_usd": p["price_usd"],
                "features": p["features"],
                "description": p["description"],
                "is_subscription": p.get("is_subscription", False),
                "billing_period": p.get("billing_period"),
                "seasonal_start": p.get("seasonal_start"),
                "seasonal_end": p.get("seasonal_end"),
                "is_addon": p.get("is_addon", False),
                "is_bundle": p.get("is_bundle", False),
                "bundle_steps": p.get("bundle_steps", []),
            }
            for p in PRODUCTS.values()
        ]
    }


@app.post("/v1/sessions/{session_id}/purchase")
def record_purchase(
    session_id: str,
    payload: PurchaseRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Record a product purchase.
    
    In production, this would verify Apple IAP receipt.
    For now, we trust the client (dev/testing only).
    """
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)
    
    # Validate product exists
    try:
        product = get_product(payload.product_id)
    except ValueError:
        raise HTTPException(400, f"Invalid product ID: {payload.product_id}")
    
    # Get existing purchases
    purchased = session.get("purchased_products") or []
    required_product_id = _required_session_product_id(session)
    preview = session.get("preview") if isinstance(session.get("preview"), dict) else None
    preview_unlock_amount = None
    if preview is not None:
        unlock_price = preview.get("unlock_price")
        if isinstance(unlock_price, dict):
            amount = unlock_price.get("amount")
            if isinstance(amount, (int, float)):
                preview_unlock_amount = float(amount)

    preview_product_id = (preview.get("product_id") or "").strip() if preview else ""
    if preview_unlock_amount is not None and preview_unlock_amount > 0 and not preview_product_id:
        raise HTTPException(400, "Preview contract is invalid for paid unlock")

    if required_product_id and payload.product_id != required_product_id:
        raise HTTPException(400, "Purchase product does not match this preview contract")

    if required_product_id is None and preview_unlock_amount is not None and preview_unlock_amount > 0:
        raise HTTPException(400, "Preview contract is invalid for paid unlock")

    # Active subscription includes all non-subscription features.
    if payload.product_id != ProductSKU.DAILY_ASTRO_TAROT and _has_active_subscription(user):
        return {
            "status": "included_by_subscription",
            "product_id": payload.product_id,
            "transaction_id": payload.transaction_id,
            "purchased_products": purchased,
            "subscription_active": True,
        }
    
    # Validate purchase is allowed
    if not validate_purchase(payload.product_id, purchased):
        raise HTTPException(400, "Purchase not valid (already owned or missing prerequisite)")
    
    verification = _verify_purchase_or_raise(
        product_id=payload.product_id,
        transaction_id=payload.transaction_id,
        receipt_data=payload.receipt_data,
        is_subscription=bool(product.get("is_subscription")),
        platform=payload.platform,
    )

    # Add to purchased products
    purchased.append(payload.product_id)

    # Update session
    db_update_session(session_id, purchased_products=purchased)
    db_record_purchase_transaction(
        user_id=str(user["id"]) if user else None,
        product_id=payload.product_id,
        transaction_id=verification.transaction_id,
        original_transaction_id=verification.original_transaction_id,
        platform=payload.platform,
        provider=verification.provider,
        environment=verification.environment,
        resource_type="session",
        resource_id=session_id,
        entitlement_active=verification.entitlement_active,
        verification_detail=verification.detail,
        receipt_present=bool((payload.receipt_data or "").strip()),
        raw=verification.raw,
    )

    return {
        "status": "purchased",
        "product_id": payload.product_id,
        "transaction_id": payload.transaction_id,
        "purchased_products": purchased,
        "verification": {
            "provider": verification.provider,
            "environment": verification.environment,
            "entitlement_active": verification.entitlement_active,
            "original_transaction_id": verification.original_transaction_id,
        },
    }


@app.get("/v1/sessions/{session_id}/revenue")
def get_session_revenue(
    session_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """Get revenue breakdown for this session."""
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    _assert_session_access(session_id, user)
    
    purchased = session.get("purchased_products") or []
    revenue = calculate_revenue(purchased)
    
    # Add cost data
    preview_cost = float(session.get("preview_cost_usd") or 0)
    reading_cost = float(session.get("reading_cost_usd") or 0)
    palm_cost = float(session.get("palm_cost_usd") or 0)
    total_cost = preview_cost + reading_cost + palm_cost
    
    gross_profit = revenue["net_total"] - total_cost
    margin = (gross_profit / revenue["net_total"] * 100) if revenue["net_total"] > 0 else 0
    
    return {
        "revenue": revenue,
        "costs": {
            "preview": preview_cost,
            "reading": reading_cost,
            "palm": palm_cost,
            "total": total_cost
        },
        "profit": {
            "gross_profit": round(gross_profit, 2),
            "margin_percent": round(margin, 1)
        }
    }


# =====================
# USER ACCOUNT ENDPOINTS
# =====================

@app.post("/v1/auth/register")
def register_user(payload: UserCreate):
    """
    Register a new user account.
    Supports email/password and Apple Sign In.
    """
    user_service = get_user_service()
    auth_service = get_auth_service()
    
    # Check if user already exists
    existing = user_service.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(400, "Email already registered")
    
    # Hash password if provided (email auth)
    password_hash = None
    if payload.password:
        password_hash = auth_service.hash_password(payload.password)
    
    # Create user
    user_id = user_service.create_user(
        email=payload.email,
        password_hash=password_hash,
        display_name=payload.display_name,
        auth_provider=payload.auth_provider,
        provider_user_id=payload.provider_user_id
    )
    
    # Generate access token
    token_data = auth_service.create_access_token(
        user_id=user_id,
        email=payload.email,
        role="user"
    )
    
    # Store token
    user_service.store_auth_token(
        user_id=user_id,
        token=token_data["access_token"]
    )
    
    return {
        "user_id": user_id,
        "email": payload.email,
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_at": token_data["expires_at"]
    }


@app.post("/v1/auth/login")
def login_user(payload: UserLogin):
    """Login with email and password."""
    user_service = get_user_service()
    auth_service = get_auth_service()
    
    # Get user by email
    user = user_service.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(401, "Invalid email or password")
    
    # Verify password
    if not user.get("password_hash"):
        raise HTTPException(401, "This account uses Apple Sign In")
    
    if not auth_service.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    
    # Update last login
    user_service.update_last_login(str(user["id"]))
    
    # Generate access token
    token_data = auth_service.create_access_token(
        user_id=str(user["id"]),
        email=user["email"],
        role=user.get("role", "user")
    )
    
    # Store token
    user_service.store_auth_token(
        user_id=str(user["id"]),
        token=token_data["access_token"]
    )
    
    return {
        "user_id": str(user["id"]),
        "email": user["email"],
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_at": token_data["expires_at"]
    }


@app.post("/v1/auth/apple")
def apple_sign_in(payload: AppleSignIn):
    """
    Authenticate with Apple Sign In.
    Creates account if first time, logs in if existing.
    """
    user_service = get_user_service()
    auth_service = get_auth_service()
    
    # Verify Apple identity token
    apple_data = auth_service.verify_apple_identity_token(payload.identity_token)
    if not apple_data:
        raise HTTPException(401, "Invalid Apple identity token")
    
    # Check if user exists
    user = user_service.get_user_by_provider("apple", payload.user_identifier)
    
    if not user:
        # Create new user
        email = payload.email or apple_data.get("email") or f"{payload.user_identifier}@appleid.com"
        
        user_id = user_service.create_user(
            email=email,
            password_hash=None,
            display_name=payload.full_name,
            auth_provider="apple",
            provider_user_id=payload.user_identifier
        )
    else:
        user_id = str(user["id"])
        email = user["email"]
        
        # Update last login
        user_service.update_last_login(user_id)
    
    # Generate access token
    token_data = auth_service.create_access_token(
        user_id=user_id,
        email=email,
        role="user"
    )
    
    # Store token
    user_service.store_auth_token(
        user_id=user_id,
        token=token_data["access_token"]
    )
    
    return {
        "user_id": user_id,
        "email": email,
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_at": token_data["expires_at"]
    }


@app.post("/v1/auth/logout")
def logout_user(user: dict = Depends(get_current_user)):
    """Logout current user (revoke token)."""
    # Token is in the dependency, but we need the actual token
    # For now, we'll revoke all tokens (logout from all devices)
    user_service = get_user_service()
    user_service.revoke_all_user_tokens(str(user["id"]))
    
    return {"status": "logged_out"}


@app.get("/v1/auth/me")
def get_current_user_profile(user: dict = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    subscription = _get_user_subscription(user)
    subscription_summary = {
        "status": subscription.get("status"),
        "product_id": subscription.get("product_id"),
        "started_at": subscription.get("started_at"),
        "renews_at": subscription.get("renews_at"),
        "canceled_at": subscription.get("canceled_at"),
        "active": _subscription_active(subscription),
    }
    birth_profile = {
        "birth_date": user.get("birth_date").isoformat() if user.get("birth_date") else None,
        "birth_time": user.get("birth_time"),
        "birth_time_unknown": user.get("birth_time_unknown"),
        "birth_location_text": user.get("birth_location_text"),
        "birth_location_normalized": user.get("birth_location_normalized"),
        "birth_location_verified": user.get("birth_location_verified"),
    }
    astrology_profile = _build_astrology_profile_for_user(user)
    return {
        "user_id": str(user["id"]),
        "email": user["email"],
        "display_name": user.get("display_name"),
        "auth_provider": user["auth_provider"],
        "role": user["role"],
        "created_at": user["created_at"].isoformat(),
        "last_login_at": user["last_login_at"].isoformat() if user.get("last_login_at") else None,
        "total_readings": user.get("total_readings", 0),
        "total_spent_usd": float(user.get("total_spent_usd", 0)),
        "subscription": subscription_summary,
        "birth_profile": birth_profile,
        "astrology_profile": astrology_profile,
    }


# Backwards-compatible alias for client profile fetch
@app.get("/v1/users/me")
def get_current_user_profile_alias(user: dict = Depends(get_current_user)):
    return get_current_user_profile(user)


@app.patch("/v1/users/me/profile")
def update_current_user_profile(
    payload: UserProfileUpdate,
    user: dict = Depends(get_current_user),
):
    updates = payload.dict(exclude_none=True)
    if not updates:
        return {"status": "no_changes"}

    db_update_user_profile(str(user["id"]), **updates)
    return {"status": "updated"}


@app.get("/v1/users/me/astrology-profile")
def get_my_astrology_profile(user: dict = Depends(get_current_user)):
    astrology_profile = _build_astrology_profile_for_user(user)
    if not astrology_profile:
        raise HTTPException(404, "Birth profile required")
    return astrology_profile


# =====================
# USER READING LIBRARY
# =====================

@app.get("/v1/users/me/readings")
def get_my_readings(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    Get authenticated user's reading history.
    Returns all past readings with preview and full text.
    """
    user_service = get_user_service()
    
    sessions = user_service.get_user_sessions(
        user_id=str(user["id"]),
        limit=limit,
        offset=offset
    )
    
    # Format for client
    readings = []
    for session in sessions:
        reading_data = {
            "session_id": str(session["id"]),
            "created_at": session["created_at"].isoformat(),
            "question": session.get("inputs", {}).get("question_intention"),
            "status": session["status"],
            "purchased_products": session.get("purchased_products", []),
            "has_reading": session.get("reading") is not None
        }
        
        # Include preview if exists
        if session.get("preview"):
            reading_data["preview"] = session["preview"]
        
        # Include full reading if exists
        if session.get("reading"):
            reading_data["reading"] = session["reading"]
        
        readings.append(reading_data)
    
    return {
        "readings": readings,
        "total": len(readings),
        "limit": limit,
        "offset": offset
    }


@app.post("/v1/sessions/{session_id}/link")
def link_session_to_account(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Link an anonymous session to authenticated user account.
    Allows users to save readings after purchase.
    """
    user_service = get_user_service()
    
    # Verify session exists
    session = db_get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Link to user
    user_service.link_session_to_user(
        user_id=str(user["id"]),
        session_id=session_id
    )
    
    return {
        "status": "linked",
        "session_id": session_id,
        "user_id": str(user["id"])
    }


@app.get("/v1/users/me/continuity")
def get_user_continuity(user: dict = Depends(get_current_user)):
    """Account-level continuity summary for revisit and unfinished journey flows."""
    user_service = get_user_service()
    sessions = user_service.get_user_sessions(user_id=str(user["id"]), limit=250)

    latest_reading = None
    unfinished_sessions: List[Dict[str, Any]] = []
    bundle_progress: List[Dict[str, Any]] = []

    for session in sessions:
        reading = _extract_reading(session)
        preview = _extract_preview(session)
        inputs = session.get("inputs") or {}
        status = (session.get("status") or "").strip().lower()

        if reading and latest_reading is None:
            latest_reading = {
                "session_id": str(session.get("id")),
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
                "question_intention": (inputs.get("question_intention") or "").strip(),
                "flow_type": _flow_type(inputs),
                "status": status,
            }

        if not reading and (preview or status in {"draft", "preview_ready"}):
            unfinished_sessions.append({
                "session_id": str(session.get("id")),
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
                "question_intention": (inputs.get("question_intention") or "").strip(),
                "flow_type": _flow_type(inputs),
                "status": status,
                "has_preview": preview is not None,
                "bundle_id": inputs.get("bundle_id"),
                "bundle_step": inputs.get("bundle_step"),
            })

        progress = _bundle_progress_summary(session)
        if progress and not progress.get("complete"):
            bundle_progress.append(progress)

    ongoing_journeys: List[Dict[str, Any]] = []

    with engine.begin() as conn:
        compatibility_rows = conn.execute(
            text(
                """
                SELECT id, created_at, purchased, preview, reading
                FROM compatibility_readings
                WHERE user_id = CAST(:user_id AS uuid)
                ORDER BY created_at DESC
                LIMIT 20
                """
            ),
            {"user_id": str(user["id"])}
        ).mappings().all()

        for row in compatibility_rows:
            if row.get("reading"):
                continue
            stage = "preview_ready" if row.get("preview") else "input_started"
            if row.get("purchased") and not row.get("reading"):
                stage = "ready_to_generate"
            ongoing_journeys.append({
                "type": "compatibility",
                "id": str(row.get("id")),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "stage": stage,
                "title": "Compatibility reading in progress",
            })

        feng_rows = conn.execute(
            text(
                """
                SELECT id, created_at, analysis_type, purchased, preview, analysis
                FROM feng_shui_analyses
                WHERE user_id = CAST(:user_id AS uuid)
                ORDER BY created_at DESC
                LIMIT 20
                """
            ),
            {"user_id": str(user["id"])}
        ).mappings().all()

        for row in feng_rows:
            if row.get("analysis"):
                continue
            stage = "preview_ready" if row.get("preview") else "input_started"
            if row.get("purchased") and not row.get("analysis"):
                stage = "ready_to_generate"
            ongoing_journeys.append({
                "type": "feng_shui",
                "id": str(row.get("id")),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "stage": stage,
                "analysis_type": row.get("analysis_type"),
                "title": "Feng Shui journey in progress",
            })

    cadence_hint = "return_this_week"
    if unfinished_sessions:
        cadence_hint = "return_tomorrow" if any(item.get("has_preview") for item in unfinished_sessions) else "return_this_week"
    elif latest_reading:
        flow_type = (latest_reading.get("flow_type") or "").lower()
        cadence_hint = "return_tomorrow" if flow_type in {"combined", "daily_horoscope"} else "return_this_week"

    return {
        "latest_reading": latest_reading,
        "unfinished_sessions": unfinished_sessions[:5],
        "bundle_progress": bundle_progress[:5],
        "ongoing_journeys": ongoing_journeys[:6],
        "counts": {
            "unfinished_sessions": len(unfinished_sessions),
            "bundle_progress": len(bundle_progress),
            "ongoing_journeys": len(ongoing_journeys),
        },
        "cadence_hint": cadence_hint,
    }


@app.get("/v1/users/me/stats")
def get_user_stats(user: dict = Depends(get_current_user)):
    """Get user's reading statistics and spending."""
    user_service = get_user_service()
    
    # Get all user sessions
    sessions = user_service.get_user_sessions(
        user_id=str(user["id"]),
        limit=1000
    )
    
    # Calculate stats
    total_sessions = len(sessions)
    completed_readings = sum(1 for s in sessions if s.get("status") == "complete")
    
    # Astrology stats
    sun_signs = {}
    for session in sessions:
        preview = session.get("preview", {})
        astro = preview.get("astrology_facts", {})
        sun_sign = astro.get("sun_sign")
        if sun_sign:
            sun_signs[sun_sign] = sun_signs.get(sun_sign, 0) + 1
    
    # Tarot stats
    tarot_cards = {}
    for session in sessions:
        tarot = session.get("tarot", {})
        cards = tarot.get("cards", [])
        for card_data in cards:
            card = card_data.get("card")
            if card:
                tarot_cards[card] = tarot_cards.get(card, 0) + 1
    
    return {
        "total_sessions": total_sessions,
        "completed_readings": completed_readings,
        "total_readings": user.get("total_readings", 0),
        "total_spent_usd": float(user.get("total_spent_usd", 0)),
        "member_since": user["created_at"].isoformat(),
        "subscription_active": _subscription_active(_get_user_subscription(user)),
        "insights": {
            "most_common_sun_sign": max(sun_signs, key=sun_signs.get) if sun_signs else None,
            "most_drawn_card": max(tarot_cards, key=tarot_cards.get) if tarot_cards else None,
            "sun_sign_distribution": sun_signs,
            "tarot_frequency": dict(sorted(tarot_cards.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    }


@app.get("/v1/users/me/purchases")
def get_user_purchase_history(
    user: dict = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0,
):
    """
    Unified purchase/billing history for account view.
    Aggregates session purchases, compatibility, Feng Shui, offerings, and
    current subscription lifecycle.
    """
    user_id = str(user["id"])
    items: List[Dict[str, Any]] = []

    def _iso(value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        if value is None:
            return ""
        return str(value)

    def _append_item(
        *,
        reference_id: str,
        created_at: Any,
        product_id: str,
        source: str,
        status: str = "purchased",
        amount_override: Optional[float] = None,
        net_override: Optional[float] = None,
    ):
        product = PRODUCTS.get(product_id, {})
        amount = amount_override if amount_override is not None else float(product.get("price_usd", 0))
        net_amount = net_override if net_override is not None else float(product.get("price_after_apple_cut", amount))
        items.append(
            {
                "reference_id": reference_id,
                "created_at": _iso(created_at),
                "product_id": product_id,
                "product_name": product.get("name", product_id),
                "amount_usd": round(float(amount), 2),
                "net_usd": round(float(net_amount), 2),
                "source": source,
                "status": status,
            }
        )

    with engine.begin() as conn:
        session_rows = conn.execute(
            text(
                """
                SELECT s.id, s.created_at, s.purchased_products
                FROM user_sessions us
                JOIN sessions s ON s.id = us.session_id
                WHERE us.user_id = CAST(:user_id AS uuid)
                  AND s.purchased_products IS NOT NULL
                ORDER BY s.created_at DESC
                """
            ),
            {"user_id": user_id},
        ).mappings().all()

        for row in session_rows:
            purchased = row.get("purchased_products") or []
            if isinstance(purchased, str):
                try:
                    purchased = json.loads(purchased)
                except Exception:
                    purchased = []
            if not isinstance(purchased, list):
                continue
            for product_id in purchased:
                if product_id not in PRODUCTS:
                    continue
                _append_item(
                    reference_id=str(row["id"]),
                    created_at=row.get("created_at"),
                    product_id=product_id,
                    source="session",
                )

        compatibility_rows = conn.execute(
            text(
                """
                SELECT id, created_at
                FROM compatibility_readings
                WHERE user_id = CAST(:user_id AS uuid) AND purchased = true
                ORDER BY created_at DESC
                """
            ),
            {"user_id": user_id},
        ).mappings().all()

        for row in compatibility_rows:
            _append_item(
                reference_id=str(row["id"]),
                created_at=row.get("created_at"),
                product_id=ProductSKU.COMPATIBILITY,
                source="compatibility",
            )

        feng_rows = conn.execute(
            text(
                """
                SELECT id, created_at, analysis_type, product_id
                FROM feng_shui_analyses
                WHERE user_id = CAST(:user_id AS uuid) AND purchased = true
                ORDER BY created_at DESC
                """
            ),
            {"user_id": user_id},
        ).mappings().all()

        for row in feng_rows:
            product_id = row.get("product_id")
            if not product_id:
                product_id = _feng_shui_product_for_type(row.get("analysis_type") or "single_room")
            if product_id not in PRODUCTS:
                continue
            _append_item(
                reference_id=str(row["id"]),
                created_at=row.get("created_at"),
                product_id=product_id,
                source="feng_shui",
            )

        offering_rows = conn.execute(
            text(
                """
                SELECT id, created_at, amount_usd
                FROM blessing_offerings
                WHERE user_id = CAST(:user_id AS uuid)
                ORDER BY created_at DESC
                """
            ),
            {"user_id": user_id},
        ).mappings().all()

        for row in offering_rows:
            amount = float(row.get("amount_usd") or 0)
            if abs(amount - 1.0) < 0.001:
                product_id = ProductSKU.BLESSING_OFFERING_100
            elif abs(amount - 3.0) < 0.001:
                product_id = ProductSKU.BLESSING_OFFERING_300
            elif abs(amount - 5.0) < 0.001:
                product_id = ProductSKU.BLESSING_OFFERING_500
            else:
                product_id = ProductSKU.BLESSING_OFFERING_100
            _append_item(
                reference_id=str(row["id"]),
                created_at=row.get("created_at"),
                product_id=product_id,
                source="blessing_offering",
                amount_override=amount,
                net_override=round(amount * 0.7, 2),
            )

    subscription = _get_user_subscription(user)
    if subscription:
        subscription_product = subscription.get("product_id") or ProductSKU.DAILY_ASTRO_TAROT
        if subscription_product in PRODUCTS:
            started_at = subscription.get("started_at")
            if started_at:
                _append_item(
                    reference_id=f"subscription:{user_id}:start",
                    created_at=started_at,
                    product_id=subscription_product,
                    source="subscription",
                    status="activated",
                )
            canceled_at = subscription.get("canceled_at")
            if canceled_at:
                _append_item(
                    reference_id=f"subscription:{user_id}:cancel",
                    created_at=canceled_at,
                    product_id=subscription_product,
                    source="subscription",
                    status="canceled",
                    amount_override=0.0,
                    net_override=0.0,
                )

    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    total = len(items)
    start = max(offset, 0)
    end = start + max(limit, 0)

    return {
        "purchases": items[start:end],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# =====================
# SUBSCRIPTION ENDPOINTS
# =====================

@app.get("/v1/subscription")
def get_subscription_status(user: dict = Depends(get_current_user)):
    """Get current user's subscription status."""
    subscription = _get_user_subscription(user)
    active = _subscription_active(subscription)
    return {
        "subscription": subscription,
        "active": active,
        "access_all_services": active,
    }


@app.post("/v1/entitlements/refresh")
def refresh_entitlements(user: dict = Depends(get_current_user)):
    user_id = str(user["id"])
    transactions = db_get_user_purchase_transactions(user_id)
    verified_products = [
        row.get("product_id")
        for row in transactions
        if row.get("status") == "verified"
        and row.get("entitlement_active")
        and row.get("product_id")
    ]
    unique_products = sorted(set(str(product_id) for product_id in verified_products))
    subscription = _get_user_subscription(user)
    active = _subscription_active(subscription)

    return {
        "status": "refreshed",
        "subscription_active": active,
        "verified_products": unique_products,
        "feature_entitlements": {
            "compatibility": _compatibility_included_for_user(user),
            "feng_shui_single": _feng_shui_included_for_user(user, ProductSKU.FENG_SHUI_SINGLE),
            "feng_shui_full": _feng_shui_included_for_user(user, ProductSKU.FENG_SHUI_FULL),
            "lunar_forecast": _user_has_any_product(user, [ProductSKU.LUNAR_FORECAST, ProductSKU.BUNDLE_NEW_BEGINNINGS]) or active,
        },
        "transactions": [
            {
                "product_id": row.get("product_id"),
                "transaction_id": row.get("transaction_id"),
                "original_transaction_id": row.get("original_transaction_id"),
                "resource_type": row.get("resource_type"),
                "resource_id": row.get("resource_id"),
                "environment": row.get("environment"),
                "provider": row.get("provider"),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
            }
            for row in transactions
        ],
    }


@app.post("/v1/entitlements/restore")
def restore_entitlement(
    payload: PurchaseRequest,
    user: dict = Depends(get_current_user)
):
    """Restore an already-purchased entitlement onto the authenticated account."""
    product = PRODUCTS.get(payload.product_id)
    if not product:
        raise HTTPException(400, "Invalid product ID")
    if product.get("is_subscription"):
        raise HTTPException(400, "Use /v1/subscription/activate for subscription restores")

    verification = _verify_purchase_or_raise(
        product_id=payload.product_id,
        transaction_id=payload.transaction_id,
        receipt_data=payload.receipt_data,
        is_subscription=False,
        platform=payload.platform,
    )

    db_record_purchase_transaction(
        user_id=str(user["id"]),
        product_id=payload.product_id,
        transaction_id=verification.transaction_id,
        original_transaction_id=verification.original_transaction_id,
        platform=payload.platform,
        provider=verification.provider,
        environment=verification.environment,
        resource_type="restore",
        resource_id=str(user["id"]),
        entitlement_active=verification.entitlement_active,
        verification_detail=verification.detail,
        receipt_present=bool((payload.receipt_data or "").strip()),
        raw=verification.raw,
    )

    return {
        "status": "restored",
        "product_id": payload.product_id,
        "transaction_id": verification.transaction_id,
        "verification": {
            "provider": verification.provider,
            "environment": verification.environment,
            "entitlement_active": verification.entitlement_active,
            "original_transaction_id": verification.original_transaction_id,
        },
    }


@app.post("/v1/subscription/activate")
def activate_subscription(
    payload: SubscriptionActivateRequest,
    user: dict = Depends(get_current_user)
):
    """Activate subscription after explicit store verification."""
    product = PRODUCTS.get(payload.product_id)
    if not product or not product.get("is_subscription"):
        raise HTTPException(400, "Invalid subscription product")

    verification = _verify_purchase_or_raise(
        product_id=payload.product_id,
        transaction_id=payload.transaction_id,
        receipt_data=payload.receipt_data,
        is_subscription=True,
        platform=payload.platform,
    )

    now = datetime.now(timezone.utc)
    renews_at = now + timedelta(days=30)
    subscription = {
        "status": "active",
        "product_id": payload.product_id,
        "transaction_id": verification.transaction_id,
        "original_transaction_id": verification.original_transaction_id or verification.transaction_id,
        "started_at": now.isoformat(),
        "renews_at": renews_at.isoformat(),
        "canceled_at": None,
        "auto_renew": True,
        "access_scope": "all_services",
        "verification_provider": verification.provider,
        "verification_environment": verification.environment,
    }
    user_service = get_user_service()
    user_service.set_subscription(str(user["id"]), subscription)
    db_record_purchase_transaction(
        user_id=str(user["id"]),
        product_id=payload.product_id,
        transaction_id=verification.transaction_id,
        original_transaction_id=verification.original_transaction_id,
        platform=payload.platform,
        provider=verification.provider,
        environment=verification.environment,
        resource_type="subscription",
        resource_id=str(user["id"]),
        entitlement_active=verification.entitlement_active,
        verification_detail=verification.detail,
        receipt_present=bool((payload.receipt_data or "").strip()),
        raw=verification.raw,
    )
    return {"status": "active", "subscription": subscription}


@app.post("/v1/subscription/cancel")
def cancel_subscription(user: dict = Depends(get_current_user)):
    """Cancel subscription (keeps access until renews_at)."""
    user_service = get_user_service()
    subscription = _get_user_subscription(user)
    if not subscription:
        raise HTTPException(400, "No active subscription")

    subscription["status"] = "canceled"
    subscription["canceled_at"] = datetime.now(timezone.utc).isoformat()
    subscription["auto_renew"] = False
    user_service.set_subscription(str(user["id"]), subscription)
    return {"status": "canceled", "subscription": subscription}


@app.get("/v1/admin/blessings/summary")
def get_blessings_summary(user: dict = Depends(require_admin)):
    """Admin summary of blessings and offerings."""
    with engine.begin() as conn:
        row = conn.execute(
            text("""
            SELECT COUNT(*) as total_offerings,
                   COALESCE(SUM(amount_usd), 0) as total_amount
            FROM blessing_offerings
            """)
        ).mappings().first()

    return {
        "total_offerings": int(row["total_offerings"]) if row else 0,
        "total_amount_usd": float(row["total_amount"]) if row else 0.0
    }


@app.get("/v1/admin/summary")
def get_admin_summary(user: dict = Depends(require_admin)):
    """Admin summary for sessions, users, costs, and revenue."""
    summary = {}
    with engine.begin() as conn:
        users_row = conn.execute(
            text("SELECT COUNT(*) as total_users FROM users")
        ).mappings().first()
        users_30_row = conn.execute(
            text("SELECT COUNT(*) as users_30 FROM users WHERE created_at >= now() - interval '30 days'")
        ).mappings().first()
        sessions_row = conn.execute(
            text("SELECT COUNT(*) as total_sessions FROM sessions")
        ).mappings().first()
        sessions_today_row = conn.execute(
            text("SELECT COUNT(*) as sessions_today FROM sessions WHERE created_at::date = now()::date")
        ).mappings().first()
        status_row = conn.execute(
            text("""
            SELECT
              SUM(CASE WHEN status = 'preview_ready' THEN 1 ELSE 0 END) AS previews,
              SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) AS readings
            FROM sessions
            """)
        ).mappings().first()
        costs_row = conn.execute(
            text("""
            SELECT
              COALESCE(SUM(preview_cost_usd), 0) as preview_cost,
              COALESCE(SUM(reading_cost_usd), 0) as reading_cost,
              COALESCE(SUM(palm_cost_usd), 0) as palm_cost
            FROM sessions
            """)
        ).mappings().first()
        feng_row = conn.execute(
            text("""
            SELECT
              COUNT(*) as feng_total,
              SUM(CASE WHEN purchased THEN 1 ELSE 0 END) as feng_purchased,
              COALESCE(SUM(cost_usd), 0) as feng_cost
            FROM feng_shui_analyses
            """)
        ).mappings().first()
        comp_row = conn.execute(
            text("""
            SELECT
              COUNT(*) as comp_total,
              SUM(CASE WHEN purchased THEN 1 ELSE 0 END) as comp_purchased
            FROM compatibility_readings
            """)
        ).mappings().first()
        offering_row = conn.execute(
            text("""
            SELECT COUNT(*) as total_offerings,
                   COALESCE(SUM(amount_usd), 0) as total_amount
            FROM blessing_offerings
            """)
        ).mappings().first()
        purchased_rows = conn.execute(
            text("SELECT purchased_products FROM sessions WHERE purchased_products IS NOT NULL")
        ).mappings().all()

    revenue_gross = 0.0
    revenue_net = 0.0
    for row in purchased_rows:
        purchased = row.get("purchased_products") or []
        try:
            revenue = calculate_revenue(purchased)
            revenue_gross += revenue["gross_total"]
            revenue_net += revenue["net_total"]
        except Exception:
            continue

    summary = {
        "users": {
            "total": int(users_row["total_users"]) if users_row else 0,
            "last_30_days": int(users_30_row["users_30"]) if users_30_row else 0
        },
        "sessions": {
            "total": int(sessions_row["total_sessions"]) if sessions_row else 0,
            "today": int(sessions_today_row["sessions_today"]) if sessions_today_row else 0,
            "previews": int(status_row["previews"] or 0) if status_row else 0,
            "readings": int(status_row["readings"] or 0) if status_row else 0
        },
        "costs": {
            "preview_usd": float(costs_row["preview_cost"]) if costs_row else 0.0,
            "reading_usd": float(costs_row["reading_cost"]) if costs_row else 0.0,
            "palm_usd": float(costs_row["palm_cost"]) if costs_row else 0.0,
            "feng_shui_usd": float(feng_row["feng_cost"]) if feng_row else 0.0
        },
        "feng_shui": {
            "total": int(feng_row["feng_total"] or 0) if feng_row else 0,
            "purchased": int(feng_row["feng_purchased"] or 0) if feng_row else 0
        },
        "compatibility": {
            "total": int(comp_row["comp_total"] or 0) if comp_row else 0,
            "purchased": int(comp_row["comp_purchased"] or 0) if comp_row else 0
        },
        "blessings": {
            "total_offerings": int(offering_row["total_offerings"] or 0) if offering_row else 0,
            "total_amount_usd": float(offering_row["total_amount"] or 0) if offering_row else 0.0
        },
        "revenue": {
            "gross_usd": round(revenue_gross, 2),
            "net_usd": round(revenue_net, 2)
        }
    }

    return summary
