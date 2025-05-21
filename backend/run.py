# backend/run.py
import os
from app import create_app, db
from app.models.team_member import TeamMember
from app.models.organization import Organization
from app.models.racket import Racket
from app.models.enums import GenderEnum, PositionEnum
import click # Flask CLI 基於 Click

# 從環境變數讀取設定名稱，預設為 'development'
# FLASK_CONFIG 會在 .env 或 docker-compose.yml 中設定
config_name = os.environ.get('FLASK_CONFIG', 'development') 
app = create_app(config_name) # 確保 create_app 能接受 config_name


@app.cli.command("seed-db")
def seed_db_command():
    """填充資料庫的種子數據"""
    print("Seeding database...")
    try:
        # 清除現有數據 (可選，小心使用)
        # TeamMember.query.delete()

        members_data = [
            {'name': '陳冠宇', 'score': 0, 'student_id': '611460162', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            {'name': '鍾楊鎧', 'score': 0, 'student_id': 'T002', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            {'name': '山嵜一花', 'score': 100, 'student_id': 'F001', 'gender': GenderEnum.MALE, 'position': PositionEnum.VERSATILE},
        ]

        for member_info in members_data:
            if not TeamMember.query.filter_by(student_id=member_info['student_id']).first():
                member = TeamMember(
                    name=member_info['name'],
                    score=member_info['score'],
                    student_id=member_info['student_id'],
                    gender=member_info['gender'],
                    position=member_info['position'],
                    is_active=True
                )
                db.session.add(member)

        db.session.commit()
        print("Database seeded!")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding database: {e}")

if __name__ == '__main__':
    # 本地直接 python run.py 執行時 (非 Docker Gunicorn)，會使用 Flask 開發伺服器
    # Docker 環境中，Gunicorn 會直接使用上面創建的 app 實例
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)