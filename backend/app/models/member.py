from typing import Dict

from sqlalchemy import Integer, String, Float, Date, Text, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from .enums.bio_enums import GenderEnum, BloodTypeEnum
from .enums.match_enums import MatchPositionEnum
from ..extensions import db


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(Integer, primary_key=True, comment="隊員唯一識別碼")  # 明確定義主鍵

    # --- 基本 Bio 資料 ---
    name = db.Column(String(80), nullable=False, comment="真實姓名")
    student_id = db.Column(String(20), unique=True, nullable=True, index=True, comment="學號")

    gender = db.Column(
        SQLAlchemyEnum(GenderEnum, name="gender_enum_members", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="性別",
    )
    blood_type = db.Column(  # 新增血型欄位
        SQLAlchemyEnum(BloodTypeEnum, name="blood_type_enum_members", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="血型",
    )
    position = db.Column(
        SQLAlchemyEnum(
            MatchPositionEnum, name="player_position_enum_members", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
        comment="擅長位置",
    )

    # --- 隊籍狀態與日期 ---
    joined_date = db.Column(Date, nullable=True, comment="入隊日期")
    leaved_date = db.Column(Date, nullable=True, comment="離隊日期 (若已離隊)")

    # --- TrueSkill 評分系統 (若仍視為基本資料一部分) ---
    mu = db.Column(Float, nullable=False, default=25.0, comment="TrueSkill μ (平均實力)")
    sigma = db.Column(Float, nullable=False, default=(25.0 / 3.0), comment="TrueSkill σ (實力不確定性)")

    notes = db.Column(Text, nullable=True, comment="關於此隊員的備註")

    # --- 關聯：所屬組織 ---
    organization_id = db.Column(
        Integer,
        ForeignKey("organizations.id", name="fk_members_organization_id"),
        nullable=True,
        index=True,
        comment="所屬組織ID",
    )
    organization = relationship("Organization", back_populates="members")

    # --- 關聯：使用球拍 ---
    racket_id = db.Column(
        Integer,
        ForeignKey("rackets.id", name="fk_members_racket_id"),
        nullable=True,
        index=True,
        comment="使用球拍ID",
    )
    racket = relationship(
        "Racket", back_populates="members_using"
    )  # 'Racket' 是模型類名, 'members_using' 是 Racket 模型中反向關聯屬性

    # --- 關聯：對應的使用者帳號 (一對一) ---
    user_id = db.Column(
        Integer,
        ForeignKey("users.id", name="fk_members_user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="對應的使用者帳號ID",
    )
    user = relationship("User", back_populates="member_profile")

    # --- 關聯：該隊員的所有比賽統計記錄 (若將其視為 Member 的一部分) ---
    match_stats_records = relationship(
        "PlayerStats", back_populates="member", lazy="dynamic", cascade="all, delete-orphan"
    )

    # --- 計算屬性 ---
    @property
    def score(self):
        """一個基於 TrueSkill 的保守評分。"""
        return (self.mu - 3 * self.sigma) * 100

    def to_dict(self, org_detail=True, racket_detail=True, user_detail=True) -> Dict:
        """將 Member 物件轉換為字典。"""
        data = {
            "id": self.id,
            "name": self.name,
            "student_id": self.student_id,
            "gender": self.gender.value if self.gender else None,
            "blood_type": self.blood_type.value if self.blood_type else None,  # 新增
            "position": self.position.value if self.position else None,
            "is_active": self.is_active,
            "joined_date": self.joined_date.isoformat() if self.joined_date else None,
            "leaved_date": self.leaved_date.isoformat() if self.leaved_date else None,
            "mu": round(self.mu, 3) if self.mu is not None else None,
            "sigma": round(self.sigma, 3) if self.sigma is not None else None,
            "score": self.score,
            "notes": self.notes,
            "user_id": self.user_id,
        }

        if org_detail:
            data["organization_id"] = self.organization_id
            data["organization_name"] = (
                self.organization.name if self.organization and hasattr(self.organization, "name") else None
            )

        if racket_detail:  # 新增
            data["racket_id"] = self.racket_id
            data["racket_info"] = (
                self.racket.to_dict()
                if self.racket and hasattr(self.racket, "to_dict")
                else (self.racket.name if self.racket and hasattr(self.racket, "name") else None)
            )

        if user_detail and self.user:
            data["user_info"] = {
                "username": self.user.username,
                "user_display_name": self.user.display_name,
                "role": self.user.role.value if self.user.role else None,
            }
        return data

    def __repr__(self) -> str:
        org_name = self.organization.name if self.organization and hasattr(self.organization, "name") else None
        org_info = f" (Org: {org_name})" if org_name else ""
        return f"<Member id={self.id}, name='{self.get_current_display_name()}'{org_info}>"
