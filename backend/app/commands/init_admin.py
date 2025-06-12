# backend/app/commands/init_admin.py

import os

import click
from flask.cli import with_appcontext

from ..extensions import db
from ..models import Member, User
from ..models.enums.user_enums import UserRoleEnum


@click.command("init-admin")
@click.option('--username', prompt='管理員帳號', help='管理員登入帳號')
@click.option('--email', prompt='管理員 Email (可選)', default='', help='管理員電子郵件')
@click.option('--name', prompt='管理員姓名', help='管理員顯示名稱')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='管理員密碼')
@click.option('--force', is_flag=True, help='強制覆蓋現有管理員')
@with_appcontext
def init_admin_command(username, email, name, password, force):
    """
    初始化管理員帳號。

    建立一個具有管理員權限的使用者帳號和對應的 Member 資料。
    支援互動式輸入或環境變數設定。
    """

    click.echo(click.style("🚀 開始初始化管理員帳號...", fg="blue"))

    # 允許從環境變數覆蓋設定
    username = username or os.environ.get("ADMIN_USERNAME")
    email = email or os.environ.get("ADMIN_EMAIL") or None
    name = name or os.environ.get("ADMIN_NAME")
    password = password or os.environ.get("ADMIN_PASSWORD")

    # 驗證必要欄位
    if not username:
        click.echo(click.style("❌ 錯誤：管理員帳號不能為空", fg="red"))
        return

    if not name:
        click.echo(click.style("❌ 錯誤：管理員姓名不能為空", fg="red"))
        return

    if not password:
        click.echo(click.style("❌ 錯誤：管理員密碼不能為空", fg="red"))
        return

    # 密碼強度檢查
    if len(password) < 6:
        click.echo(click.style("❌ 錯誤：密碼長度至少需要 6 個字元", fg="red"))
        return

    # 處理空的 email
    if email == '':
        email = None

    try:
        # 檢查是否已存在管理員
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            if not force:
                click.echo(click.style(f"⚠️  警告：使用者名稱 '{username}' 已存在", fg="yellow"))
                if click.confirm("是否要覆蓋現有的使用者？"):
                    force = True
                else:
                    click.echo("操作已取消")
                    return

            if force:
                click.echo(click.style(f"🗑️  刪除現有使用者 '{username}'...", fg="yellow"))
                # 刪除關聯的 Member（如果存在）
                if existing_user.member_profile:
                    db.session.delete(existing_user.member_profile)
                db.session.delete(existing_user)
                db.session.commit()
                click.echo(click.style("✅ 現有使用者已刪除", fg="green"))

        # 檢查 email 是否已存在（如果提供了 email）
        if email:
            existing_email_user = User.query.filter_by(email=email).first()
            if existing_email_user and existing_email_user.username != username:
                click.echo(click.style(f"❌ 錯誤：Email '{email}' 已被其他使用者使用", fg="red"))
                return

        # 創建管理員使用者
        click.echo(click.style("👤 創建管理員使用者...", fg="blue"))
        admin_user = User(
            username=username,
            email=email,
            role=UserRoleEnum.ADMIN,
            display_name=name,
            is_active=True
        )
        admin_user.set_password(password)
        db.session.add(admin_user)

        # 創建對應的 Member 資料
        click.echo(click.style("👥 創建 Member 資料...", fg="blue"))
        admin_member = Member(
            user=admin_user,
            name=name,
            # 其他欄位使用預設值
        )
        db.session.add(admin_member)

        # 提交到資料庫
        db.session.commit()

        # 成功訊息
        click.echo(click.style("✨ 管理員帳號創建成功！", fg="green", bold=True))
        click.echo("📋 帳號資訊:")
        click.echo(f"   使用者名稱: {username}")
        click.echo(f"   Email: {email or '未設定'}")
        click.echo(f"   姓名: {name}")
        click.echo("   角色: 管理員")
        click.echo("   狀態: 啟用")

        # 安全提醒
        click.echo(click.style("\n🔒 安全提醒:", fg="yellow", bold=True))
        click.echo("   • 請立即登入並更改密碼")
        click.echo("   • 請確保帳號資訊安全")
        click.echo("   • 建議設定強密碼和雙因子認證")

    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"❌ 創建管理員帳號失敗: {str(e)}", fg="red"))
        click.echo(click.style("🔄 資料庫已回滾", fg="yellow"))


@click.command("list-admins")
@with_appcontext
def list_admins_command():
    """列出所有管理員帳號"""

    click.echo(click.style("👥 管理員帳號列表:", fg="blue", bold=True))

    admins = User.query.filter_by(role=UserRoleEnum.ADMIN).all()

    if not admins:
        click.echo(click.style("❌ 未找到任何管理員帳號", fg="red"))
        return

    for i, admin in enumerate(admins, 1):
        status_color = "green" if admin.is_active else "red"
        status_text = "啟用" if admin.is_active else "停用"

        click.echo(f"\n{i}. {admin.display_name or admin.username}")
        click.echo(f"   📧 Email: {admin.email or '未設定'}")
        click.echo(f"   👤 使用者名稱: {admin.username}")
        click.echo(f"   📅 創建時間: {admin.created_at}")
        click.echo(f"   🔄 更新時間: {admin.updated_at}")
        click.echo(f"   📊 狀態: {click.style(status_text, fg=status_color)}")


@click.command("reset-admin-password")
@click.option('--username', prompt='管理員帳號', help='要重設密碼的管理員帳號')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='新密碼')
@with_appcontext
def reset_admin_password_command(username, password):
    """重設管理員密碼"""

    click.echo(click.style(f"🔑 重設管理員 '{username}' 的密碼...", fg="blue"))

    # 密碼強度檢查
    if len(password) < 6:
        click.echo(click.style("❌ 錯誤：密碼長度至少需要 6 個字元", fg="red"))
        return

    try:
        # 查找管理員
        admin = User.query.filter_by(username=username, role=UserRoleEnum.ADMIN).first()

        if not admin:
            click.echo(click.style(f"❌ 錯誤：找不到管理員帳號 '{username}'", fg="red"))
            return

        # 更新密碼
        admin.set_password(password)
        db.session.commit()

        click.echo(click.style(f"✅ 管理員 '{username}' 的密碼已成功重設", fg="green"))
        click.echo(click.style("🔒 請立即使用新密碼登入", fg="yellow"))

    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"❌ 重設密碼失敗: {str(e)}", fg="red"))
