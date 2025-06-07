# backend/app/models/player_stats.py
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..extensions import db


class PlayerStats(db.Model):
    __tablename__ = "player_stats"

    id = db.Column(Integer, primary_key=True, comment="球員單場比賽統計的唯一識別碼")

    # --- 修正部分：加入與 MatchRecord 的關聯 ---
    # 1. 加入指向 match_records 資料表的外鍵
    match_record_id = db.Column(
        Integer,
        ForeignKey("match_records.id", name="fk_player_stats_match_record_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所屬的比賽記錄ID",
    )
    # 2. 加入與 MatchRecord.player_stats_entries 相互呼應的 relationship
    match_record = relationship("MatchRecord", back_populates="player_stats_entries")
    # --- 修正結束 ---

    # --- 關聯到是哪一位球員的數據 ---
    member_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_player_stats_member_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所屬的隊員ID",
    )
    # 這個 back_populates 必須與 Member 模型中的 'match_stats_records' 關聯對應
    member = relationship("Member", back_populates="match_stats_records")

    # --- 詳細統計數據欄位 (範例) ---
    # 您可以根據軟式網球的實際需求，在這裡加入更多欄位
    # 例如：
    # serves_in = db.Column(Integer, default=0, comment="發球進球數")
    # aces = db.Column(Integer, default=0, comment="Ace球數")
    # double_faults = db.Column(Integer, default=0, comment="雙發失誤數")
    # winners = db.Column(Integer, default=0, comment="致勝球數")
    # unforced_errors = db.Column(Integer, default=0, comment="非受迫性失誤數")

    def to_dict(self) -> dict:
        """將 PlayerStats 物件轉換為字典。"""
        return {
            "id": self.id,
            "match_record_id": self.match_record_id,
            "member_id": self.member_id,
            # "aces": self.aces, # ... 其他統計數據 ...
        }

    def __repr__(self) -> str:
        return f"<PlayerStats id={self.id}, match_id={self.match_record_id}, member_id={self.member_id}>"
