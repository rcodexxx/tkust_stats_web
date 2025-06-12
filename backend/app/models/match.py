# backend/app/models/match.py
from sqlalchemy import Date, Integer, Text, Time
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from ..extensions import db
from .enums import (
    CourtEnvironmentEnum,
    CourtSurfaceEnum,
    MatchFormatEnum,
    MatchTimeSlotEnum,
    MatchTypeEnum,
)


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(Integer, primary_key=True, comment="比賽唯一識別碼")
    match_date = db.Column(Date, nullable=False, index=True, comment="比賽日期")

    # 時間相關字段
    match_time = db.Column(Time, nullable=True, comment="比賽時間")
    match_time_slot = db.Column(
        SQLAlchemyEnum(
            MatchTimeSlotEnum,
            name="match_time_slot_enum_matches",
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
        comment="比賽時間段"
    )

    # 場地相關字段
    court_surface = db.Column(
        SQLAlchemyEnum(
            CourtSurfaceEnum,
            name="court_surface_enum_matches",
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
        comment="場地材質"
    )
    court_environment = db.Column(
        SQLAlchemyEnum(
            CourtEnvironmentEnum,
            name="court_environment_enum_matches",
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
        comment="場地環境"
    )

    # 備註字段
    notes = db.Column(Text, nullable=True, comment="比賽備註")

    # 原有必要字段
    match_type = db.Column(
        SQLAlchemyEnum(
            MatchTypeEnum,
            name="match_type_enum_matches",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="比賽類型 (單打、雙打、混雙)",
    )
    match_format = db.Column(
        SQLAlchemyEnum(
            MatchFormatEnum,
            name="match_format_enum_matches",
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        comment="賽制",
    )

    results = relationship("MatchRecord", back_populates="match", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "match_time": self.match_time.isoformat() if self.match_time else None,
            "match_time_slot": self.match_time_slot.value if self.match_time_slot else None,
            "court_surface": self.court_surface.value if self.court_surface else None,
            "court_environment": self.court_environment.value if self.court_environment else None,
            "match_type": self.match_type.value if self.match_type else None,
            "match_format": self.match_format.value if self.match_format else None,
            "notes": self.notes,
        }
        return data

    def __repr__(self) -> str:
        return (
            f"<Match id={self.id}, date='{self.match_date}', type='{self.match_type.value if self.match_type else ''}'>"
        )
