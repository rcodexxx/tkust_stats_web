# backend/app/commands/seed.py

from flask import current_app
from flask.cli import with_appcontext

from ..extensions import db
from ..models.enums import GenderEnum, PositionEnum, UserRoleEnum
from ..models.member import Member
from ..models.organization import Organization
from ..models.user import User


@current_app.cli.command("seed-db")  # 或者您之前用的 "seed-team"
@with_appcontext
def seed_db_command():
    """Seeds the database with new team members if they don't already exist (based on student_id)."""

    current_app.logger.info(
        "Starting database seeding process (add new members only)..."
    )

    try:

        Member.query.delete()

        User.query.delete()

        Organization.query.delete()  # 先刪除沒有外鍵依賴的或被依賴最少的

        db.session.commit()

        current_app.logger.info("Old data (Organizations, Users, Members) deleted.")

        org1 = Organization(name="淡江大學網球校隊", city="新北市")

        db.session.add(org1)

        db.session.commit()

        members_data = [
            {
                "user": {
                    "username": "0976060398",  # 手機號作為 username
                    "password": "0976060398",
                    # "email": "admin_yu@example.com",
                    "role": UserRoleEnum.ADMIN,
                },
                "member": {
                    "name": "陳冠宇",
                    "display_name": "-_-yu",
                    "student_id": "611460162",  # 學號
                    "gender": GenderEnum.MALE,
                    "position": PositionEnum.BACK,
                    "organization_id": "NULL",
                    "mu": 25.0,
                    "sigma": round(25.0 / 3.0, 4),
                },
            },
        ]

        created_count = 0

        passwords_info = []  # 用於記錄生成的密碼

        for item_data in members_data:

            user_info = item_data.get("user", {})

            member_info = item_data.get("member", {})

            # 檢查 User 是否已存在 (基於 username)

            existing_user = User.query.filter_by(
                username=user_info.get("username")
            ).first()

            if existing_user:

                current_app.logger.info(
                    f"User with username {user_info.get('username')} already exists. Skipping."
                )

                continue

            # 檢查 Member 的 student_id 是否已存在 (如果 student_id 是唯一的)

            if member_info.get("student_id"):

                existing_member_sid = Member.query.filter_by(
                    student_id=member_info.get("student_id")
                ).first()

                if existing_member_sid:

                    current_app.logger.info(
                        f"Member with student_id {member_info.get('student_id')} already exists. Skipping user {user_info.get('username')}."
                    )

                    continue

            try:

                actual_password = user_info.get(
                    "password", user_info.get("username")
                )  # 預設手機號為密碼

                if not actual_password:  # 最後的防線，理論上 username 必填

                    actual_password = "password"  # 或者拋出錯誤

                new_user = User(
                    username=user_info["username"],
                    email=user_info.get("email"),
                    role=user_info.get("role", UserRoleEnum.ADMIN),  # 預設 PLAYER
                )

                new_user.set_password(actual_password)

                db.session.add(new_user)  # 先 add User

                # db.session.flush() # 可選，確保 new_user.id 可用

                new_member = Member(
                    name=member_info["name"],
                    display_name=member_info.get("display_name", member_info["name"]),
                    student_id=member_info.get("student_id"),
                    organization_id=member_info.get(
                        "organization_id"
                    ),  # <--- 使用 organization_id
                    gender=member_info.get("gender"),
                    position=member_info.get("position"),
                    mu=member_info.get(
                        "mu", Member.mu.default.arg if Member.mu.default else 25.0
                    ),
                    sigma=member_info.get(
                        "sigma",
                        (
                            Member.sigma.default.arg
                            if Member.sigma.default
                            else round(25.0 / 3.0, 4)
                        ),
                    ),
                    is_active=member_info.get("is_active", True),  # Member.is_active
                    user_account=new_user,  # 建立關聯
                )

                db.session.add(new_member)

                db.session.commit()  # 為每個成員提交一次，或在循環外統一提交

                created_count += 1

                passwords_info.append(
                    f"User '{new_user.username}': Initial password is '{actual_password}'"
                )

                current_app.logger.info(
                    f"Added User: {new_user.username}, Member: {new_member.name}"
                )

            except Exception as e_inst:

                db.session.rollback()

                current_app.logger.error(
                    f"Error creating user/member for {user_info.get('username')}: {str(e_inst)}",
                    exc_info=True,
                )

        if created_count > 0:

            current_app.logger.info(
                f"Successfully seeded {created_count} new user/member entries."
            )

            for p_info in passwords_info:

                current_app.logger.info(p_info)

            current_app.logger.warning(
                "IMPORTANT: Please ensure users change these initial passwords upon first login!"
            )

        else:

            current_app.logger.info(
                "No new entries were seeded (they might already exist)."
            )

    except Exception as e:

        db.session.rollback()

        current_app.logger.error(
            f"Critical error during database seeding: {str(e)}", exc_info=True
        )
