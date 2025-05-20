# app/config.py
import os
from dotenv import load_dotenv  # 用於從 .env 檔案載入環境變數

# 專案的根目錄 (tkust_stats_web/)
# __file__ 是 config.py 的路徑: tkust_stats_web/app/config.py
# os.path.dirname(__file__) 是 app/
# os.path.join(os.path.dirname(__file__), os.pardir) 是 tkust_stats_web/ (專案根目錄)
# project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
# dotenv_path = os.path.join(project_root_dir, '.env')

# load_dotenv() 會自動尋找執行腳本目錄或專案根目錄下的 .env 檔案。
# 在 Docker 環境中，環境變數通常由 docker-compose.yml 的 env_file 或 environment 指令注入。
# 但為了方便本地非 Docker 環境執行 (例如直接 python run.py)，在這裡載入也是一個好習慣。
# 如果 .env 檔案與 run.py 在同一層 (專案根目錄)，Flask CLI 通常會自動載入。
# 為了確保任何執行方式都能載入，可以明確指定路徑：
# basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # Assuming config.py is in app/
# load_dotenv(os.path.join(basedir, '.env'))
# 或者，由於我們的 .env 檔案在專案根目錄，而 run.py 也在那裡，
# 當執行 run.py 時，Python 的當前工作目錄通常是專案根目錄，所以 load_dotenv() 通常能找到它。
# 如果在 app/__init__.py 中呼叫 create_app 時直接 load_dotenv()，那它會相對於 app/ 目錄尋找。
# 最穩妥的方式是，如果您的 .env 在專案根目錄，而您的啟動腳本 (如 run.py) 也在根目錄，
# 可以在 run.py 的頂部執行 load_dotenv()。
# 或者，如果 config.py 負責載入，確保路徑正確：
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')  # 指向專案根目錄的 .env
load_dotenv(dotenv_path=dotenv_path)


class Config:
    """
    基礎設定類別，所有環境通用的設定。
    特定環境的設定可以繼承這個類別並覆寫。
    """
    # 安全性相關
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-should-set-a-very-very-secret-key'
    # 警告: 上面的 'you-should-set-a-very-very-secret-key' 僅為預設值，
    # 在生產環境中務必透過環境變數設定一個強隨機的 SECRET_KEY。

    # 資料庫相關
    # SQLALCHEMY_DATABASE_URI 會從環境變數 DATABASE_URL 讀取。
    # 這是 Docker (透過 .env 和 docker-compose.yml) 和 Render (平台設定) 提供的主要方式。
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # 如果 DATABASE_URL 沒有設定，您可以選擇提供一個本地開發用的預設 SQLite 路徑，
    # 但既然我們都用 Docker + PostgreSQL，最好是確保 DATABASE_URL 總是被設定。
    # 例如: or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'instance', 'dev.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 建議設為 False 以避免不必要的警告和效能開銷

    # 其他應用程式設定
    # 例如: UPLOAD_FOLDER, MAIL_SERVER, 等等。
    # DEBUG 模式不應該在 Config 基礎類別中直接設為 True
    DEBUG = False  # 生產環境預設值
    TESTING = False  # 測試環境預設值


class DevelopmentConfig(Config):
    """開發環境特定設定"""
    DEBUG = True
    # 如果本地開發時 (即使是用 Docker)，希望使用不同的資料庫URI (例如本地的 SQLite 而非 Docker內的 Postgres)
    # 可以在 .env 中設定一個不同的 DATABASE_URL，或者在這裡覆寫。
    # 但我們目前的設計是本地 Docker 也使用 PostgreSQL，所以通常不需要覆寫 SQLALCHEMY_DATABASE_URI。
    # SQLALCHEMY_ECHO = True # (可選) 輸出 SQLAlchemy 執行的 SQL 語句，方便除錯


class TestingConfig(Config):
    """測試環境特定設定"""
    TESTING = True
    # 測試時通常使用記憶體中的 SQLite 或一個專用的測試資料庫
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    # 確保測試時 CSRF 保護等被適當處理 (例如，如果使用 Flask-WTF)
    WTF_CSRF_ENABLED = False  # 測試時通常禁用 CSRF


class ProductionConfig(Config):
    """生產環境特定設定"""
    # DEBUG 和 TESTING 預設為 False (繼承自 Config)
    # 生產環境的 SECRET_KEY 和 DATABASE_URL 必須透過環境變數設定。
    # 可以在此處加入其他生產環境特定的優化或安全設定。
    pass


# 提供一個字典，方便在 app/__init__.py 的 create_app 工廠函數中根據環境名稱選擇設定類別
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig  # 當 FLASK_CONFIG 未設定時的預設選項
)

# 方便直接匯入使用的目前設定 (根據 FLASK_CONFIG 環境變數)
# config_name = os.environ.get('FLASK_CONFIG', 'default')
# current_config = config_by_name[config_name]