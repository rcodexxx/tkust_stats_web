# backend/app/services/match_service.py (完整修復版本)
from flask import current_app
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Match, MatchRecord
from ..models.enums.match_enums import MatchOutcomeEnum
from ..tools.exceptions import AppException, ValidationError
from .rating_service import RatingService  # 導入評分服務


class MatchRecordService:

    # 🔧 新增：分數驗證相關方法
    @staticmethod
    def _get_games_to_win(match_format: str) -> int:
        """根據比賽格式獲取獲勝所需的局數"""
        format_map = {
            'games_5': 3,
            'games_7': 4,
            'games_9': 5
        }
        return format_map.get(match_format, 5)

    @staticmethod
    def _validate_match_score(games_a: int, games_b: int, match_format: str) -> tuple[bool, str]:
        """
        驗證比賽分數是否符合規則
        返回: (是否有效, 錯誤訊息)
        """
        games_to_win = MatchRecordService._get_games_to_win(match_format)

        # 1. 基本驗證：分數不能為負數
        if games_a < 0 or games_b < 0:
            return False, "比賽分數不能為負數"

        # 2. 比賽必須有勝負
        if games_a == games_b:
            return False, "比賽分數不能相同，必須分出勝負"

        # 3. 必須有一方達到獲勝局數
        if games_a < games_to_win and games_b < games_to_win:
            return False, f"比賽尚未結束，需要有一方達到 {games_to_win} 局"

        # 4. 只能有一方達到獲勝局數
        if games_a >= games_to_win and games_b >= games_to_win:
            return False, f"無效分數：雙方都達到了獲勝局數 {games_to_win}"

        # 5. 達到獲勝局數的一方必須領先
        if games_a >= games_to_win and games_a <= games_b:
            return False, f"無效分數：A方達到 {games_to_win} 局但未領先"

        if games_b >= games_to_win and games_b <= games_a:
            return False, f"無效分數：B方達到 {games_to_win} 局但未領先"

        return True, ""

    @staticmethod
    def _calculate_outcome(games_a: int, games_b: int, match_format: str = None) -> MatchOutcomeEnum:
        """
        根據 A 方和 B 方的局數以及比賽格式計算 A 方的賽果
        修復版本：加入比賽格式驗證
        """
        # 如果提供了 match_format，先驗證分數有效性
        if match_format:
            is_valid, error_msg = MatchRecordService._validate_match_score(games_a, games_b, match_format)
            if not is_valid:
                raise ValidationError(f"比賽分數無效: {error_msg}")

            # 計算結果
            games_to_win = MatchRecordService._get_games_to_win(match_format)

            # A方獲勝的條件：達到獲勝局數且領先
            if games_a >= games_to_win and games_a > games_b:
                return MatchOutcomeEnum.WIN

            # B方獲勝的條件：達到獲勝局數且領先
            elif games_b >= games_to_win and games_b > games_a:
                return MatchOutcomeEnum.LOSS

            # 理論上不會到達這裡，因為前面已經驗證過
            else:
                raise ValidationError("無法確定比賽結果")
        else:
            # 向後相容：如果沒有提供 match_format，使用舊邏輯
            return MatchOutcomeEnum.WIN if games_a > games_b else MatchOutcomeEnum.LOSS

    @staticmethod
    def create_match_record(data: dict) -> MatchRecord:
        """
        創建一個新的比賽事件 (Match) 和比賽記錄 (MatchRecord)，並觸發評分更新。
        'data' 是經過 MatchRecordCreateSchema 驗證後的數據。
        🔧 修復：加入分數驗證邏輯
        """
        try:
            # 🔧 加入分數驗證
            is_valid, error_msg = MatchRecordService._validate_match_score(
                data["a_games"],
                data["b_games"],
                data["match_format"]
            )
            if not is_valid:
                raise ValidationError(error_msg)

            # 1. 創建 Match 物件，儲存比賽的元數據
            new_match = Match(
                match_date=data["match_date"],
                match_type=data["match_type"],
                match_format=data["match_format"],
                court_surface=data.get("court_surface"),
                court_environment=data.get("court_environment"),
                match_time_slot=data.get("time_slot"),
                total_points=data.get("total_points"),
                duration_minutes=data.get("duration_minutes"),
                youtube_url=data.get("youtube_url"),
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

            # 🔧 使用修復後的計算方法
            new_record.side_a_outcome = MatchRecordService._calculate_outcome(
                new_record.a_games,
                new_record.b_games,
                data["match_format"]
            )
            db.session.add(new_record)

            # 3. 提交變更並更新評分
            db.session.commit()

            # 4. 呼叫 RatingService 更新評分
            RatingService.update_ratings_from_match(new_record)

            db.session.commit()
            current_app.logger.info(f"成功創建比賽記錄 ID {new_record.id}")
            return new_record

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"創建比賽記錄時出錯: {e}", exc_info=True)
            if isinstance(e, (ValidationError, AppException)):
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
        """獲取比賽記錄列表，支援篩選、排序和分頁。"""
        query = MatchRecord.query.options(
            joinedload(MatchRecord.player1),
            joinedload(MatchRecord.player2),
            joinedload(MatchRecord.player3),
            joinedload(MatchRecord.player4),
            joinedload(MatchRecord.match),
        )

        # 應用篩選條件
        query = MatchRecordService._apply_filters(query, args)

        # 應用排序
        query = MatchRecordService._apply_sorting(query, args)

        # 應用分頁
        return MatchRecordService._apply_pagination(query, args)

    @staticmethod
    def _apply_filters(query, args: dict):
        """應用篩選條件到查詢中"""
        # 日期範圍篩選
        if start_date := args.get("start_date"):
            query = query.join(Match).filter(Match.match_date >= start_date)
        if end_date := args.get("end_date"):
            query = query.join(Match).filter(Match.match_date <= end_date)

        # 比賽類型篩選
        if match_type := args.get("match_type"):
            query = query.join(Match).filter(Match.match_type == match_type)
        if match_format := args.get("match_format"):
            query = query.join(Match).filter(Match.match_format == match_format)

        # 場地相關篩選
        if court_surface := args.get("court_surface"):
            query = query.join(Match).filter(Match.court_surface == court_surface)
        if court_environment := args.get("court_environment"):
            query = query.join(Match).filter(Match.court_environment == court_environment)
        if time_slot := args.get("time_slot"):
            query = query.join(Match).filter(Match.match_time_slot == time_slot)

        # 球員篩選
        if player_id := args.get("player_id"):
            query = query.filter(
                or_(
                    MatchRecord.player1_id == player_id,
                    MatchRecord.player2_id == player_id,
                    MatchRecord.player3_id == player_id,
                    MatchRecord.player4_id == player_id,
                )
            )

        return query

    @staticmethod
    def _apply_sorting(query, args: dict):
        """應用排序到查詢中"""
        sort_by = args.get("sort_by", "match_date")
        sort_order = args.get("sort_order", "desc")

        # 定義可排序的欄位映射
        sortable_fields = {
            "match_date": Match.match_date,
            "id": MatchRecord.id,
            "total_games": (MatchRecord.a_games + MatchRecord.b_games),
        }

        if sort_by in sortable_fields:
            field = sortable_fields[sort_by]
            if sort_order.lower() == "asc":
                query = query.join(Match).order_by(asc(field))
            else:
                query = query.join(Match).order_by(desc(field))
        else:
            # 預設排序：按比賽日期降序
            query = query.join(Match).order_by(desc(Match.match_date))

        return query

    @staticmethod
    def _apply_pagination(query, args: dict):
        """應用分頁到查詢中"""
        try:
            page = int(args.get("page", 1))
            per_page = int(args.get("per_page", 20))

            # 限制 per_page 的範圍
            per_page = min(max(per_page, 1), 100)
            page = max(page, 1)

            # 使用 SQLAlchemy 的 paginate 方法
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            return {
                "items": pagination.items,
                "total": pagination.total,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            }
        except (ValueError, TypeError):
            # 如果分頁參數無效，返回所有結果
            items = query.all()
            return {
                "items": items,
                "total": len(items),
                "page": 1,
                "per_page": len(items),
                "pages": 1,
                "has_next": False,
                "has_prev": False,
            }

    @staticmethod
    def update_match_record(record_id: int, data: dict) -> MatchRecord:
        """
        更新比賽記錄
        🔧 修復：加入完整的分數驗證邏輯
        """
        record = MatchRecordService.get_match_record_by_id(record_id)
        if not record:
            raise AppException("找不到要更新的比賽記錄。", status_code=404)

        try:
            # 🔧 如果更新了分數，先驗證新分數的有效性
            new_a_games = data.get("a_games", record.a_games)
            new_b_games = data.get("b_games", record.b_games)
            new_match_format = data.get("match_format",
                                        record.match.match_format.value if record.match.match_format else "games_9")

            # 驗證分數
            is_valid, error_msg = MatchRecordService._validate_match_score(
                new_a_games,
                new_b_games,
                new_match_format
            )
            if not is_valid:
                raise ValidationError(error_msg)

            # 獲取更新前的球員ID（用於評分重新計算）
            old_player_ids = {
                record.player1_id, record.player2_id,
                record.player3_id, record.player4_id
            }
            old_player_ids.discard(None)

            # 🔧 更新 Match 相關欄位
            match = record.match
            if match:
                # Match 模型的直接欄位
                match_fields_mapping = {
                    "match_date": "match_date",
                    "match_type": "match_type",
                    "match_format": "match_format",
                    "court_surface": "court_surface",
                    "court_environment": "court_environment",
                    "time_slot": "match_time_slot",  # 注意：前端 time_slot 映射到 match_time_slot
                    "total_points": "total_points",
                    "duration_minutes": "duration_minutes",
                    "youtube_url": "youtube_url",
                    "match_notes": "notes",  # 🔧 重要：前端 match_notes 映射到 Match.notes
                }

                for request_field, model_field in match_fields_mapping.items():
                    if request_field in data:
                        setattr(match, model_field, data[request_field])

            # 🔧 更新 MatchRecord 相關欄位（球員和分數）
            record_fields = [
                "player1_id",
                "player2_id",
                "player3_id",
                "player4_id",
                "a_games",
                "b_games",
            ]

            for field in record_fields:
                if field in data:
                    setattr(record, field, data[field])

            # 🔧 重新計算比賽結果（使用修復後的方法）
            if "a_games" in data or "b_games" in data or "match_format" in data:
                record.side_a_outcome = MatchRecordService._calculate_outcome(
                    record.a_games,
                    record.b_games,
                    new_match_format
                )

            # 獲取更新後的球員ID
            new_player_ids = {
                record.player1_id, record.player2_id,
                record.player3_id, record.player4_id
            }
            new_player_ids.discard(None)

            # 合併所有受影響的球員
            affected_player_ids = list(old_player_ids.union(new_player_ids))

            # 提交更改
            db.session.commit()

            # 重新計算評分
            if affected_player_ids:
                RatingService.recalculate_ratings_for_players(affected_player_ids)

            db.session.commit()
            current_app.logger.info(f"成功更新比賽記錄 ID {record_id}")
            return record

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新比賽記錄 ID {record_id} 時出錯: {e}", exc_info=True)
            if isinstance(e, (ValidationError, AppException)):
                raise e
            raise AppException("更新比賽記錄時發生未預期錯誤。")

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
    def get_match_statistics(args: dict = None):
        """獲取比賽統計資訊"""
        try:
            query = MatchRecord.query.join(Match)

            # 如果有篩選條件，應用篩選
            if args:
                query = MatchRecordService._apply_filters(query, args)

            records = query.all()

            # 計算統計資訊
            total_matches = len(records)
            total_games = sum(record.total_games for record in records)
            avg_duration = None

            if records:
                durations = [
                    record.match.duration_minutes
                    for record in records
                    if record.match.duration_minutes
                ]
                if durations:
                    avg_duration = sum(durations) / len(durations)

            # 場地類型統計
            surface_stats = {}
            environment_stats = {}
            time_slot_stats = {}

            for record in records:
                match = record.match
                if match.court_surface:
                    surface_stats[match.court_surface.value] = (
                            surface_stats.get(match.court_surface.value, 0) + 1
                    )
                if match.court_environment:
                    environment_stats[match.court_environment.value] = (
                            environment_stats.get(match.court_environment.value, 0) + 1
                    )
                if match.match_time_slot:
                    time_slot_stats[match.match_time_slot.value] = (
                            time_slot_stats.get(match.match_time_slot.value, 0) + 1
                    )

            return {
                "total_matches": total_matches,
                "total_games": total_games,
                "average_duration_minutes": round(avg_duration, 1)
                if avg_duration
                else None,
                "court_surface_distribution": surface_stats,
                "court_environment_distribution": environment_stats,
                "time_slot_distribution": time_slot_stats,
            }

        except Exception as e:
            current_app.logger.error(f"獲取比賽統計時出錯: {e}", exc_info=True)
            raise AppException("獲取比賽統計時發生錯誤。")
