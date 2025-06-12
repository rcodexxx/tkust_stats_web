# backend/app/models/match_record.py
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship

from ..extensions import db
from .enums import MatchOutcomeEnum


class MatchRecord(db.Model):
    __tablename__ = "match_records"

    id = db.Column(Integer, primary_key=True, comment="比賽記錄唯一識別碼")

    match_id = db.Column(
        Integer,
        ForeignKey("matches.id", name="fk_match_records_match_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="所屬比賽事件ID",
    )
    match = relationship("Match", back_populates="results")

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
    )
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

    @property
    def total_games(self) -> int:
        """總局數 = A方局數 + B方局數"""
        return self.a_games + self.b_games

    def to_dict(self, details: bool = False) -> dict:
        data = {
            "id": self.id,
            "match_id": self.match_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "player3_id": self.player3_id,
            "player4_id": self.player4_id,
            "a_games": self.a_games,
            "b_games": self.b_games,
            "total_games": self.total_games,
            "side_a_outcome": self.side_a_outcome.value if self.side_a_outcome else None,
        }
        if details:
            data["player_stats"] = (
                [stat.to_dict() for stat in self.player_stats_entries] if self.player_stats_entries else []
            )
        return data

    def __repr__(self) -> str:
        return f"<MatchRecord id={self.id}, match_id={self.match_id}, a_games={self.a_games}, b_games={self.b_games}>"
