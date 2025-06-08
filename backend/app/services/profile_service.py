# backend/app/services/profile_service.py
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User
from ..tools.exceptions import UserNotFoundError, UserAlreadyExistsError, AppException


class ProfileService:
    @staticmethod
    def get_user_profile(user_id: int) -> User:
        """
        根據使用者 ID 獲取完整的使用者物件及其關聯的 Member profile。
        如果找不到使用者，則拋出 UserNotFoundError。
        """
        user = User.query.options(db.joinedload(User.member_profile)).get(user_id)
        if not user or not user.is_active:
            raise UserNotFoundError("找不到使用者或帳號已被停用。")
        return user

    @staticmethod
    def update_user_profile(user_id: int, data: dict) -> User:
        """
        更新使用者的個人資料。
        'data' 是經過 ProfileUpdateSchema 驗證後的數據。
        """
        user_to_update = ProfileService.get_user_profile(user_id)  # 重用 get 方法，同時檢查存在性
        member_to_update = user_to_update.member_profile

        # --- 更新 User 模型的欄位 ---
        if "email" in data:
            new_email = data["email"]
            # 檢查 email 是否已被其他使用者使用
            if new_email and User.query.filter(User.email == new_email, User.id != user_id).first():
                raise UserAlreadyExistsError(f"電子郵件 '{new_email}' 已被其他帳號使用。")
            user_to_update.email = new_email

        if "display_name" in data:
            user_to_update.display_name = data["display_name"]

        # --- 更新 Member 模型的欄位 ---
        if member_to_update:
            # 遍歷 data 中的鍵，如果 Member 模型有對應的屬性，則更新
            for field in [
                "name",
                "student_id",
                "gender",
                "position",
                "organization_id",
            ]:  # 以及您在 Schema 中允許更新的其他欄位
                if field in data:
                    setattr(member_to_update, field, data[field])
        elif any(key in data for key in ["gender", "position", "organization_id"]):
            # 如果使用者嘗試更新 Member 欄位，但沒有 Member profile，可以選擇報錯或忽略
            # 這裡我們選擇忽略，只更新 User 部分
            pass

        try:
            db.session.commit()
            return user_to_update
        except IntegrityError as e:
            db.session.rollback()
            raise AppException(f"資料庫錯誤，更新失敗: {e.orig}", status_code=409)
        except Exception as e:
            db.session.rollback()
            raise AppException(f"更新個人資料時發生未預期錯誤: {e}")
