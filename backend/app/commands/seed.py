from flask import current_app # <--- 匯入 current_app
from flask.cli import with_appcontext
import click
from ..models import *
from ..extensions import db, migrate, cors  # 假設您在 extensions.py 中也定義了 cors = CORS()


@current_app.cli.command("seed-db")
@with_appcontext
def seed_db_command():
    """填充資料庫的種子數據"""
    print("Seeding database...")
    try:
        # 清除現有數據 (可選，小心使用)
        # TeamMember.query.delete()

        members_data = [
            {'name': '陳冠宇', 'student_id': '611460162', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            {'name': '鍾楊鎧', 'student_id': 'T002', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            {'name': '山嵜一花', 'student_id': '410865025', 'gender': GenderEnum.FEMALE, 'position': PositionEnum.VERSATILE},
            {'name': '黃宇微', 'student_id': '411530636', 'gender': GenderEnum.FEMALE, 'position': PositionEnum.FRONT},
        ]

        for member_info in members_data:
            if not TeamMember.query.filter_by(student_id=member_info['student_id']).first():
                member = TeamMember(
                    name=member_info['name'],
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

