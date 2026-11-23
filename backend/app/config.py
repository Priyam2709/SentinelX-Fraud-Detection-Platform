"""
SentinelX Configuration Module
Loads settings from environment variables or .env file with production defaults.
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "SentinelX Fraud Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # MongoDB Settings
    # Supports MongoDB Atlas connection strings e.g. mongodb+srv://<user>:<password>@cluster.mongodb.net
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "sentinelx_fraud_db")
    USE_MOCK_IF_NO_MONGO: bool = True
    
    # ML Models path
    MODELS_DIR: str = os.getenv(
        "MODELS_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml", "models")
    )
    ACTIVE_MODEL_VERSION: str = "xgb_v1.0"
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "sentinelx-super-secret-key-change-in-prod-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
