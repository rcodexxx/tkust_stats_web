from ..extensions import db
from .enums import GenderEnum, PositionEnum, SQLAlchemyEnum
from sqlalchemy import Float

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    # Basic data
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment="姓名")
    student_id = db.Column(db.String(20), unique=True, nullable=True, comment="學號")
    gender = db.Column(SQLAlchemyEnum(GenderEnum), nullable=True, comment="性別")
    position = db.Column(SQLAlchemyEnum(PositionEnum), nullable=True, comment="位置")

    # TrueSkill
    mu = db.Column(Float, nullable=False, default=25.0, comment="TrueSkill μ")
    sigma = db.Column(Float, nullable=False, default=8.333, comment="TrueSkill σ")

    is_active = db.Column(db.Boolean, default=True, nullable=False, comment="是否為現役隊員")
    notes = db.Column(db.Text, nullable=True, comment="備註")

    match_stats_records = db.relationship('PlayerStats', backref='player', lazy='dynamic', cascade="all, delete-orphan")

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