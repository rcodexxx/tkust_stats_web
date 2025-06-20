# backend/app/schemas/match_schemas.py
from marshmallow import Schema, ValidationError, fields, validate, validates_schema
from marshmallow_enum import EnumField

from ..models.enums.match_enums import (
    CourtEnvironmentEnum,
    CourtSurfaceEnum,
    MatchFormatEnum,
    MatchStartServeEnum,
    MatchTimeSlotEnum,
    MatchTypeEnum,
)


class MatchRecordCreateSchema(Schema):
    match_date = fields.Date(required=True)
    match_type = EnumField(MatchTypeEnum, by_value=True, required=True)
    match_format = EnumField(MatchFormatEnum, by_value=True, required=True)

    player1_id = fields.Int(required=True, validate=validate.Range(min=1))
    player2_id = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1)
    )
    player3_id = fields.Int(required=True, validate=validate.Range(min=1))
    player4_id = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1)
    )

    a_games = fields.Int(required=True, validate=validate.Range(min=0))
    b_games = fields.Int(required=True, validate=validate.Range(min=0))

    court_surface = EnumField(
        CourtSurfaceEnum, by_value=True, required=False, allow_none=True
    )
    court_environment = EnumField(
        CourtEnvironmentEnum, by_value=True, required=False, allow_none=True
    )
    time_slot = EnumField(
        MatchTimeSlotEnum, by_value=True, required=False, allow_none=True
    )
    total_points = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    duration_minutes = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=20, max=180)
    )
    youtube_url = fields.Url(required=False, allow_none=True)
    match_notes = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=500)
    )

    @validates_schema
    def validate_players_selection(self, data, **kwargs):
        match_type = data.get("match_type")
        if match_type == MatchTypeEnum.DOUBLES:
            if not all(
                [
                    data.get("player1_id"),
                    data.get("player2_id"),
                    data.get("player3_id"),
                    data.get("player4_id"),
                ]
            ):
                raise ValidationError("雙打模式下必須選擇4個球員。")
        elif match_type == MatchTypeEnum.SINGLES:
            if data.get("player2_id") or data.get("player4_id"):
                raise ValidationError("單打模式下只能選擇2個球員。")


class MatchRecordDetailedCreateSchema(MatchRecordCreateSchema):
    game1_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game1_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game2_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game2_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game3_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game3_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game4_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game4_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game5_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game5_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game6_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game6_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game7_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game7_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game8_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game8_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game9_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )
    game9_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0), load_default=0
    )

    first_serve_side = EnumField(
        MatchStartServeEnum, by_value=True, required=False, allow_none=True
    )

    @validates_schema
    def validate_detailed_scores_consistency(self, data, **kwargs):
        super().validate_players_selection(data, **kwargs)

        games_detail = []
        for game_num in range(1, 10):
            a_score = data.get(f"game{game_num}_a_score", 0) or 0
            b_score = data.get(f"game{game_num}_b_score", 0) or 0
            if a_score > 0 or b_score > 0:
                games_detail.append((a_score, b_score))

        if games_detail:
            calculated_a_games = sum(1 for a, b in games_detail if a > b)
            calculated_b_games = sum(1 for a, b in games_detail if b > a)

            total_a_games = data.get("a_games")
            total_b_games = data.get("b_games")

            if total_a_games is not None and total_a_games != calculated_a_games:
                raise ValidationError(
                    f"A方總局數({total_a_games})與詳細比分計算結果({calculated_a_games})不一致"
                )
            if total_b_games is not None and total_b_games != calculated_b_games:
                raise ValidationError(
                    f"B方總局數({total_b_games})與詳細比分計算結果({calculated_b_games})不一致"
                )


class MatchRecordUpdateSchema(Schema):
    match_date = fields.Date(required=False)
    match_type = EnumField(MatchTypeEnum, by_value=True, required=False)
    match_format = EnumField(MatchFormatEnum, by_value=True, required=False)

    player1_id = fields.Int(required=False, validate=validate.Range(min=1))
    player2_id = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1)
    )
    player3_id = fields.Int(required=False, validate=validate.Range(min=1))
    player4_id = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1)
    )

    a_games = fields.Int(required=False, validate=validate.Range(min=0))
    b_games = fields.Int(required=False, validate=validate.Range(min=0))

    court_surface = EnumField(
        CourtSurfaceEnum, by_value=True, required=False, allow_none=True
    )
    court_environment = EnumField(
        CourtEnvironmentEnum, by_value=True, required=False, allow_none=True
    )
    time_slot = EnumField(
        MatchTimeSlotEnum, by_value=True, required=False, allow_none=True
    )
    total_points = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    duration_minutes = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=20, max=180)
    )
    youtube_url = fields.Url(required=False, allow_none=True)
    match_notes = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=500)
    )


