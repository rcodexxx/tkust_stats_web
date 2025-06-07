import datetime  # 確保導入 datetime

from sqlalchemy import Integer, String, Enum as SQLAlchemyEnum
from werkzeug.security import generate_password_hash, check_password_hash

from .enums.user_enums import UserRoleEnum
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(Integer, primary_key=True, comment="使用者唯一識別碼")
    username = db.Column(String(30), unique=True, nullable=False, index=True, comment="帳號 (登入用)")
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True,
        index=True,
        comment="電子郵件 (通常用於登入或通知)",
    )
    password_hash = db.Column(String(256), nullable=False, comment="雜湊後的密碼")
    display_name = db.Column(String(50), nullable=True, comment="暱稱 (顯示名稱)")

    role = db.Column(
        SQLAlchemyEnum(
            UserRoleEnum,
            name="user_role_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=UserRoleEnum.MEMBER,  # 預設角色為隊員
        comment="使用者角色",
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        comment="最後更新時間",
    )

    is_active = db.Column(db.Boolean, default=True, nullable=False, comment="帳號是否啟用")
    member_profile = db.relationship(
        "Member",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str):
        """
        設定使用者密碼。
        會將傳入的明文密碼雜湊化後儲存。
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        檢查傳入的明文密碼是否與儲存的雜湊密碼相符。
        """
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """
        將 User 物件轉換為字典。
        :return: dict
        """
        data = {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User id={self.id}, username='{self.username}', role='{self.role.value}'>"
