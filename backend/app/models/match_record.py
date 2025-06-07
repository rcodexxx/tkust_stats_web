# backend/app/models/match_record.py
import datetime

from sqlalchemy import Integer, Date, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship  # foreign 用於指定 relationship 的 foreign_keys

from .enums import (
    MatchFormatEnum,
    MatchTypeEnum,
    MatchOutcomeEnum,
)
from ..extensions import db


class MatchRecord(db.Model):
    __tablename__ = "match_records"

    id = db.Column(Integer, primary_key=True, comment="比賽記錄唯一識別碼")

    match_date = db.Column(Date, nullable=False, default=datetime.date.today, index=True, comment="比賽日期")
    match_type = db.Column(
        SQLAlchemyEnum(
            MatchFormatEnum, name="match_type_enum_match_records", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        comment="比賽類型",
    )
    match_format = db.Column(
        SQLAlchemyEnum(
            MatchTypeEnum, name="match_format_enum_match_records", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        comment="賽制",
    )

    # --- Side A Players ---
    player1_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p1_id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    player1 = relationship("Member", foreign_keys=[player1_id], backref="match_records_p1")

    player2_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p2_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    player2 = relationship("Member", foreign_keys=[player2_id], backref="match_records_p2")

    # --- Side B Players ---
    player3_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p3_id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    player3 = relationship("Member", foreign_keys=[player3_id], backref="match_records_p3")

    player4_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_match_records_p4_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )  # 雙打時的隊友
    player4 = relationship("Member", foreign_keys=[player4_id], backref="match_records_p4")

    # --- Scores and Outcome ---
    a_games = db.Column(Integer, nullable=False, comment="A方贏得的總局數")
    b_games = db.Column(Integer, nullable=False, comment="B方贏得的總局數")

    # 記錄 A 方的賽果，B 方的賽果可以由此推斷
    side_a_outcome = db.Column(
        SQLAlchemyEnum(
            MatchOutcomeEnum,
            name="outcome_enum_match_records",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="A方視角的比賽結果 (勝/負)",
    )

    # --- 關聯到球員的詳細統計數據 ---
    player_stats_entries = relationship(
        "PlayerStats",
        back_populates="match_record",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self, details: bool = False) -> dict:
        data = {
            "id": self.id,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "match_type": self.match_type.value if self.match_type else None,
            "match_format": self.match_format.value if self.match_format else None,
            "player1": self.player1_id,
            "player2": self.player2_id,
            "player3": self.player3_id,
            "player4": self.player4_id,
            "a_games": self.a_games,
            "b_games": self.b_games,
            "side_a_outcome": self.side_a_outcome.value if self.side_a_outcome else None,
            "match_notes": self.match_notes,
        }
        if details:
            data["player_stats"] = (
                [stat.to_dict() for stat in self.player_stats_entries] if self.player_stats_entries else []
            )
        return data

    def __repr__(self) -> str:
        return f"<MatchRecord id={self.id}, date='{self.match_date}', type='{self.match_type.value if self.match_type else ''}'>"
