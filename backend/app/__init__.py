# backend/app/__init__.py

import logging
import os
from datetime import datetime  # 保留，因為 inject_current_time 使用了它

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException

from .api import api_bp
from .commands import cli_commands_bp
from .config import config_by_name
from .extensions import cors, db, migrate


def create_app(config_name: str = None):
    """
    應用程式工廠函數 (Application Factory)。
    負責創建和配置 Flask 應用程式實例。
    """
    load_dotenv()  # 載入 .env 檔案中的環境變數
    jwt = JWTManager()  # 初始化 JWTManager

    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")

    app = Flask(__name__, instance_relative_config=True)

    # 1. 載入應用程式設定
    try:
        app.config.from_object(config_by_name[config_name])
        app.logger.info(f"Loading configuration: '{config_name}'")
    except KeyError:
        app.logger.warning(f"Invalid FLASK_CONFIG '{config_name}'. Using 'default' config.")
        app.config.from_object(config_by_name["default"])

    # 2. 設定 Logger
    # 避免在 Flask 開發伺服器重載時重複設定 logger
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"  # 更詳細的 formatter
        )
        stream_handler.setFormatter(formatter)
        if not app.logger.handlers:  # 避免重複添加 handler
            app.logger.addHandler(stream_handler)
        app.logger.info("Flask logger configured for DEBUG level.")

    # 檢查資料庫 URI 是否設定
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.logger.critical("FATAL ERROR: SQLALCHEMY_DATABASE_URI is not set. Application cannot start.")
        import sys

        sys.exit(1)  # 資料庫未設定，應用程式無法正常運行，直接退出

    # 3. 初始化 Flask 擴充套件
    db.init_app(app)
    migrate.init_app(app, db)  # Flask-Migrate 用於資料庫遷移
    jwt.init_app(app)  # Flask-JWT-Extended 用於 JWT 認證

    # 設定 CORS (Cross-Origin Resource Sharing)
    allowed_origins_str = os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"  # 預設允許開發伺服器
    )
    allowed_origins_list = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]
    # 使用 extensions.py 中定義的 cors 實例來初始化
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": allowed_origins_list}},  # 只對 /api/ 路徑下的資源啟用 CORS
        supports_credentials=True,  # 允許跨域請求攜帶 cookies
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 允許的 HTTP 方法
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # 允許的請求頭
    )
    app.logger.info(f"CORS configured for API. Allowed Origins: {allowed_origins_list}")

    # 4. 註冊 Request Hook (請求鉤子)
    @app.before_request
    def log_request_info_hook():  # 避免與其他變數/函式重名，加上 _hook 後綴
        app.logger.debug(f"Path: {request.path}, Method: {request.method}")
        app.logger.debug(f"Headers: {request.headers}")
        if request.data:  # 只在有 data 時記錄
            app.logger.debug(f"Request Data: {request.get_data(as_text=True)}")

    @app.after_request
    def log_response_info_hook(response):  # 加上 _hook 後綴
        app.logger.debug(f"Response Status: {response.status}")
        app.logger.debug(f"Response Headers: {response.headers}")
        # 如果需要記錄 response body (注意可能很大，且影響效能)
        # if response.content_type == 'application/json':
        #     app.logger.debug(f"Response Data: {response.get_data(as_text=True)}")
        return response

    # 5. 註冊藍圖 (Blueprints)
    from .api import api_bp  # 確保在 create_app 內部導入，避免循環依賴問題

    app.register_blueprint(api_bp, url_prefix="/api")
    app.logger.info("Registered API blueprint at /api")

    app.register_blueprint(cli_commands_bp)  # 註冊 CLI 指令藍圖
    app.logger.info("Registered CLI commands blueprint.")

    # 6. 設定 JWT 錯誤處理回調
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        token_type = jwt_payload.get("type", "unknown")
        app.logger.info(f"{token_type.capitalize()} token has expired for sub: {jwt_payload.get('sub')}")
        return jsonify(error="token_expired", message=f"您的 {token_type} token 已過期，請重新整理或登入。"), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        app.logger.warning(f"Invalid token encountered: {error_string}")
        return jsonify(error="invalid_token", message="提供的認證 Token 無效。"), 422  # 422 Unprocessable Entity

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        app.logger.warning(f"Missing token: {error_string}")
        return jsonify(error="authorization_required", message="請求缺少有效的認證 Token。"), 401

    # 7. 註冊全域錯誤處理器
    @app.errorhandler(400)
    def handle_bad_request_error(error: HTTPException):  # 加入型別提示
        message = error.description or "請求無效。"
        app.logger.warning(f"Bad Request (400): {message} for {request.path}")
        return jsonify(error="bad_request", message=message), 400

    @app.errorhandler(404)
    def handle_not_found_error(error: HTTPException):
        app.logger.warning(f"Resource Not Found (404): {request.path} (Referrer: {request.referrer})")
        return jsonify(error="not_found", message="您請求的資源不存在。"), 404

    @app.errorhandler(405)
    def handle_method_not_allowed_error(error: HTTPException):
        app.logger.warning(f"Method Not Allowed (405) for {request.path}: {request.method}")
        return jsonify(error="method_not_allowed", message="請求的方法不被允許。"), 405

    @app.errorhandler(HTTPException)  # 通用 HTTP 錯誤處理
    def handle_http_exception(error: HTTPException):
        app.logger.warning(
            f"HTTP Exception Caught: Code={error.code}, Name={error.name}, Path={request.path}, Description={error.description}"
        )
        response_data = {
            "error": getattr(error, "name", "Http Exception").lower().replace(" ", "_"),
            "message": getattr(error, "description", "發生了一個 HTTP 錯誤。"),
        }
        status_code = getattr(error, "code", 500)
        return jsonify(response_data), status_code

    @app.errorhandler(Exception)  # 最後的防線，捕捉所有未處理的 Python 異常 (通常導致 500)
    def handle_generic_exception(error: Exception):
        app.logger.error(
            f"Unhandled Exception on path {request.path}: {str(error)}", exc_info=True
        )  # exc_info=True 會記錄堆疊追蹤
        if app.debug or os.environ.get("FLASK_ENV") == "development":
            error_message = f"伺服器內部錯誤: {str(error)}"
        else:
            error_message = "伺服器發生未預期的錯誤，我們已記錄此問題並將盡快處理。"
        return jsonify(error="internal_server_error", message=error_message), 500

    # 8. (可選) 註冊模板上下文處理器
    @app.context_processor
    def inject_current_time_to_templates():  # 稍微修改函式名，更清晰
        return {"current_time_utc": datetime.utcnow(), "current_time_local": datetime.now()}

    # 9. (可選) 設定 Shell 上下文處理器
    @app.shell_context_processor
    def make_shell_context():
        # 導入所有模型，方便在 flask shell 中使用
        from .models.user import User
        from .models.member import Member
        from .models.organization import Organization
        from .models.racket import Racket
        from .models.match import Match
        from .models.match_record import MatchRecord  # 您原有的比賽記錄模型
        from .models.player_stats import PlayerStats  # 詳細統計模型

        # 根據您最終的模型結構調整此處的導入
        models_to_import = {
            "db": db,
            "User": User,
            "Member": Member,
            "Organization": Organization,
            "Racket": Racket,
            "Match": Match,
            "MatchRecord": MatchRecord,  # 或 MatchResult
            "PlayerStats": PlayerStats,
            "app": app,  # 將 app 實例也加入，方便測試
        }
        return models_to_import

    # 10. (重要) 確保 SQLAlchemy 能找到所有模型定義 (Alembic 遷移用)
    with app.app_context():
        # 再次導入模型，確保在 Alembic 掃描時所有模型都被 SQLAlchemy 的 metadata 知曉
        # 這裡的導入順序通常不影響 Alembic，只要它們都被執行到即可
        # 建議與 shell_context_processor 中的模型列表保持一致
        app.logger.debug("Registering models with SQLAlchemy for Alembic...")
        from .models.user import User
        from .models.member import Member
        from .models.organization import Organization
        from .models.racket import Racket
        from .models.match import Match
        from .models.match_record import MatchRecord
        from .models.player_stats import PlayerStats

        # ... 確保所有您實際使用的模型都已導入 ...
        app.logger.debug("Models registered.")

    app.logger.info(f"Flask App '{app.name}' created successfully with config '{config_name}'.")
    app.logger.info(f"SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    return app
