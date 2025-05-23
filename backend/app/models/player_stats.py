# backend/app/models/player_match_stats.py
from ..extensions import db

class PlayerStats(db.Model):
    __tablename__ = 'player_stats' # 確認表名與 TeamMember 中 relationship 一致
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match_records.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('team_members.id'), nullable=False)

    # 這裡可以放非常詳細的數據，例如：
    # games_won = db.Column(db.Integer, default=0)
    # aces = db.Column(db.Integer, default=0)
    # double_faults = db.Column(db.Integer, default=0)
    # winners = db.Column(db.Integer, default=0)
    # unforced_errors = db.Column(db.Integer, default=0)
    # ... 等等，根據您未來想記錄的詳細程度

    # 暫時可以只有基礎結構，未來再擴充欄位並遷移
    notes = db.Column(db.Text, nullable=True, comment="該球員本場比賽的特殊記錄")

    __table_args__ = (db.UniqueConstraint('match_id', 'player_id', name='_match_player_stats_uc'),)

    def __repr__(self):
        return f"<PlayerMatchStats for Player ID {self.player_id} in Match ID {self.match_id}>"