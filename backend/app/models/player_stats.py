# 建議放在 app/models/player_match_stats.py
from ..extensions import db


class PlayerStats(db.Model):
    """
    記錄特定球員在特定單場比賽中的進階統計數據
    """
    __tablename__ = 'player_stats'
    id = db.Column(db.Integer, primary_key=True)

    match_id = db.Column(db.Integer, db.ForeignKey('match_records.id'), nullable=False, comment="對應的單場比賽ID")
    player_id = db.Column(db.Integer, db.ForeignKey('team_members.id'), nullable=False, comment="對應的球員ID")

    # --- 以下為可記錄的進階數據範例 ---
    # 您可以根據實際需要增減這些欄位
    # 發球 (Serve)
    aces = db.Column(db.Integer, default=0, comment="Ace球數量")
    double_faults = db.Column(db.Integer, default=0, comment="雙發失誤數量")
    first_serves_in = db.Column(db.Integer, default=0, comment="一發進球數")
    first_serves_total = db.Column(db.Integer, default=0, comment="一發總數")
    second_serves_in = db.Column(db.Integer, default=0, comment="二發進球數")
    second_serves_total = db.Column(db.Integer, default=0, comment="二發總數")

    # 得分相關 (Scoring)
    winners = db.Column(db.Integer, default=0, comment="致勝球數量 (不含Ace)")
    unforced_errors = db.Column(db.Integer, default=0, comment="非受迫性失誤數量")
    forced_errors_caused = db.Column(db.Integer, default=0, comment="造成對手受迫性失誤數量")  # 對手因我方好球而失誤

    # 網前表現 (Net Play)
    net_points_won = db.Column(db.Integer, default=0, comment="網前得分")
    net_points_played = db.Column(db.Integer, default=0, comment="總上網次數")

    # 關鍵分 (Key Points)
    break_points_won = db.Column(db.Integer, default=0, comment="破發點得分數")
    break_points_saved = db.Column(db.Integer, default=0, comment="救回的破發點數")
    break_points_opportunities = db.Column(db.Integer, default=0, comment="總破發點機會數")  # 自己拿到的破發點

    # 其他綜合數據
    total_points_won = db.Column(db.Integer, default=0, comment="總得分")
    # games_won = db.Column(db.Integer, default=0, comment="贏得的局數") # 這個可能比較適合放在 MatchRecord 或從 score_str 分析

    custom_stat_field_1 = db.Column(db.String(255), nullable=True, comment="自訂統計欄位1")  # 預留彈性
    custom_stat_field_2 = db.Column(db.Float, nullable=True, comment="自訂統計欄位2")  # 預留彈性

    # 確保一個球員在一場比賽中只有一條統計記錄
    __table_args__ = (db.UniqueConstraint('match_id', 'player_id', name='_match_player_stats_uc'),)

    def __repr__(self):
        return f"<PlayerMatchStats for Player ID {self.player_id} in Match ID {self.match_id}>"