# your_project/app/services/match_service.py
from flask import current_app
from sqlalchemy.orm import joinedload

from .rating_service import RatingService  # 導入評分服務
from ..extensions import db
from ..models import MatchRecord, Member  # 導入您的模型
from ..models.enums.match_enums import MatchOutcomeEnum
from ..tools.exceptions import AppException, ValidationError


class MatchRecordService:
    @staticmethod
    def _calculate_outcome(games_a: int, games_b: int) -> MatchOutcomeEnum:
        """根據 A 方和 B 方的局數計算 A 方的賽果。"""
        return MatchOutcomeEnum.WIN if games_a > games_b else MatchOutcomeEnum.LOSS

    @staticmethod
    def create_match_record(data: dict) -> MatchRecord:
        """
        創建一個新的比賽記錄，並觸發評分更新。
        'data' 是經過 MatchRecordCreateSchema 驗證後的數據。
        """
        try:
            # 1. 創建 MatchRecord 物件
            # 注意：這裡的欄位名稱現在與您的新 MatchRecord 模型完全對應
            new_record = MatchRecord(
                match_date=data["match_date"],
                match_type=data["match_type"],  # 來自 Schema 的 MatchTypeEnum
                match_format=data["match_format"],  # 來自 Schema 的 MatchFormatEnum
                player1_id=data["player1_id"],
                player2_id=data.get("player2_id"),
                player3_id=data["player3_id"],
                player4_id=data.get("player4_id"),
                a_games=data["a_games"],
                b_games=data["b_games"],
                match_notes=data.get("match_notes"),
            )
            # 根據 a_games 和 b_games 計算 side_a_outcome
            new_record.side_a_outcome = MatchRecordService._calculate_outcome(new_record.a_games, new_record.b_games)
            db.session.add(new_record)

            # 2. 呼叫 RatingService 更新評分
            # RatingService 內部也需要調整以使用新的欄位名
            RatingService.update_ratings_from_match(new_record)

            # 未來您可以在此處添加創建 PlayerStats 的邏輯

            db.session.commit()
            return new_record
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"創建比賽記錄時出錯: {e}", exc_info=True)
            if isinstance(e, ValidationError):  # 如果是我們自己拋出的驗證錯誤
                raise e
            raise AppException("創建比賽記錄時發生未預期錯誤。")

    @staticmethod
    def get_match_record_by_id(record_id: int):
        """根據 ID 獲取單場比賽記錄，並預先載入所有球員資訊。"""
        return MatchRecord.query.options(
            joinedload(MatchRecord.player1).subqueryload(Member.user),
            joinedload(MatchRecord.player2).subqueryload(Member.user),
            joinedload(MatchRecord.player3).subqueryload(Member.user),
            joinedload(MatchRecord.player4).subqueryload(Member.user),
        ).get(record_id)

    @staticmethod
    def get_all_match_records(args: dict):
        """獲取比賽記錄列表。"""
        query = MatchRecord.query.order_by(MatchRecord.match_date.desc(), MatchRecord.id.desc())
        # 在此處可以根據 args 加入篩選和分頁邏輯
        return query.all()

    @staticmethod
    def delete_match_record(record: MatchRecord) -> bool:
        """
        刪除一場比賽記錄，並觸發相關球員的評分重新計算。
        """
        if not record:
            raise AppException("找不到要刪除的比賽記錄。", status_code=404)

        # 獲取所有受影響的球員 ID
        affected_player_ids = [
            p_id for p_id in [record.player1_id, record.player2_id, record.player3_id, record.player4_id] if p_id
        ]

        try:
            # 刪除記錄
            db.session.delete(record)

            # 重新計算分數
            RatingService.recalculate_ratings_for_players(affected_player_ids)

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"刪除比賽記錄 ID {record.id} 時出錯: {e}", exc_info=True)
            raise AppException("刪除比賽記錄時發生未預期錯誤。")
