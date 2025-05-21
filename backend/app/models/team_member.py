from ..extensions import db
from .enums import GenderEnum, PositionEnum, SQLAlchemyEnum
import datetime

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment="姓名")
    student_id = db.Column(db.String(20), unique=True, nullable=True, comment="學號")
    organization_id = db.Column(db.String(20), nullable=True, comment="單位")
    gender = db.Column(SQLAlchemyEnum(GenderEnum), nullable=True, comment="性別")
    position = db.Column(SQLAlchemyEnum(PositionEnum), nullable=True, comment="位置")
    score = db.Column(db.Integer, nullable=False, default=0, comment="積分")
    racket = db.Column(db.String(100), nullable=True, comment="球拍")
    join_date = db.Column(db.Date, nullable=True, default=datetime.date.today, comment="入隊日期")
    leave_date = db.Column(db.Date, nullable=True, comment="離隊日期")
    is_active = db.Column(db.Boolean, default=True, nullable=False, comment="是否為現役隊員")
    notes = db.Column(db.Text, nullable=True, comment="備註")

    match_stats_records = db.relationship('PlayerStats', backref='player', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TeamMember {self.name}>"