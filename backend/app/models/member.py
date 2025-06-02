from sqlalchemy import Enum as SQLAlchemyEnum

from .enums import GenderEnum, PositionEnum
from ..extensions import db


class Member(db.Model):
    __tablename__ = "members"
    # Basic data
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment="真實姓名")
    display_name = db.Column(db.String(20), nullable=False, comment="暱稱")
    student_id = db.Column(db.String(15), unique=True, nullable=True, comment="學號")
    gender = db.Column(
        SQLAlchemyEnum(GenderEnum), nullable=True, create_type=False, comment="性別"
    )
    position = db.Column(
        SQLAlchemyEnum(PositionEnum), nullable=True, create_type=False, comment="位置"
    )

    # TrueSkill
    mu = db.Column(db.Float, nullable=False, default=25.0, comment="TrueSkill μ")
    sigma = db.Column(db.Float, nullable=False, default=8.333, comment="TrueSkill σ")

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    joined_date = db.Column(db.Date, nullable=True)
    leaved_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True, comment="備註")

    # Organization
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", name="fk_member_organization_id"),
        nullable=True,
    )
    organization_profile = db.relationship("Organization", back_populates="members")

    # User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_team_member_user_id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
        index=True,
    )
    user_account = db.relationship("User", back_populates="team_member_profile")

    # Stats
    match_stats_records = db.relationship(
        "PlayerStats", backref="player", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def score(self):
        return int((self.mu - 3 * self.sigma) * 100)

    def get_display_name(self):
        return (
            self.display_name
            if self.display_name and self.display_name.strip()
            else self.name
        )

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "display_name": self.get_display_name(),  # 使用 get_display_name 更佳
            "organization_id": self.organization_id,
            "organization_name": (
                self.organization_profile.name if self.organization_profile else None
            ),
            "score": self.score,  # 確保 self.score 是一個有效的屬性或計算屬性
            "mu": (
                round(self.mu, 2) if self.mu is not None else None
            ),  # 處理 mu 可能為 None
            "sigma": (
                round(self.sigma, 2) if self.sigma is not None else None
            ),  # 處理 sigma 可能為 None
            "student_id": self.student_id,
            "gender": self.gender.name if self.gender else None,  # 返回 Enum 的 NAME
            "position": (self.position.name if self.position else None),
            "notes": self.notes,
            "is_active": self.is_active,  # Member 自身的活躍狀態
            "joined_date": self.joined_date.isoformat() if self.joined_date else None,
            "leaved_date": self.leaved_date.isoformat() if self.leaved_date else None,
            # 初始化 User 相關欄位為 None
            "user_id": self.user_id,  # 直接使用外鍵 user_id，即使 user_account 未載入或不存在，這個 ID 也可能存在
            "username": None,  # User 的登入帳號 (手機號)
            "user_email": None,  # User 的 Email
            "user_role": None,  # User 的角色 (Enum NAME)
        }

        if self.user_account:  # 檢查是否存在關聯的 User 物件
            # data["user_id"] = self.user_account.id # User 的主鍵，其實與 self.user_id 應該相同
            data["username"] = self.user_account.username
            data["user_email"] = self.user_account.email
            data["user_role"] = (
                self.user_account.role.name if self.user_account.role else None
            )

        return data

    def __repr__(self):
        org_info = (
            f" (Org: {self.organization_profile.short_name or self.organization_profile.name})"
            if self.organization_profile
            else ""
        )
        return f"<Member {self.name}{org_info}>"
