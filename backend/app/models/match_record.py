# backend/app/models/match_record.py
import datetime

from sqlalchemy import Enum as SQLAlchemyEnum

from ..extensions import db
from ..models.enums import (
    MatchFormatEnum,  # <--- 加入 MatchFormatEnum
    MatchTypeEnum,
    OutcomeEnum,
)


class MatchRecord(db.Model):
    __tablename__ = "match_records"
    id = db.Column(db.Integer, primary_key=True)

    match_date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    match_type = db.Column(
        SQLAlchemyEnum(MatchTypeEnum, name="match_type_enum_mr", create_type=False),
        nullable=False,
    )
    match_format = db.Column(
        SQLAlchemyEnum(MatchFormatEnum, name="match_format_enum_mr", create_type=False),
        nullable=False,
        comment="賽制",
    )  # <--- 新增賽制欄位

    side_a_player1_id = db.Column(
        db.Integer, db.ForeignKey("members.id"), nullable=False
    )
    side_a_player1 = db.relationship(
        "Member",
        foreign_keys=[side_a_player1_id],
        backref="matches_as_side_a_p1_mr",
    )  # 調整 backref 名稱

    side_a_player2_id = db.Column(
        db.Integer, db.ForeignKey("members.id"), nullable=True
    )
    side_a_player2 = db.relationship(
        "Member",
        foreign_keys=[side_a_player2_id],
        backref="matches_as_side_a_p2_mr",
    )

    side_b_player1_id = db.Column(
        db.Integer, db.ForeignKey("members.id"), nullable=False
    )
    side_b_player1 = db.relationship(
        "Member",
        foreign_keys=[side_b_player1_id],
        backref="matches_as_side_b_p1_mr",
    )

    side_b_player2_id = db.Column(
        db.Integer, db.ForeignKey("members.id"), nullable=True
    )
    side_b_player2 = db.relationship(
        "Member",
        foreign_keys=[side_b_player2_id],
        backref="matches_as_side_b_p2_mr",
    )

    side_a_games_won = db.Column(db.Integer, nullable=False, comment="A方贏得的總局數")
    side_b_games_won = db.Column(db.Integer, nullable=False, comment="B方贏得的總局數")

    side_a_outcome = db.Column(
        SQLAlchemyEnum(OutcomeEnum, name="outcome_enum_mr", create_type=False),
        nullable=False,
        comment="A方視角的比賽結果",
    )

    match_notes = db.Column(db.Text, nullable=True)

    # PlayerMatchStats 關聯 (為未來做準備)
    # 一場 MatchRecord 可以對應到多個 PlayerMatchStats (例如雙打時，side_a_player1, side_a_player2, side_b_player1, side_b_player2 各一條)
    player_stats = db.relationship(
        "PlayerStats", backref="match", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "match_type": self.match_type.value if self.match_type else None,
            "match_format": self.match_format.value if self.match_format else None,
            "side_a_player1": (
                {"id": self.side_a_player1_id, "name": self.side_a_player1.name}
                if self.side_a_player1
                else None
            ),
            "side_a_player2": (
                {"id": self.side_a_player2_id, "name": self.side_a_player2.name}
                if self.side_a_player2
                else None
            ),
            "side_b_player1": (
                {"id": self.side_b_player1_id, "name": self.side_b_player1.name}
                if self.side_b_player1
                else None
            ),
            "side_b_player2": (
                {"id": self.side_b_player2_id, "name": self.side_b_player2.name}
                if self.side_b_player2
                else None
            ),
            "side_a_games_won": self.side_a_games_won,
            "side_b_games_won": self.side_b_games_won,
            "side_a_outcome": (
                self.side_a_outcome.value if self.side_a_outcome else None
            ),
            "match_notes": self.match_notes,
        }
