# backend/app/config.py
import os
# from dotenv import load_dotenv # 如果在這裡載入 .env

# 如果 .env 在專案根目錄 (backend/.env)
# basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) # 指向 backend/
# load_dotenv(os.path.join(basedir, '.env'))
# 通常 load_dotenv() 在 create_app 的開頭或 run.py 頂部執行一次即可

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_default_and_insecure_secret_key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # 必須由環境變數提供

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
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False # 測試時通常禁用 CSRF (如果使用 Flask-WTF)

class ProductionConfig(Config):
    # 生產環境的 SECRET_KEY 和 DATABASE_URL 必須透過環境變數設定
    # 任何生產環境特定的設定可以在這裡覆寫
    pass

config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig
)