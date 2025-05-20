from backend.app.extensions import db
from backend.app.models.enums import MatchTypeEnum, OutcomeEnum, SQLAlchemyEnum
import datetime


class MatchRecord(db.Model):
    """
    記錄每一場單獨的比賽 (可能是某個 TeamEvent 下的一點，或獨立的比賽)
    """
    __tablename__ = 'match_records'
    id = db.Column(db.Integer, primary_key=True)

    # 外鍵: 可選地關聯到一個 TeamEvent
    team_event_id = db.Column(db.Integer, db.ForeignKey('team_events.id'), nullable=True, comment="所屬團隊賽事ID")

    # 我方球員 (單打則 player2_id 為空)
    player1_id = db.Column(db.Integer, db.ForeignKey('team_members.id'), nullable=False, comment="我方球員1 ID")
    player1 = db.relationship('TeamMember', foreign_keys=[player1_id],
                              backref=db.backref('matches_as_player1', lazy='dynamic'))

    player2_id = db.Column(db.Integer, db.ForeignKey('team_members.id'), nullable=True, comment="我方球員2 ID (雙打時)")
    player2 = db.relationship('TeamMember', foreign_keys=[player2_id],
                              backref=db.backref('matches_as_player2', lazy='dynamic'))

    # 對方球員
    opponent_player1_name = db.Column(db.String(100), nullable=True, comment="對方球員1姓名")
    opponent_player2_name = db.Column(db.String(100), nullable=True, comment="對方球員2姓名 (雙打時)")

    match_date = db.Column(db.Date, nullable=False, default=datetime.date.today, comment="單場比賽日期")
    match_type = db.Column(SQLAlchemyEnum(MatchTypeEnum), nullable=False, comment="單打/雙打")

    our_score_str = db.Column(db.String(50), nullable=True, comment="我方得分 (例: 6,6 / 7-5,6-2)")
    opponent_score_str = db.Column(db.String(50), nullable=True, comment="對方得分 (例: 2,3 / 6-7,2-6)")
    outcome = db.Column(SQLAlchemyEnum(OutcomeEnum), nullable=True, comment="比賽結果 (勝/負)")

    point_order_in_event = db.Column(db.String(50), nullable=True,
                                     comment="在團隊賽中的點數/順序 (例: 第一點單打, 第二點雙打)")
    match_notes = db.Column(db.Text, nullable=True, comment="單場比賽備註")

    # 反向關聯: 一場比賽可以有多個球員的統計數據 (我方球員)
    player_stats = db.relationship('PlayerStats', backref='match_record_parent', lazy='dynamic',
                                   cascade="all, delete-orphan")

    def __repr__(self):
        p1_name = self.player1.name if self.player1 else 'N/A'
        return f"<MatchRecord ID {self.id} featuring {p1_name} on {self.match_date}>"