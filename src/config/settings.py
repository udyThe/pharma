"""
Pharma Agentic AI - Configuration Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MOCK_DATA_DIR: Path = BASE_DIR / "mock_data"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    DATA_DIR: Path = BASE_DIR / "data"
    
    # Groq Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    GROQ_RATE_PER_SEC: int = int(os.getenv("GROQ_RATE_PER_SEC", "5"))
    GROQ_BURST: int = int(os.getenv("GROQ_BURST", "10"))
    USE_ASYNC_QUEUE: bool = os.getenv("USE_ASYNC_QUEUE", "false").lower() == "true"

    # External data APIs (optional)
    MARKET_API_URL: str = os.getenv("MARKET_API_URL", "")
    PATENT_API_URL: str = os.getenv("PATENT_API_URL", "")
    CLINICAL_API_URL: str = os.getenv("CLINICAL_API_URL", "")
    SOCIAL_API_URL: str = os.getenv("SOCIAL_API_URL", "")
    COMPETITOR_API_URL: str = os.getenv("COMPETITOR_API_URL", "")
    DATA_API_KEY: str = os.getenv("DATA_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    RAG_CACHE_TTL: int = int(os.getenv("RAG_CACHE_TTL", "1800"))
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Infra
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_BACKEND_URL: str = os.getenv("CELERY_BACKEND_URL", REDIS_URL)
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
    
    def __init__(self):
        # Ensure directories exist
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate required configuration."""
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required. Set it in .env file.")
        return True


# Global settings instance
settings = Settings()
