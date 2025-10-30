"""
Neural Nexus v3.0 - Configuration Settings
Loads environment variables and provides application configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/neural_nexus_v3')
    
    # Riot API Keys
    RIOT_API_KEY_APEX: str = os.getenv('RIOT_API_KEY_APEX', '')
    RIOT_API_KEY_NEXUS: str = os.getenv('RIOT_API_KEY_NEXUS', '')
    
    # Collection Settings
    REGIONS: list[str] = os.getenv('REGIONS', 'na1,euw1,kr').split(',')
    MATCH_HISTORY_DEPTH: int = int(os.getenv('MATCH_HISTORY_DEPTH', '200'))
    APEX_TIERS: list[str] = os.getenv('APEX_TIERS', 'CHALLENGER,GRANDMASTER').split(',')
    
    # Storage Configuration
    DATA_PATH: Path = Path(os.getenv('DATA_PATH', 'F:/neural_nexus_data_v3'))
    LOG_PATH: Path = Path(os.getenv('LOG_PATH', 'F:/neural_nexus_data_v3/logs'))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', '120'))
    
    # Coordination Settings
    APEX_POLL_INTERVAL: int = int(os.getenv('APEX_POLL_INTERVAL', '5'))
    NEXUS_POLL_INTERVAL: int = int(os.getenv('NEXUS_POLL_INTERVAL', '10'))
    MATCH_LOCK_EXPIRY_MINUTES: int = int(os.getenv('MATCH_LOCK_EXPIRY_MINUTES', '60'))
    
    # Regional Routing Mappings
    REGIONAL_ROUTING = {
        'na1': 'americas',
        'br1': 'americas',
        'la1': 'americas',
        'la2': 'americas',
        'euw1': 'europe',
        'eun1': 'europe',
        'tr1': 'europe',
        'ru': 'europe',
        'kr': 'asia',
        'jp1': 'asia',
        'oc1': 'sea',
        'ph2': 'sea',
        'sg2': 'sea',
        'th2': 'sea',
        'tw2': 'sea',
        'vn2': 'sea'
    }
    
    @classmethod
    def get_regional_routing(cls, platform: str) -> str:
        """Get regional routing for a platform (e.g., na1 -> americas)"""
        return cls.REGIONAL_ROUTING.get(platform.lower(), 'americas')
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required settings and return list of errors"""
        errors = []
        
        if not cls.RIOT_API_KEY_APEX:
            errors.append("RIOT_API_KEY_APEX is required")
        
        if not cls.RIOT_API_KEY_NEXUS:
            errors.append("RIOT_API_KEY_NEXUS is required")
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        if not cls.DATA_PATH.exists():
            errors.append(f"DATA_PATH does not exist: {cls.DATA_PATH}")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration (sanitized)"""
        print("=" * 60)
        print("Neural Nexus v3.0 - Configuration")
        print("=" * 60)
        print(f"Database: {cls.DATABASE_URL.split('@')[-1]}")  # Hide credentials
        print(f"APEX Key: {'*' * 20}{cls.RIOT_API_KEY_APEX[-8:] if cls.RIOT_API_KEY_APEX else 'NOT SET'}")
        print(f"NEXUS Key: {'*' * 20}{cls.RIOT_API_KEY_NEXUS[-8:] if cls.RIOT_API_KEY_NEXUS else 'NOT SET'}")
        print(f"Regions: {', '.join(cls.REGIONS)}")
        print(f"Match History Depth: {cls.MATCH_HISTORY_DEPTH}")
        print(f"Data Path: {cls.DATA_PATH}")
        print(f"Rate Limit: {cls.RATE_LIMIT_REQUESTS} requests per {cls.RATE_LIMIT_WINDOW_SECONDS}s")
        print("=" * 60)


# Global settings instance
settings = Settings()


if __name__ == "__main__":
    # Test configuration
    settings.print_config()
    
    errors = settings.validate()
    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration is valid!")