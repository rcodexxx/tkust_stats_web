import datetime

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Integer, String
from werkzeug.security import check_password_hash, generate_password_hash

from .enums import UserRoleEnum
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    username = db.Column(
        String(30), unique=True, nullable=False, index=True, comment="帳號"
    )
    password_hash = db.Column(String(256), nullable=False)
    role = db.Column(
        SQLAlchemyEnum(
            UserRoleEnum,
            name="user_role_enum_users",
            create_type=False,
            values_callable=lambda x: [e.name for e in x],
        ),
        nullable=False,
        default=UserRoleEnum.MEMBER,
        comment="使用者角色",
    )
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # 與 TeamMember 的一對一反向關聯
    team_member_profile = db.relationship(
        "Member",
        back_populates="user_account",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRoleEnum.ADMIN

    def is_cadre(self):
        return self.role == UserRoleEnum.CADRE

    def is_coach(self):
        return self.role == UserRoleEnum.COACH

    def to_dict(self):  # 新增一個參數控制是否包含成員資訊
        member_profile = self.team_member_profile
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.name if self.role else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "display_name": (
                member_profile.display_name if member_profile.display_name else None
            ),
        }

        return data

    def __repr__(self):
        return (
            f"<User {self.username} (Role: {self.role.name if self.role else 'N/A'})>"
        )
