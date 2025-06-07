# backend/app/commands/seed.py

import click
from flask.cli import with_appcontext

from ..extensions import db
from ..models import User, Member
from ..models.enums.user_enums import UserRoleEnum  # 導入您的 UserRoleEnum


@click.command("init-admin")
@with_appcontext
def init_admin_command():
    """
    建立一個初始的管理員帳號。
    此指令會檢查帳號是否已存在，若已存在則會跳過，確保冪等性。
    建議透過環境變數來設定憑證。
    """
    # 1. 從環境變數獲取管理員憑證，若無則使用安全的預設值
    # 生產環境中，強烈建議透過環境變數設定所有這些值
    # admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    # admin_email = os.environ.get("ADMIN_EMAIL", f"{admin_username}@example.com")
    # admin_password = os.environ.get("ADMIN_PASSWORD")
    # admin_name = os.environ.get("ADMIN_NAME", "網站管理員")
    admin_username = "0976060398"
    admin_password = admin_username
    admin_name = "-_-Yu"

    # 2. 檢查密碼是否已設定 (非常重要)
    if not admin_password:
        click.echo(click.style("錯誤：ADMIN_PASSWORD 環境變數未設定。請設定管理員密碼後再執行。", fg="red"))
        # 若希望在指令中互動式地設定密碼，可以取消以下註解：
        # admin_password = click.prompt("請輸入管理員密碼", type=str, hide_input=True, confirmation_prompt=True)
        return

    # 3. 檢查管理員帳號是否已存在 (冪等性檢查)
    if User.query.filter_by(username=admin_username).first():
        click.echo(click.style(f"使用者名稱為 '{admin_username}' 的管理員已存在，跳過建立程序。", fg="yellow"))
        return
    # if User.query.filter_by(email=admin_email).first():
    #     click.echo(click.style(f"Email 為 '{admin_email}' 的管理員已存在，跳過建立程序。", fg="yellow"))
    #     return
    #
    # click.echo(f"正在建立管理員帳號: Username={admin_username}, Email={admin_email}")

    try:
        # 4. 創建 User 和 Member 物件
        user_profile = User(
            username=admin_username,
            # email=admin_email,
            role=UserRoleEnum.ADMIN,  # 明確設定角色為管理員
            is_active=True,  # 管理員帳號預設為啟用
            display_name=admin_name,  # 管理員的顯示名稱
        )
        user_profile.set_password(admin_password)  # 使用 User 模型中的 set_password 方法來雜湊密碼
        db.session.add(user_profile)

        # 根據您的模型設計，每個 User 都需要一個關聯的 Member profile
        admin_member_profile = Member(
            user_profile=user_profile,  # 直接關聯 User 物件，SQLAlchemy 會處理 user_id
            name=admin_name,
        )
        db.session.add(admin_member_profile)

        # 5. 提交到資料庫
        db.session.commit()
        click.echo(click.style(f"✅ 管理員帳號 '{admin_username}' 及對應的 Member profile 已成功建立！", fg="green"))

    except Exception as e:
        db.session.rollback()  # 如果發生任何錯誤，回滾事務
        click.echo(click.style(f"❌ 建立管理員帳號失敗：{str(e)}", fg="red"))
