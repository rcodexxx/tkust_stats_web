# backend/app/commands/user_management.py

import os

from flask import current_app
from flask.cli import with_appcontext

from ..extensions import db
from ..models.enums import UserRoleEnum  # 假設新 User 預設為 PLAYER
from ..models.member import Member
from ..models.user import User

# 從環境變數獲取預設初始密碼，如果未設定則使用一個備用值
# 這個密碼應該與您 seeding 或快速註冊時使用的初始密碼邏輯一致
DEFAULT_INITIAL_PASSWORD_FOR_EXISTING_MEMBERS = os.environ.get(
    "EXISTING_MEMBER_DEFAULT_PASSWORD", "ChangemeNow!"  # 務必提醒使用者更改此密碼
)


@current_app.cli.command("users:init")
@with_appcontext
def create_users_for_existing_members():
    """
    為那些還沒有 User 帳號的 TeamMember，
    使用其 student_id 作為 username 來創建 User 帳號。
    """
    current_app.logger.info(
        "Starting to create User accounts for TeamMembers without one..."
    )

    # 1. 查詢所有還沒有 user_id (即沒有關聯 User 帳號) 的 TeamMember
    members_without_users = Member.query.filter(Member.user_id.is_(None)).all()

    if not members_without_users:
        current_app.logger.info(
            "No TeamMembers found without an associated User account."
        )
        return

    created_users_count = 0
    skipped_members_count = 0

    for member in members_without_users:
        current_app.logger.info(
            f"Processing TeamMember: {member.name} (ID: {member.id})"
        )

        # 2. 使用 student_id 作為 username
        potential_username = member.student_id

        if not potential_username or not potential_username.strip():
            current_app.logger.warning(
                f"  Skipping {member.name}: student_id is missing or empty. Cannot create username."
            )
            skipped_members_count += 1
            continue

        # 3. 檢查 username (student_id) 是否已被其他 User 使用
        existing_user = User.query.filter_by(username=potential_username).first()
        if existing_user:
            current_app.logger.warning(
                f"  Skipping {member.name}: Username '{potential_username}' (from student_id) "
                f"is already taken by User ID {existing_user.id}. "
                f"Consider linking existing User or choosing a different username strategy."
            )
            skipped_members_count += 1
            continue
            # 或者，如果 existing_user 沒有關聯的 team_member_profile，您可以嘗試關聯它：
            # if existing_user.team_member_profile is None:
            #     member.user_account = existing_user
            #     db.session.add(member) # 更新 member 的 user_id
            #     current_app.logger.info(f"  Linked existing User '{potential_username}' to TeamMember {member.name}")
            # else:
            #     # Username 已被其他 User 使用，且該 User 已關聯其他 TeamMember
            #     skipped_members_count += 1
            # continue

        # 4. 創建新的 User 實例
        try:
            new_user = User(
                username=potential_username,
                role=UserRoleEnum.PLAYER,  # 新帳號預設為 PLAYER，您可以按需調整
                is_active=True,  # 預設帳號啟用
                # email 欄位是 nullable=True，所以可以不提供
            )
            new_user.set_password(DEFAULT_INITIAL_PASSWORD_FOR_EXISTING_MEMBERS)

            # 5. 將 User 與 TeamMember 關聯
            member.user_account = new_user  # 這會自動設定 member.user_id
            # SQLAlchemy 會處理 User 的添加，因為 TeamMember 中設定了關聯

            # 或者先 add user, flush, 再設定 member.user_id
            # db.session.add(new_user)
            # db.session.flush() # 確保 new_user.id 可用
            # member.user_id = new_user.id

            db.session.add(
                member
            )  # 即使只是更新了 member.user_id，也 add 一下確保 session 追蹤
            # 實際上，如果 new_user 和 member 都已正確關聯，只需要 add 其中一個 (通常是 "多" 的一方，或者父物件如果設定了 cascade)
            # 由於 User.team_member_profile 有 cascade，add(new_user) 也可能帶動 member.
            # 但為清晰，這裡 add(member) 包含已更新的 user_account。
            # 為了確保 User 也被持久化，更安全的是:
            # db.session.add_all([new_user, member])

            created_users_count += 1
            current_app.logger.info(
                f"  Successfully prepared User account '{potential_username}' for TeamMember '{member.name}'. Initial pwd: '{DEFAULT_INITIAL_PASSWORD_FOR_EXISTING_MEMBERS}'"
            )

        except Exception as e_inst:
            current_app.logger.error(
                f"  Error creating User/linking for TeamMember {member.name}: {str(e_inst)}",
                exc_info=True,
            )
            skipped_members_count += 1
            db.session.rollback()  # 回滾這個成員的操作，繼續下一個
            continue  # 確保即使單個失敗，也不影響其他成員的處理

    if created_users_count > 0:
        try:
            db.session.commit()
            current_app.logger.info(
                f"Successfully created and linked {created_users_count} User accounts."
            )
        except Exception as e_commit:
            db.session.rollback()
            current_app.logger.error(
                f"Error committing User account creations: {str(e_commit)}",
                exc_info=True,
            )
    else:
        current_app.logger.info("No new User accounts were created.")

    if skipped_members_count > 0:
        current_app.logger.warning(f"{skipped_members_count} TeamMembers were skipped.")

    current_app.logger.info("User creation process from existing members finished.")
