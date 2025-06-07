# backend/app/commands/seed.py

import click
from flask.cli import with_appcontext

from ..extensions import db
from ..models.enums import UserRoleEnum
from ..models.member import Member
from ..models.user import User


@click.command("init-admin")
@with_appcontext
def init_admin_command():
    """Seeds the database with new team members if they don't already exist (based on student_id)."""

    username = "0912345678"

    try:
        new_admin_user = User(
            username=username,
            role=UserRoleEnum.ADMIN,
            is_active=True,
            display_name="-_-Yu",
        )
        new_admin_user.set_password(username)

        db.session.add(new_admin_user)

        # 3. Member profile
        admin_member_profile = Member(
            user=new_admin_user,
            name="陳冠宇",
        )
        db.session.add(admin_member_profile)

        # 4. 提交到資料庫
        db.session.commit()
        click.echo(click.style(f"✅ 管理員帳號 '{username}' 及對應的 Member profile 已成功建立！", fg="green"))

    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"❌ 建立管理員帳號失敗：{str(e)}", fg="red"))
