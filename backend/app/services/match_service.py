# your_project/app/services/match_service.py
from flask import current_app
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Match, MatchRecord, Member  # 導入 Match 和 MatchRecord
from ..models.enums.match_enums import MatchOutcomeEnum
from ..tools.exceptions import AppException, ValidationError
from .rating_service import RatingService  # 導入評分服務


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
            new_record.side_a_outcome = MatchRecordService._calculate_outcome(
                new_record.a_games, new_record.b_games
            )
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
            p_id
            for p_id in [
                record.player1_id,
                record.player2_id,
                record.player3_id,
                record.player4_id,
            ]
            if p_id
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
            current_app.logger.error(
                f"刪除比賽記錄 ID {record.id} 時出錯: {e}", exc_info=True
            )
            raise AppException("刪除比賽記錄時發生未預期錯誤。")

    @staticmethod
    def search_match_records(filters: dict, page: int = 1, per_page: int = 15):
        """
        根據篩選條件搜尋比賽記錄
        """
        try:
            # 基礎查詢，包含預載入
            query = MatchRecord.query.options(
                joinedload(MatchRecord.player1).joinedload(Member.organization),
                joinedload(MatchRecord.player2).joinedload(Member.organization),
                joinedload(MatchRecord.player3).joinedload(Member.organization),
                joinedload(MatchRecord.player4).joinedload(Member.organization),
                joinedload(MatchRecord.match),
            )

            # 球員篩選
            if filters.get("player_ids"):
                player_ids = filters["player_ids"]
                # 搜尋任何一個位置包含這些球員的比賽
                player_conditions = or_(
                    MatchRecord.player1_id.in_(player_ids),
                    MatchRecord.player2_id.in_(player_ids),
                    MatchRecord.player3_id.in_(player_ids),
                    MatchRecord.player4_id.in_(player_ids),
                )
                query = query.filter(player_conditions)

            # 位置篩選（需要與球員ID一起使用）
            if filters.get("player_position") and filters.get("player_ids"):
                position = filters["player_position"]
                player_ids = filters["player_ids"]

                if position == "front":
                    # 前排位置（player1 和 player3）
                    position_conditions = or_(
                        MatchRecord.player1_id.in_(player_ids),
                        MatchRecord.player3_id.in_(player_ids),
                    )
                elif position == "back":
                    # 後排位置（player2 和 player4）
                    position_conditions = or_(
                        MatchRecord.player2_id.in_(player_ids),
                        MatchRecord.player4_id.in_(player_ids),
                    )
                else:  # any position
                    position_conditions = or_(
                        MatchRecord.player1_id.in_(player_ids),
                        MatchRecord.player2_id.in_(player_ids),
                        MatchRecord.player3_id.in_(player_ids),
                        MatchRecord.player4_id.in_(player_ids),
                    )
                query = query.filter(position_conditions)

            # 比賽類型篩選（通過關聯的 Match 表）
            if filters.get("match_type"):
                query = query.join(Match).filter(
                    Match.match_type == filters["match_type"]
                )

            # 賽制篩選
            if filters.get("match_format"):
                query = query.join(Match).filter(
                    Match.match_format == filters["match_format"]
                )

            # 勝方篩選
            if filters.get("winner_side"):
                if filters["winner_side"] == "A":
                    query = query.filter(
                        MatchRecord.side_a_outcome == MatchOutcomeEnum.WIN
                    )
                elif filters["winner_side"] == "B":
                    query = query.filter(
                        MatchRecord.side_a_outcome == MatchOutcomeEnum.LOSS
                    )

            # 日期範圍篩選
            if filters.get("date_from"):
                query = query.join(Match).filter(
                    Match.match_date >= filters["date_from"]
                )

            if filters.get("date_to"):
                query = query.join(Match).filter(Match.match_date <= filters["date_to"])

            # 分數差距篩選
            if filters.get("min_score_diff") is not None:
                score_diff = func.abs(MatchRecord.a_games - MatchRecord.b_games)
                query = query.filter(score_diff >= filters["min_score_diff"])

            if filters.get("max_score_diff") is not None:
                score_diff = func.abs(MatchRecord.a_games - MatchRecord.b_games)
                query = query.filter(score_diff <= filters["max_score_diff"])

            # 排序（最新的在前）
            query = query.join(Match).order_by(
                Match.match_date.desc(), MatchRecord.id.desc()
            )

            # 分頁
            paginated_result = query.paginate(
                page=page, per_page=per_page, error_out=False
            )

            return {
                "records": paginated_result.items,
                "total": paginated_result.total,
                "pages": paginated_result.pages,
                "current_page": paginated_result.page,
                "per_page": paginated_result.per_page,
                "has_next": paginated_result.has_next,
                "has_prev": paginated_result.has_prev,
            }

        except Exception as e:
            current_app.logger.error(f"搜尋比賽記錄時出錯: {e}", exc_info=True)
            raise AppException("搜尋比賽記錄時發生錯誤。")
