# backend/app/__init__.py

import os
from flask import Flask
from dotenv import load_dotenv  # 通常在 config.py 或 run.py 更早載入，但這裡確保一下
from datetime import datetime  # 用於 footer 的年份

# 匯入設定 (假設您有 config.py 和 config_by_name 字典)
from .config import config_by_name

# 匯入擴充套件實例 (在 extensions.py 中定義)
from .extensions import db, migrate, cors  # 假設您在 extensions.py 中也定義了 cors = CORS()


def create_app(config_name=None):
    """
    應用程式工廠函數。
    """
    # 如果 .env 檔案與 run.py 在同一層 (專案根目錄)，
    # 且 run.py 是啟動點，它通常會先載入 .env。
    # 如果直接測試或從不同入口點啟動，確保 .env 被載入。
    # 假設 dotenv_path 指向 backend/.env (如果 create_app 從 backend/run.py 調用)
    # 或者，如果您總是透過 docker-compose 啟動，環境變數會被注入，這裡的 load_dotenv 可能不是絕對必要。
    # 但為了本地直接執行 `flask` 命令的方便性，可以保留。
    # dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    # load_dotenv(dotenv_path=dotenv_path)
    # 更簡單的方式是假設 .env 在當前工作目錄或上層目錄，load_dotenv() 會嘗試尋找。
    load_dotenv()  # 會嘗試尋找 .env

    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')  # 從環境變數讀取，預設 'default'

    app = Flask(__name__, instance_relative_config=True)

    # 1. 載入設定
    try:
        app.config.from_object(config_by_name[config_name])
        print(f" * Loading configuration: '{config_name}'")  # 除錯用
    except KeyError:
        print(f" * ERROR: Invalid FLASK_CONFIG '{config_name}'. Using 'default' config.")
        app.config.from_object(config_by_name['default'])

    # (可選) 嘗試從 instance/config.py 覆蓋設定 (如果 instance 資料夾存在且有 config.py)
    # app.config.from_pyfile('config.py', silent=True) # 'silent=True' 表示如果檔案不存在則不報錯

    # 檢查 DATABASE_URL 是否成功載入 (非常重要)
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        print(
            " * FATAL ERROR: SQLALCHEMY_DATABASE_URI is not set. Please check your environment variables (.env) or config files.")
        # 可以選擇在這裡拋出錯誤或退出
        # raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set!")

    # 2. 初始化擴充套件
    db.init_app(app)
    migrate.init_app(app, db)

    # 設定 CORS
    allowed_origins_str = os.environ.get('CORS_ALLOWED_ORIGINS')  # 預設允許本地 Vue
    allowed_origins_list = [origin.strip() for origin in allowed_origins_str.split(',')]
    if "*" in allowed_origins_str:
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    else:
        cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins_list}})
    print(f" * CORS configured for origins: {allowed_origins_list}")

    # 3. 註冊藍圖 (Blueprints)
    # 從 app.api 套件的 __init__.py 中匯入 bp 實例 (我們之前將其命名為 bp，但叫 api_bp 可能更清晰)
    from .api import bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    print(" * Registered API blueprint at /api")  # 除錯用

    # 如果您未來有其他藍圖，例如管理後台等，也可以在這裡註冊
    # from .admin import bp as admin_blueprint
    # app.register_blueprint(admin_blueprint, url_prefix='/admin')

    # 4. (可選) 註冊全域錯誤處理器 (如果需要回傳 JSON 格式的錯誤)
    # def handle_validation_error(e):
    #     return jsonify(error=str(e)), 400
    # app.register_error_handler(ValidationError, handle_validation_error) # 假設您有自訂的 ValidationError

    # 5. (可選) 註冊上下文處理器
    @app.context_processor
    def inject_current_time():
        # 這個主要用於 Jinja2 模板，在純 API 後端中可能用處不大，除非您仍有少量管理頁面
        return {'now': datetime.utcnow()}

    # 6. (可選) Shell 上下文處理器，方便 `flask shell` 操作
    @app.shell_context_processor
    def make_shell_context():
        from .models.team_member import TeamMember
        from .models.team_event import TeamEvent
        from .models.match_record import MatchRecord
        from .models.player_stats import PlayerStats
        # 匯入所有模型和 db 實例
        return {
            'db': db,
            'TeamMember': TeamMember,
            'TeamEvent': TeamEvent,
            'MatchRecord': MatchRecord,
            'PlayerMatchStats': PlayerStats
            # 您也可以將 app 實例加入，方便測試
            # 'app': app
        }

    # 7. (重要) 確保 SQLAlchemy 能在應用程式上下文中找到所有模型定義
    #    這有助於 Alembic (Flask-Migrate) 正確偵測模型變更。
    #    通常，在藍圖的 routes.py 中匯入模型就足夠了。
    #    或者，在 shell context processor 中匯入也可以。
    #    如果遇到遷移問題，可以明確地在這裡匯入一次所有模型所在的模組：
    with app.app_context():
        # 匯入模型模組以確保它們被 SQLAlchemy 註冊
        from .models.team_member import TeamMember
        from .models.player_stats import PlayerStats
        from .models.match_record import MatchRecord
        # print(" * Models loaded within app_context for SQLAlchemy registration.") # 除錯用

    print(f" * Flask App '{app.name}' created with config '{config_name}'")
    print(f" * SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")  # 除錯用

    return app