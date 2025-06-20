# backend/app/services/match_service.py
from flask import current_app
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Match, MatchRecord
from ..models.enums.match_enums import MatchOutcomeEnum, MatchStartServeEnum
from ..tools.exceptions import AppException, ValidationError
from .rating_service import RatingService


class MatchRecordService:
    @staticmethod
    def _calculate_outcome(games_a: int, games_b: int) -> MatchOutcomeEnum:
        return MatchOutcomeEnum.WIN if games_a > games_b else MatchOutcomeEnum.LOSS

    @staticmethod
    def create_match_record(data: dict) -> MatchRecord:
        try:
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
                notes=data.get("match_notes"),
            )
            db.session.add(new_match)

            new_record = MatchRecord(
                match=new_match,
                player1_id=data["player1_id"],
                player2_id=data.get("player2_id"),
                player3_id=data["player3_id"],
                player4_id=data.get("player4_id"),
                a_games=data["a_games"],
                b_games=data["b_games"],
            )
            new_record.side_a_outcome = MatchRecordService._calculate_outcome(
                new_record.a_games, new_record.b_games
            )
            db.session.add(new_record)

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
    def create_match_record_detailed(data: dict) -> MatchRecord:
        try:
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
                notes=data.get("match_notes"),
            )
            db.session.add(new_match)

            new_record = MatchRecord(
                match=new_match,
                player1_id=data["player1_id"],
                player2_id=data.get("player2_id"),
                player3_id=data["player3_id"],
                player4_id=data.get("player4_id"),
                a_games=data["a_games"],
                b_games=data["b_games"],
            )

            MatchRecordService._set_detailed_scores(new_record, data)
            MatchRecordService._set_serve_tracking(new_record, data)

            if MatchRecordService._has_any_detailed_scores(data):
                new_record.update_games_total()

            new_record.side_a_outcome = MatchRecordService._calculate_outcome(
                new_record.a_games, new_record.b_games
            )

            db.session.add(new_record)
            RatingService.update_ratings_from_match(new_record)
            db.session.commit()
            return new_record

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"創建詳細比賽記錄時出錯: {e}", exc_info=True)
            if isinstance(e, ValidationError):
                raise e
            raise AppException("創建比賽記錄時發生未預期錯誤。")

    @staticmethod
    def get_match_record_by_id(record_id: int):
        return MatchRecord.query.options(
            joinedload(MatchRecord.player1),
            joinedload(MatchRecord.player2),
            joinedload(MatchRecord.player3),
            joinedload(MatchRecord.player4),
            joinedload(MatchRecord.match),
        ).get(record_id)

    @staticmethod
    def get_all_match_records(args: dict):
        query = MatchRecord.query.options(
            joinedload(MatchRecord.player1),
            joinedload(MatchRecord.player2),
            joinedload(MatchRecord.player3),
            joinedload(MatchRecord.player4),
            joinedload(MatchRecord.match),
        )

        query = MatchRecordService._apply_filters(query, args)
        query = MatchRecordService._apply_sorting(query, args)
        return MatchRecordService._apply_pagination(query, args)

    @staticmethod
    def update_match_record(record_id: int, data: dict) -> MatchRecord:
        record = MatchRecordService.get_match_record_by_id(record_id)
        if not record:
            raise AppException("找不到要更新的比賽記錄。", status_code=404)

        try:
            if record.match:
                match_fields_mapping = {
                    "court_surface": "court_surface",
                    "court_environment": "court_environment",
                    "time_slot": "match_time_slot",
                    "total_points": "total_points",
                    "duration_minutes": "duration_minutes",
                    "youtube_url": "youtube_url",
                    "match_notes": "notes",
                }

                for request_field, model_field in match_fields_mapping.items():
                    if request_field in data:
                        setattr(record.match, model_field, data[request_field])

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

            if "a_games" in data or "b_games" in data:
                record.side_a_outcome = MatchRecordService._calculate_outcome(
                    record.a_games, record.b_games
                )

            MatchRecordService._handle_rating_updates(record, data)
            db.session.commit()
            return record

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新比賽記錄時出錯: {e}", exc_info=True)
            if isinstance(e, (ValidationError, AppException)):
                raise e
            raise AppException("更新比賽記錄時發生未預期錯誤。")

    @staticmethod
    def update_match_record_detailed(record_id: int, data: dict) -> MatchRecord:
        record = MatchRecordService.get_match_record_by_id(record_id)
        if not record:
            raise AppException("找不到要更新的比賽記錄。", status_code=404)

        try:
            if record.match:
                match_fields_mapping = {
                    "court_surface": "court_surface",
                    "court_environment": "court_environment",
                    "time_slot": "match_time_slot",
                    "total_points": "total_points",
                    "duration_minutes": "duration_minutes",
                    "youtube_url": "youtube_url",
                    "match_notes": "notes",
                }

                for request_field, model_field in match_fields_mapping.items():
                    if request_field in data:
                        setattr(record.match, model_field, data[request_field])

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

            MatchRecordService._set_detailed_scores(record, data)
            MatchRecordService._set_serve_tracking(record, data)

            if MatchRecordService._has_any_detailed_scores(data):
                record.update_games_total()

            if (
                "a_games" in data
                or "b_games" in data
                or MatchRecordService._has_any_detailed_scores(data)
            ):
                record.side_a_outcome = MatchRecordService._calculate_outcome(
                    record.a_games, record.b_games
                )

            MatchRecordService._handle_rating_updates(record, data)
            db.session.commit()
            return record

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新詳細比賽記錄時出錯: {e}", exc_info=True)
            if isinstance(e, (ValidationError, AppException)):
                raise e
            raise AppException("更新比賽記錄時發生未預期錯誤。")

    @staticmethod
    def delete_match_record(record: MatchRecord) -> bool:
        if not record:
            raise AppException("找不到要刪除的比賽記錄。", status_code=404)

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
            db.session.delete(record)
            RatingService.recalculate_ratings_for_players(affected_player_ids)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"刪除比賽記錄時出錯: {e}", exc_info=True)
            raise AppException("刪除比賽記錄時發生未預期錯誤。")

    @staticmethod
    def _apply_filters(query, args: dict):
        if start_date := args.get("start_date"):
            query = query.join(Match).filter(Match.match_date >= start_date)
        if end_date := args.get("end_date"):
            query = query.join(Match).filter(Match.match_date <= end_date)
        if match_type := args.get("match_type"):
            query = query.join(Match).filter(Match.match_type == match_type)
        if match_format := args.get("match_format"):
            query = query.join(Match).filter(Match.match_format == match_format)
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
        sort_by = args.get("sort_by", "match_date")
        sort_order = args.get("sort_order", "desc")

        if sort_by == "match_date":
            order_column = Match.match_date
            query = query.join(Match)
        elif sort_by == "total_games":
            order_column = MatchRecord.a_games + MatchRecord.b_games
        else:
            order_column = getattr(MatchRecord, sort_by, MatchRecord.id)

        if sort_order == "asc":
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))

        return query

    @staticmethod
    def _apply_pagination(query, args: dict):
        page = args.get("page", 1)
        per_page = min(args.get("per_page", 20), 100)

        if args.get("all", False):
            return query.all()

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
            "has_prev": pagination.has_prev,
            "has_next": pagination.has_next,
        }

    @staticmethod
    def _set_detailed_scores(record: MatchRecord, data: dict) -> None:
        score_fields = [
            "game1_a_score",
            "game1_b_score",
            "game2_a_score",
            "game2_b_score",
            "game3_a_score",
            "game3_b_score",
            "game4_a_score",
            "game4_b_score",
            "game5_a_score",
            "game5_b_score",
            "game6_a_score",
            "game6_b_score",
            "game7_a_score",
            "game7_b_score",
            "game8_a_score",
            "game8_b_score",
            "game9_a_score",
            "game9_b_score",
        ]

        for field in score_fields:
            if field in data:
                setattr(record, field, data[field] or 0)

    @staticmethod
    def _has_any_detailed_scores(data: dict) -> bool:
        score_fields = [
            "game1_a_score",
            "game1_b_score",
            "game2_a_score",
            "game2_b_score",
            "game3_a_score",
            "game3_b_score",
            "game4_a_score",
            "game4_b_score",
            "game5_a_score",
            "game5_b_score",
            "game6_a_score",
            "game6_b_score",
            "game7_a_score",
            "game7_b_score",
            "game8_a_score",
            "game8_b_score",
            "game9_a_score",
            "game9_b_score",
        ]

        return any(data.get(field, 0) > 0 for field in score_fields)

    @staticmethod
    def _set_serve_tracking(record: MatchRecord, data: dict) -> None:
        if "first_serve_side" in data:
            if data["first_serve_side"]:
                record.first_serve_side = MatchStartServeEnum(data["first_serve_side"])
            else:
                record.first_serve_side = None

    @staticmethod
    def _handle_rating_updates(record: MatchRecord, data: dict) -> None:
        player_fields_changed = any(
            field in data
            for field in ["player1_id", "player2_id", "player3_id", "player4_id"]
        )
        scores_changed = any(
            field in data for field in ["a_games", "b_games"]
        ) or MatchRecordService._has_any_detailed_scores(data)

        if player_fields_changed or scores_changed:
            affected_player_ids = []
            for field in ["player1_id", "player2_id", "player3_id", "player4_id"]:
                player_id = getattr(record, field, None)
                if player_id:
                    affected_player_ids.append(player_id)

            db.session.commit()

            if affected_player_ids:
                RatingService.recalculate_ratings_for_players(affected_player_ids)
