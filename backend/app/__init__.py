# app/__init__.py
import os
from flask import Flask
from .config import config_by_name
from .extensions import db, migrate
from flask_cors import CORS # <--- 匯入 CORS

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # 初始化擴充套件
    db.init_app(app)
    migrate.init_app(app, db)

    # 設定 CORS
    # 開發時允許所有來源，或指定 Vue 開發伺服器的來源 (通常是 http://localhost:5173 或 http://localhost:8080 for Vue CLI)
    # 生產環境應指定您 Vue 前端部署後的實際網域
    origins = os.environ.get('CORS_ALLOWED_ORIGINS', "http://localhost:5173,http://127.0.0.1:5173")
    if origins == "*":
         CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        CORS(app, resources={r"/api/*": {"origins": origins.split(',')}})


    # 註冊 API 藍圖
    # 範例：將所有 API 路由放在一個名為 'api' 的藍圖中，前綴為 /api
    from .api.routes import bp as api_bp # 假設您將 API 路由整合到 app/api/routes.py
    app.register_blueprint(api_bp, url_prefix='/api')

    # 移除或註解掉之前渲染 HTML 的 main 和 match 藍圖的註冊
    # from .main import bp as main_bp
    # app.register_blueprint(main_bp)
    # from .match import bp as match_bp
    # app.register_blueprint(match_bp, url_prefix='/match')

    @app.shell_context_processor
    def make_shell_context():
        # ... (保持不變)
        from app.models.team_member import TeamMember # etc.
        return {'db': db, 'TeamMember': TeamMember} # Add other models

    with app.app_context():
        from app.models import team_member, team_event, match_record, player_match_stats # 確保模型被載入

    return app