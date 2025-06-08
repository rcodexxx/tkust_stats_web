# your_project/app/services/match_service.py
from flask import current_app
from sqlalchemy.orm import joinedload

from .rating_service import RatingService  # 導入評分服務
from ..extensions import db
from ..models import Match, MatchRecord  # 導入 Match 和 MatchRecord
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
        創建一個新的比賽事件 (Match) 和比賽記錄 (MatchRecord)，並觸發評分更新。
        'data' 是經過 MatchRecordCreateSchema 驗證後的數據。
        """
        try:
            # 1. 創建 Match 物件，儲存比賽的元數據
            new_match = Match(
                match_date=data["match_date"],
                match_type=data["match_type"],
                match_format=data["match_format"],
                # 注意：您最新的 Match 模型沒有 notes，如果需要，請在 Match 模型中加入
                # notes=data.get('match_notes')
            )
            db.session.add(new_match)

            # 2. 創建 MatchRecord 物件，儲存參與者和賽果
            new_record = MatchRecord(
                match=new_match,  # 將其與上面創建的 Match 物件關聯
                player1_id=data["player1_id"],
                player2_id=data.get("player2_id"),
                player3_id=data["player3_id"],
                player4_id=data.get("player4_id"),
                a_games=data["a_games"],
                b_games=data["b_games"],
            )
            # 根據 a_games 和 b_games 計算 side_a_outcome
            new_record.side_a_outcome = MatchRecordService._calculate_outcome(new_record.a_games, new_record.b_games)
            db.session.add(new_record)

            # 3. 呼叫 RatingService 更新評分
            # RatingService 內部需要使用 player1_id, player2_id 等新欄位名
            RatingService.update_ratings_from_match(new_record)

            db.session.commit()
            return new_record

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"創建比賽記錄時出錯: {e}", exc_info=True)
            if isinstance(e, ValidationError):
                raise e
            raise AppException("創建比賽記錄時發生未預期錯誤。")

    @staticmethod
    def get_match_record_by_id(record_id: int):
        """根據 ID 獲取單場比賽記錄，並預先載入球員資訊。"""
        return MatchRecord.query.options(
            joinedload(MatchRecord.player1),
            joinedload(MatchRecord.player2),
            joinedload(MatchRecord.player3),
            joinedload(MatchRecord.player4),
            joinedload(MatchRecord.match),  # 預先載入關聯的 Match 事件
        ).get(record_id)

    @staticmethod
    def get_all_match_records(args: dict):
        """獲取比賽記錄列表。"""
        query = MatchRecord.query.order_by(MatchRecord.id.desc())  # 假設按 ID 降序
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
            # 刪除比賽記錄，關聯的 Match 事件也會因為 ondelete='CASCADE' 而被刪除
            db.session.delete(record)

            # 重新計算分數
            RatingService.recalculate_ratings_for_players(affected_player_ids)

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"刪除比賽記錄 ID {record.id} 時出錯: {e}", exc_info=True)
            raise AppException("刪除比賽記錄時發生未預期錯誤。")
