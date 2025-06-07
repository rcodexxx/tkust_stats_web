# backend/app/models/match.py
from sqlalchemy import Integer, Date, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from .enums import MatchTypeEnum, MatchFormatEnum
from ..extensions import db


# 如果需要，也可以從 common_enums 導入 OrganizationTypeEnum 等
# from your_project.app.enums.common_enums import OrganizationTypeEnum


class Match(db.Model):
    __tablename__ = "matches"  # 新的表名

    id = db.Column(Integer, primary_key=True, comment="比賽唯一識別碼")
    match_date = db.Column(Date, nullable=False, index=True, comment="比賽日期")

    match_type = db.Column(
        SQLAlchemyEnum(
            MatchTypeEnum,
            name="match_type_enum_matches",  # 資料庫 ENUM 型別名稱
            values_callable=lambda x: [e.value for e in x],  # 使用 Enum 的 value
        ),
        nullable=False,
        comment="比賽類型 (單打、雙打、混雙)",
    )
    match_format = db.Column(
        SQLAlchemyEnum(
            MatchFormatEnum, name="match_format_enum_matches", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,  # MatchRecord 中此欄位是 nullable=False
        comment="賽制",
    )

    results = relationship("MatchRecord", back_populates="match", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "match_type": self.match_type.value if self.match_type else None,
            "match_format": self.match_format.value if self.match_format else None,
            "notes": self.notes,
        }
        return data

    def __repr__(self) -> str:
        return (
            f"<Match id={self.id}, date='{self.match_date}', type='{self.match_type.value if self.match_type else ''}'>"
        )
