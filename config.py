"""Application configuration"""

import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-local-only")
    # PostgreSQL接続URL（ローカル開発用、本番はRenderで設定）
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///circle_events.db")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-secure-key")


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
