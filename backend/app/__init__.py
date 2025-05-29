# backend/app/__init__.py

import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import config_by_name
from .extensions import cors, db, migrate


def create_app(config_name=None):
    """
    應用程式工廠函數。
    """
    load_dotenv()  # 會嘗試尋找 .env
    jwt = JWTManager()

    if config_name is None:
        config_name = os.environ.get(
            "FLASK_CONFIG", "default"
        )  # 從環境變數讀取，預設 'default'

    app = Flask(__name__, instance_relative_config=True)

    # 1. 載入設定
    try:
        app.config.from_object(config_by_name[config_name])
        print(f" * Loading configuration: '{config_name}'")  # 除錯用
    except KeyError:
        print(
            f" * ERROR: Invalid FLASK_CONFIG '{config_name}'. Using 'default' config."
        )
        app.config.from_object(config_by_name["default"])

    # 設定 Flask logger，使其輸出更詳細的資訊到控制台
    if (
        not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    ):  # 避免在重載時重複設定
        app.logger.setLevel(logging.DEBUG)  # 設定日誌級別為 DEBUG
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        # 可以加入更詳細的 formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        if not app.logger.handlers:  # 避免重複加入 handler
            app.logger.addHandler(handler)
        app.logger.info("Flask logger configured for DEBUG level.")

    # 檢查 DATABASE_URL 是否成功載入 (非常重要)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        print(
            " * FATAL ERROR: SQLALCHEMY_DATABASE_URI is not set. Please check your environment variables (.env) or config files."
        )

    # 2. 初始化擴充套件
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    jwt.init_app(app)

    # 設定 CORS
    allowed_origins_str = os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    allowed_origins_list = [origin.strip() for origin in allowed_origins_str.split(",")]

    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins_list}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )
    app.logger.info(f"CORS configured for API. Origins: {allowed_origins_list}")

    @app.before_request
    def log_request_info():
        app.logger.debug("Request Headers: %s", request.headers)
        app.logger.debug("Request Method: %s", request.method)
        app.logger.debug("Request Path: %s", request.path)
        app.logger.debug("Request Data: %s", request.get_data(as_text=True))

    @app.after_request
    def log_response_info(response):
        app.logger.debug("Response Status: %s", response.status)
        app.logger.debug("Response Headers: %s", response.headers)
        return response

    # 3. 註冊藍圖 (Blueprints)
    from .api import bp as api_blueprint

    app.register_blueprint(api_blueprint, url_prefix="/api")
    print(" * Registered API blueprint at /api")  # 除錯用

    # 4. (可選) 註冊全域錯誤處理器 (如果需要回傳 JSON 格式的錯誤)
    # def handle_validation_error(e):
    #     return jsonify(error=str(e)), 400
    # app.register_error_handler(ValidationError, handle_validation_error) # 假設您有自訂的 ValidationError
    with app.app_context():  # 將命令的匯入和註冊放在 app_context 內確保 current_app 可用
        from .commands import seed  # 假設您的檔案是 app/commands/seed.py

    # 5. (可選) 註冊上下文處理器
    @app.context_processor
    def inject_current_time():
        # 這個主要用於 Jinja2 模板，在純 API 後端中可能用處不大，除非您仍有少量管理頁面
        return {"now": datetime.utcnow()}

    # 6. (可選) Shell 上下文處理器，方便 `flask shell` 操作
    @app.shell_context_processor
    def make_shell_context():
        from .models.match_record import MatchRecord
        from .models.member import TeamMember
        from .models.player_stats import PlayerStats

        # 匯入所有模型和 db 實例
        return {
            "db": db,
            "TeamMember": TeamMember,
            "MatchRecord": MatchRecord,
            "PlayerStats": PlayerStats,
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
        from .models.match_record import MatchRecord
        from .models.member import TeamMember
        from .models.player_stats import PlayerStats

        # print(" * Models loaded within app_context for SQLAlchemy registration.") # 除錯用

    print(f" * Flask App '{app.name}' created with config '{config_name}'")
    print(
        f" * SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}"
    )  # 除錯用

    return app
