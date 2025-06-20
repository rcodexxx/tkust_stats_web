# backend/app/models/player_stats.py (擴展版)
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from ..extensions import db


class PlayerStats(db.Model):
    __tablename__ = "player_stats"

    id = db.Column(Integer, primary_key=True, comment="球員單場比賽統計的唯一識別碼")

    # 關聯到比賽記錄
    match_record_id = db.Column(
        Integer,
        ForeignKey(
            "match_records.id",
            name="fk_player_stats_match_record_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="所屬的比賽記錄ID",
    )
    match_record = relationship("MatchRecord", back_populates="player_stats_entries")

    # 關聯到選手
    member_id = db.Column(
        Integer,
        ForeignKey("members.id", name="fk_player_stats_member_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所屬的隊員ID",
    )
    member = relationship("Member", back_populates="match_stats_records")

    # 🔥 新增：基本統計欄位
    points_won = db.Column(Integer, nullable=True, default=0, comment="總得分")

    # 🔥 新增：彈性擴展欄位（JSON格式，支援未來統計需求）
    additional_stats = db.Column(JSON, nullable=True, comment="額外統計數據(JSON格式)")

    # 🔥 新增：時間戳
    created_at = db.Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="創建時間"
    )
    updated_at = db.Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新時間",
    )

    # 🔥 新增：表級約束
    __table_args__ = (
        db.UniqueConstraint(
            "match_record_id", "member_id", name="uq_player_stats_match_member"
        ),
    )

    # 🔥 新增：便利方法
    def get_additional_stat(self, stat_name: str, default=None):
        """從 additional_stats JSON 中獲取特定統計數據"""
        if not self.additional_stats:
            return default
        return self.additional_stats.get(stat_name, default)

    def set_additional_stat(self, stat_name: str, value):
        """設置額外的統計數據到 JSON 欄位"""
        if not self.additional_stats:
            self.additional_stats = {}

        stats = dict(self.additional_stats)
        stats[stat_name] = value
        self.additional_stats = stats

    def to_dict(self) -> dict:
        """將 PlayerStats 物件轉換為字典"""
        return {
            "id": self.id,
            "match_record_id": self.match_record_id,
            "member_id": self.member_id,
            "member_name": self.member.name if self.member else None,
            "points_won": self.points_won,
            "additional_stats": self.additional_stats or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<PlayerStats id={self.id}, match_id={self.match_record_id}, member_id={self.member_id}, points={self.points_won}>"