class MatchRecordDetailedUpdateSchema(MatchRecordUpdateSchema):
    game1_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game1_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game2_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game2_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game3_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game3_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game4_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game4_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game5_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game5_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game6_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game6_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game7_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game7_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game8_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game8_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game9_a_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )
    game9_b_score = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )

    first_serve_side = EnumField(
        MatchStartServeEnum, by_value=True, required=False, allow_none=True
    )


class MatchRecordResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    match_id = fields.Int(dump_only=True)

    match_date = fields.Date(attribute="match.match_date", dump_only=True)
    match_type = EnumField(
        MatchTypeEnum, by_value=True, attribute="match.match_type", dump_only=True
    )
    match_format = EnumField(
        MatchFormatEnum, by_value=True, attribute="match.match_format", dump_only=True
    )

    player1_id = fields.Int(dump_only=True)
    player2_id = fields.Int(dump_only=True)
    player3_id = fields.Int(dump_only=True)
    player4_id = fields.Int(dump_only=True)

    a_games = fields.Int(dump_only=True)
    b_games = fields.Int(dump_only=True)
    side_a_outcome = fields.Str(dump_only=True)

    court_surface = EnumField(
        CourtSurfaceEnum, by_value=True, attribute="match.court_surface", dump_only=True
    )
    court_environment = EnumField(
        CourtEnvironmentEnum,
        by_value=True,
        attribute="match.court_environment",
        dump_only=True,
    )
    time_slot = EnumField(
        MatchTimeSlotEnum,
        by_value=True,
        attribute="match.match_time_slot",
        dump_only=True,
    )
    total_points = fields.Int(attribute="match.total_points", dump_only=True)
    duration_minutes = fields.Int(attribute="match.duration_minutes", dump_only=True)
    youtube_url = fields.Str(attribute="match.youtube_url", dump_only=True)
    match_notes = fields.Str(attribute="match.notes", dump_only=True)


class MatchRecordDetailedResponseSchema(MatchRecordResponseSchema):
    game1_a_score = fields.Int(dump_only=True)
    game1_b_score = fields.Int(dump_only=True)
    game2_a_score = fields.Int(dump_only=True)
    game2_b_score = fields.Int(dump_only=True)
    game3_a_score = fields.Int(dump_only=True)
    game3_b_score = fields.Int(dump_only=True)
    game4_a_score = fields.Int(dump_only=True)
    game4_b_score = fields.Int(dump_only=True)
    game5_a_score = fields.Int(dump_only=True)
    game5_b_score = fields.Int(dump_only=True)
    game6_a_score = fields.Int(dump_only=True)
    game6_b_score = fields.Int(dump_only=True)
    game7_a_score = fields.Int(dump_only=True)
    game7_b_score = fields.Int(dump_only=True)
    game8_a_score = fields.Int(dump_only=True)
    game8_b_score = fields.Int(dump_only=True)
    game9_a_score = fields.Int(dump_only=True)
    game9_b_score = fields.Int(dump_only=True)

    first_serve_side = EnumField(MatchStartServeEnum, by_value=True, dump_only=True)

    has_detailed_scores = fields.Method("get_has_detailed_scores", dump_only=True)
    games_detail = fields.Method("get_games_detail", dump_only=True)
    serve_advantage = fields.Method("get_serve_advantage", dump_only=True)

    def get_has_detailed_scores(self, obj):
        return obj.has_detailed_scores() if obj else False

    def get_games_detail(self, obj):
        return obj.get_all_games_scores_with_serve() if obj else []

    def get_serve_advantage(self, obj):
        if not obj or not obj.first_serve_side:
            return None
        return obj._calculate_serve_advantage()


class MatchQuerySchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    sort_by = fields.Str(
        load_default="match_date",
        validate=validate.OneOf(["match_date", "total_games", "id"]),
    )
    sort_order = fields.Str(
        load_default="desc", validate=validate.OneOf(["asc", "desc"])
    )

    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False)
    match_type = EnumField(MatchTypeEnum, by_value=True, required=False)
    match_format = EnumField(MatchFormatEnum, by_value=True, required=False)
    player_id = fields.Int(required=False, validate=validate.Range(min=1))

    all = fields.Bool(load_default=False)
