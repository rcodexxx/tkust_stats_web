# backend/app/services/auth_service.py
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError  # 用於捕捉資料庫唯一性衝突

from ..extensions import db
from ..models.enums.user_enums import UserRoleEnum
from ..models.member import Member
from ..models.user import User
from ..tools.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserInactiveError,
    IncorrectPasswordError,
    PasswordPolicyError,
    UserNotFoundError,
    TokenRefreshError,
    AppException,
)


class AuthService:
    @staticmethod
    def register(username: str) -> dict:
        """
        僅使用手機號碼進行快速註冊。
        username 參數即為手機號碼。
        """
        # 1. 檢查使用者名稱 (手機號碼) 是否已存在
        if User.query.filter_by(username=username).first():
            raise UserAlreadyExistsError(message=f"手機號碼 '{username}' 已被註冊。")

        # 2. 設定初始密碼 (極度不安全，僅為符合「僅手機號碼」的快速流程)
        initial_password = username

        # 3. 生成預設的 Member 名稱
        default_member_name = f"隊員_{username[-4:]}"
        default_user_display_name = f"用戶_{username[-4:]}"  # User 的暱稱也可以有預設

        try:
            # 4. 創建 User 物件
            new_user = User(
                username=username,
                email=None,  # 快速註冊時 email 為空
                role=UserRoleEnum.MEMBER,
                display_name=default_user_display_name,
            )
            new_user.set_password(initial_password)  # 使用手機號碼作為初始密碼
            db.session.add(new_user)

            # 5. 創建 Member 物件並關聯
            new_member = Member(
                user=new_user,
                name=default_member_name,
                # 其他 Member bio 欄位使用預設值或為 None
            )
            db.session.add(new_member)

            # 預先 flush 以獲取 new_user.id (如果 JWT 生成需要)
            # db.session.flush() # 如果 create_access_token 需要 user.id 且 user 是新物件

            db.session.commit()

        except IntegrityError as e:
            db.session.rollback()
            # 雖然前面檢查過 username，但 email 也可能是 unique 的 (儘管現在是 None)
            # 或者其他資料庫層級的約束衝突
            raise UserAlreadyExistsError(message=f"註冊失敗，該手機號碼可能已被使用或發生資料庫衝突。")
        except Exception as e:
            db.session.rollback()
            raise AppException(message=f"註冊過程中發生未預期的錯誤: {str(e)}")

        # 6. 生成 Tokens
        # 確保 new_user.id 在 commit 後可用
        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)

        return {
            "user": new_user,  # 回傳 User 物件供後續序列化
            "access_token": access_token,
            "refresh_token": refresh_token,
            "initial_password_warning": f"您的帳號已使用手機號碼 '{initial_password}' 作為初始密碼創建。為了您的帳號安全，請在首次登入後立即修改密碼！",
        }

    @staticmethod
    def login(username: str, password: str) -> dict:
        """使用者登入。"""
        user = User.query.filter_by(username=username).first()

        if not user:
            user = User.query.filter_by(email=username).first()  # 也允許用 email 登入

        if not user or not user.check_password(password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserInactiveError()

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def refresh_access_token(user_id_str: str) -> str:
        """刷新 Access Token。"""
        try:
            user_id = int(user_id_str)
            user = db.session.get(User, user_id)  # 使用 db.session.get 獲取 User
            if not user or not user.is_active:
                raise TokenRefreshError()
        except ValueError:  # user_id_str 無法轉為 int
            raise TokenRefreshError(message="無效的使用者ID格式。")

        new_access_token = create_access_token(identity=user_id, fresh=False)
        return new_access_token

    @staticmethod
    def change_user_password(user_id: int, old_password: str, new_password: str) -> bool:
        """修改使用者密碼。"""
        user = db.session.get(User, user_id)  # 使用 db.session.get
        if not user:
            # 理論上，jwt_required 應確保 user 存在，但多一層防護
            raise UserNotFoundError()
        if not user.is_active:
            raise UserInactiveError()

        if not user.check_password(old_password):
            raise IncorrectPasswordError()

        # 可以在這裡加入更多新密碼的策略驗證，例如不能與最近幾次密碼相同等
        # 基礎的長度驗證已在 Schema 中完成，但服務層也可以再做一次或做更複雜的檢查
        if len(new_password) < 6:  # 範例：與 Schema 保持一致
            raise PasswordPolicyError(message="新密碼長度至少需要6位。")
        if old_password == new_password:
            raise PasswordPolicyError(message="新密碼不能與舊密碼相同。")

        user.set_password(new_password)
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise AppException(message=f"更新密碼時發生錯誤: {str(e)}")
