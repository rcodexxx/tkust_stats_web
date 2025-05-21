from ..extensions import db
from .enums import OverallMatchNatureEnum, SQLAlchemyEnum
import datetime

class TeamEvent(db.Model):
    """
    代表一次完整的團體賽事，例如「大專盃 vs. 輔仁大學」
    一個 TeamEvent 可以包含多個 MatchRecord (多點單雙打)
    """
    __tablename__ = 'team_events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, comment="賽事名稱 (例：113學年度大專盃淘汰賽 vs 台灣大學)")
    event_date = db.Column(db.Date, nullable=False, default=datetime.date.today, comment="賽事日期")
    opponent_team_overall = db.Column(db.String(100), nullable=True, comment="對手隊伍總稱")
    nature = db.Column(SQLAlchemyEnum(OverallMatchNatureEnum), nullable=True, comment="整體賽事性質")
    venue = db.Column(db.String(100), nullable=True, comment="比賽地點")
    event_notes = db.Column(db.Text, nullable=True, comment="團隊賽事備註")

    match_records = db.relationship('MatchRecord', backref='team_event_parent', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TeamEvent '{self.name}' on {self.event_date}>"