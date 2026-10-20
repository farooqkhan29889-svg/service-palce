from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "ServeNow API"
    DEBUG: bool = True
    API_VERSION: str = "1.0.0"

    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "servenow"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Payment (Razorpay)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # Platform settings
    PLATFORM_COMMISSION_RATE: float = 0.10  # 10%
    GST_RATE: float = 0.18  # 18%

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = ""

    # Redis (for caching and real-time)
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
