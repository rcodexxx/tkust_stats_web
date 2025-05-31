# backend/app/commands/seed.py (或 run.py 中的 seed_db_command)

from flask import current_app
from flask.cli import with_appcontext

from ..extensions import db
from ..models.enums import GenderEnum, PositionEnum, UserRoleEnum
from ..models.member import Member
from ..models.user import User

INITIAL_PASSWORD = "password"


@current_app.cli.command("seed-db")  # 或者您之前用的 "seed-team"
@with_appcontext
def seed_db_command():
    """Seeds the database with new team members if they don't already exist (based on student_id)."""
    current_app.logger.info(
        "Starting database seeding process (add new members only)..."
    )

    Member.query.delete()
    User.query.delete()
    db.session.commit()
    current_app.logger.info("Old data deleted.")

    current_app.logger.info("Adding new User and TeamMember data...")
    try:
        members_data = [
            {
                "user": {
                    "username": "0976060398",
                    "email": "",
                    "role": UserRoleEnum.ADMIN,
                },
                "member": {
                    "name": "陳冠宇",
                    "display_name": "-_-yu",
                    "organization": "淡江大學",
                    "student_id": "611460162",
                    "gender": GenderEnum.MALE,
                    "position": PositionEnum.BACK,
                },
            },
            # {'name': '鍾楊鎧', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            # {'name': '白芳維', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            # {'name': '楊承恩', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.FRONT},
            # {'name': '簡宏洲', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.VERSATILE},
            # {'name': '曾彥綸', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            # {'name': '周俊瑋', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.BACK},
            # {'name': 'Angus', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.FRONT},
            # {'name': '詹貴翔', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.FRONT},
            # {'name': '許朝凱', 'student_id': '', 'gender': GenderEnum.MALE, 'position': PositionEnum.FRONT},
            # {'name': '山嵜一花', 'student_id': '410865025', 'gender': GenderEnum.FEMALE,
            #  'position': PositionEnum.VERSATILE},
            # {'name': '黃宇微', 'student_id': '411530636', 'gender': GenderEnum.FEMALE, 'position': PositionEnum.FRONT},
            # {'name': '徐欣妘', 'student_id': '', 'gender': GenderEnum.FEMALE, 'position': PositionEnum.FRONT},
            # {'name': '邱筣穎', 'student_id': '', 'gender': GenderEnum.FEMALE, 'position': PositionEnum.BACK},
            # {'name': '吳柏萱', 'student_id': '', 'gender': GenderEnum.FEMALE, 'position': PositionEnum.BACK},
            # {'name': '胡育慈', 'student_id': '', 'gender': GenderEnum.FEMALE, 'position': PositionEnum.FRONT},
        ]

        created_count = 0
        for item in members_data:
            if "user" in item and "member" in item:
                user_data = item["user"]
                member_data = item["member"]

                try:
                    new_user = User(
                        username=user_data["username"],
                        email=user_data["email"],
                        role=(
                            user_data["role"]
                            if user_data["role"] == UserRoleEnum.ADMIN
                            else UserRoleEnum.MEMBER
                        ),
                    )
                    new_user.set_password(user_data["username"])

                    new_member = Member(
                        name=member_data["name"],
                        display_name=member_data.get("display_name"),
                        student_id=(
                            member_data.get("student_id")
                            if member_data.get("student_id")
                            else None
                        ),
                        organization=member_data.get("organization"),
                        gender=member_data.get("gender"),
                        position=member_data.get("position"),
                        mu=member_data.get("mu", 25.0),
                        sigma=member_data.get("sigma", round(25.0 / 3.0, 4)),
                        is_active=True,
                        user_account=new_user,
                    )
                    db.session.add(new_member)
                    created_count += 1
                    current_app.logger.info(
                        f"Added User: {new_user.username}, Member: {new_member.name}"
                    )
                except Exception as e_inst:
                    db.session.rollback()
                    current_app.logger.error(
                        f"Error creating user/member for {user_data.get('username')}: {str(e_inst)}",
                        exc_info=True,
                    )

        if created_count > 0:
            db.session.commit()
            current_app.logger.info(
                f"Successfully seeded {created_count} new user/member entries."
            )
        else:
            current_app.logger.info("No new entries were seeded.")
        current_app.logger.info(
            f"Default password for seeded users (if any): '{INITIAL_PASSWORD}'"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Critical error during database seeding: {str(e)}", exc_info=True
        )
