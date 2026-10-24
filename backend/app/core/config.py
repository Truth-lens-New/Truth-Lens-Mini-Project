"""
TruthLens Backend Configuration

Loads environment variables and provides typed settings for the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database (Legacy/External)
    postgres_user: str = "truthlens"
    postgres_password: str = "truthlens_secret"
    postgres_db: str = "truthlens"
    database_url: str = "postgresql+asyncpg://truthlens:truthlens_secret@postgres:5432/truthlens"
    
    # JWT
    jwt_secret_key: str = "your_super_secret_jwt_key_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # API Keys
    gemini_api_key: str = ""
    google_factcheck_api_key: str = ""
    gnews_api_key: str = ""
    groq_api_key: str = ""

    # Twilio WhatsApp Bot
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"  # Twilio sandbox default
    # Validate X-Twilio-Signature on the inbound webhook (recommended).
    # Disable only when a trusted proxy rewrites the request URL so the
    # signature URL cannot be reconstructed exactly.
    twilio_validate_signatures: bool = True
    # Externally-visible webhook URL (e.g. https://xyz.ngrok.io/api/v1/whatsapp)
    # used for signature validation when running behind a proxy/tunnel.
    twilio_webhook_public_url: str = ""

    # CORS
    backend_cors_origins: str = '["http://localhost:5173","http://localhost:3000"]'

    # Deployment environment: "development" (default) or "production".
    # In production, startup fails with sample JWT/database credentials.
    environment: str = "development"

    # Optional LLM crux extraction (uses Gemini for long documents).
    # OFF by default: local spaCy crux ranking is used instead.
    use_llm_crux: bool = False
    gemini_model: str = "gemini-2.5-flash"

    # Investigation concurrency / rate protection
    max_concurrent_investigations: int = 2
    max_investigation_rate: int = 10          # per user per rate window
    rate_window_seconds: float = 60.0
    max_claims_per_investigation: int = 5     # cap claims investigated per request
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.backend_cors_origins)
        except json.JSONDecodeError:
            return ["http://localhost:5173", "http://localhost:3000"]
    
    # Data paths
    domain_trust_csv_path: str = "data/domain_trust_seed.csv"
    
    # Pipeline versioning
    pipeline_version: str = "0.1.0"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
