from datetime import datetime

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Float

from .enums import GenderEnum, PositionEnum
from ..extensions import db


class TeamMember(db.Model):
    __tablename__ = "members"
    # Basic data
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment="真實姓名")
    display_name = db.Column(db.String(20), nullable=False, comment="暱稱")
    organization = db.Column(db.String(50), nullable=False, comment="組織/單位")
    student_id = db.Column(db.String(15), unique=True, nullable=True, comment="學號")
    gender = db.Column(SQLAlchemyEnum(GenderEnum), nullable=True, comment="性別")
    position = db.Column(SQLAlchemyEnum(PositionEnum), nullable=True, comment="位置")

    # TrueSkill
    mu = db.Column(Float, nullable=False, default=25.0, comment="TrueSkill μ")
    sigma = db.Column(Float, nullable=False, default=8.333, comment="TrueSkill σ")

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    joined_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    leaved_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    notes = db.Column(db.Text, nullable=True, comment="備註")

    # User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_team_member_user_id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
        index=True,
    )
    user_account = db.relationship("User", back_populates="team_member_profile")

    match_stats_records = db.relationship(
        "PlayerStats", backref="player", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def score(self):
        return int((self.mu - 3 * self.sigma) * 100)

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "score": self.score,
            "mu": round(self.mu, 2),
            "sigma": round(self.sigma, 2),
            "student_id": self.student_id,
            "gender": self.gender.value if self.gender else None,
            "position": self.position.value if self.position else None,
        }
        return data

    def __repr__(self):
        return f"<TeamMember {self.name}>"
