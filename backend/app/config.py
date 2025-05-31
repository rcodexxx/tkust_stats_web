import datetime
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")  # 必須由環境變數提供

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(
        hours=1
    )  # Access Token 有效期，例如 1 小時
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(
        days=30
    )  # Refresh Token 有效期，例如 30 天

    # CORS 設定 (也可以在這裡設定，然後在 create_app 中讀取)
    # CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', "http://localhost:5173,http://127.0.0.1:5173")
    # CORS_RESOURCES = {r"/api/*": {"origins": CORS_ALLOWED_ORIGINS.split(',') if CORS_ALLOWED_ORIGINS != "*" else "*"}}

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_ECHO = True # 可選，顯示執行的 SQL


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory:"
    )
    WTF_CSRF_ENABLED = False  # 測試時通常禁用 CSRF (如果使用 Flask-WTF)


class ProductionConfig(Config):
    # 生產環境的 SECRET_KEY 和 DATABASE_URL 必須透過環境變數設定
    # 任何生產環境特定的設定可以在這裡覆寫
    pass


config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig,
)
