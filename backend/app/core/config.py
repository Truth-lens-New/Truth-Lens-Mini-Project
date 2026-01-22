"""
TruthLens Backend Configuration

Loads environment variables and provides typed settings for the application.
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://truthlens:truthlens_secret@localhost:5432/truthlens"
    
    # JWT
    jwt_secret_key: str = "your_super_secret_jwt_key_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # API Keys
    gemini_api_key: str = ""
    google_factcheck_api_key: str = ""
    gnews_api_key: str = ""
    groq_api_key: str = ""
    
    # CORS
    backend_cors_origins: str = '["http://localhost:5173","http://localhost:3000"]'
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
