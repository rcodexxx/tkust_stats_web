# backend/run.py
import os

from app import create_app, db

# 從環境變數讀取設定名稱，預設為 'development'
# FLASK_CONFIG 會在 .env 或 docker-compose.yml 中設定
config_name = os.environ.get("FLASK_CONFIG", "development")
app = create_app(config_name)  # 確保 create_app 能接受 config_name

if __name__ == "__main__":
    # 本地直接 python run.py 執行時 (非 Docker Gunicorn)，會使用 Flask 開發伺服器
    # Docker 環境中，Gunicorn 會直接使用上面創建的 app 實例
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
