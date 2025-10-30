import os
from typing import List
from dotenv import load_dotenv # type: ignore

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration from environment variables"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/neural_nexus")
    
    # API Keys
    RIOT_API_KEY_COLLECTION: str = os.getenv("RIOT_API_KEY_COLLECTION", "")
    RIOT_API_KEY_ENRICHMENT: str = os.getenv("RIOT_API_KEY_ENRICHMENT", "")
    
    # Regions
    REGIONS: List[str] = os.getenv("REGIONS", "na1,euw1,kr").split(",")
    
    # Collection Settings
    MIN_TIER: str = os.getenv("MIN_TIER", "DIAMOND")
    COLLECTION_BATCH_SIZE: int = int(os.getenv("COLLECTION_BATCH_SIZE", "100"))
    
    # Storage
    DATA_PATH: str = os.getenv("DATA_PATH", "F:/neural_nexus_data")
    LOG_PATH: str = os.getenv("LOG_PATH", "F:/neural_nexus_data/logs")
    
    # API Server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "120"))
    
    @classmethod
    def validate(cls) -> bool:
        """Check if required settings are present"""
        if not cls.RIOT_API_KEY_COLLECTION:
            raise ValueError("RIOT_API_KEY_COLLECTION is required")
        if not cls.RIOT_API_KEY_ENRICHMENT:
            raise ValueError("RIOT_API_KEY_ENRICHMENT is required")
        return True

# Global settings instance
settings = Settings()