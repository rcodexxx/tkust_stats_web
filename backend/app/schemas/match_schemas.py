# backend/app/schemas/match_schemas.py
from marshmallow import Schema, ValidationError, fields, validate, validates_schema
from marshmallow_enum import EnumField

# 假設您的 enums 和 models 在這些路徑
from ..models.enums.match_enums import (
    CourtEnvironmentEnum,
    CourtSurfaceEnum,
    MatchFormatEnum,
    MatchTimeSlotEnum,
    MatchTypeEnum,
)


# --- 用於巢狀顯示的簡潔 Schema ---
class SimpleMemberSchema(Schema):
    """僅序列化隊員的基礎資訊，用於比賽記錄的回應中。"""

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    # 顯示名稱優先使用 User model 上的 display_name，若無則用 Member 的 name
    display_name = fields.Method("get_display_name_from_user", dump_only=True)

    def get_display_name_from_user(self, obj):
        if obj and obj.user and obj.user.display_name:
            return obj.user.display_name
        elif obj and obj.name:
            return obj.name
        return None


# --- 創建比賽記錄的請求 Schema ---
class MatchRecordCreateSchema(Schema):
    match_date = fields.Date(required=True)

    # 比賽基本資訊
    match_type = EnumField(
        MatchTypeEnum,
        by_value=True,
        required=True,
        error_messages={"invalid": "無效的比賽類型。"},
    )
    match_format = EnumField(
        MatchFormatEnum,
        by_value=True,
        required=True,
        error_messages={"invalid": "無效的賽制。"},
    )

    # 場地相關欄位
    court_surface = EnumField(
        CourtSurfaceEnum,
        by_value=True,
        required=False,
        allow_none=True,
        error_messages={"invalid": "無效的場地材質。"},
    )
    court_environment = EnumField(
        CourtEnvironmentEnum,
        by_value=True,
        required=False,
        allow_none=True,
        error_messages={"invalid": "無效的場地環境。"},
    )
    time_slot = EnumField(
        MatchTimeSlotEnum,
        by_value=True,
        required=False,
        allow_none=True,
        error_messages={"invalid": "無效的比賽時間段。"},
    )

    # 比賽詳細資訊
    total_points = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0),
        metadata={"description": "總得分數"},
    )
    duration_minutes = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=20, max=60),
        metadata={"description": "比賽時長(分鐘)"},
    )
    youtube_url = fields.Url(
        required=False, allow_none=True, metadata={"description": "YouTube 影片連結"}
    )

    # 球員 ID (4個球員分別對應 A方1號、A方2號、B方1號、B方2號)
    player1_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "請選擇有效的A方1號球員。",
            "invalid": "球員ID必須是正整數。",
        },
    )
    player2_id = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
        error_messages={"invalid": "球員ID必須是正整數。"},
    )
    player3_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "請選擇有效的B方1號球員。",
            "invalid": "球員ID必須是正整數。",
        },
    )
    player4_id = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
        error_messages={"invalid": "球員ID必須是正整數。"},
    )

    # 比分資訊
    a_games = fields.Int(
        required=True,
        validate=validate.Range(min=0),
        error_messages={
            "required": "請輸入A方局數。",
            "invalid": "A方局數必須是非負整數。",
        },
    )
    b_games = fields.Int(
        required=True,
        validate=validate.Range(min=0),
        error_messages={
            "required": "請輸入B方局數。",
            "invalid": "B方局數必須是非負整數。",
        },
    )

    # 比賽備註
    match_notes = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=500)
    )

    @validates_schema
    def validate_players_selection(self, data, **kwargs):
        """驗證球員選擇的合理性"""
        match_type = data.get("match_type")

        # 驗證雙打模式下必須有4個球員
        if match_type == MatchTypeEnum.DOUBLES:
            if not all(
                [
                    data.get("player1_id"),
                    data.get("player2_id"),
                    data.get("player3_id"),
                    data.get("player4_id"),
                ]
            ):
                raise ValidationError(
                    "雙打模式下必須選擇4個球員。", field_name="_schema"
                )

        # 驗證單打模式下只能有2個球員
        elif match_type == MatchTypeEnum.SINGLES:
            if data.get("player2_id") or data.get("player4_id"):
                raise ValidationError(
                    "單打模式下只能選擇2個球員。", field_name="_schema"
                )

    @validates_schema
    def validate_duration_against_games(self, data, **kwargs):
        """驗證比賽時長與局數的合理性"""
        duration = data.get("duration_minutes")
        total_games = data.get("a_games", 0) + data.get("b_games", 0)

        if duration and total_games:
            # 粗略估算：每局約2-4分鐘
            min_expected = total_games * 2
            max_expected = total_games * 4

            if duration < min_expected or duration > max_expected:
                raise ValidationError(
                    f"比賽時長 ({duration}分鐘) 與總局數 ({total_games}局) 不太合理。"
                    f"建議時長範圍：{min_expected}-{max_expected}分鐘",
                    field_name="duration_minutes",
                )


# --- 顯示比賽記錄的回應 Schema ---
class MatchRecordResponseSchema(Schema):
    id = fields.Int(dump_only=True)

    # 比賽基本資訊 (從關聯的 Match 物件獲取)
    match_date = fields.Date(attribute="match.match_date", dump_only=True)
    match_type = EnumField(
        MatchTypeEnum, by_value=True, attribute="match.match_type", dump_only=True
    )
    match_format = EnumField(
        MatchFormatEnum, by_value=True, attribute="match.match_format", dump_only=True
    )

    # 場地相關資訊
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

    # 比賽詳細資訊
    total_points = fields.Int(attribute="match.total_points", dump_only=True)
    duration_minutes = fields.Int(attribute="match.duration_minutes", dump_only=True)
    youtube_url = fields.Str(attribute="match.youtube_url", dump_only=True)

    # 球員資訊（使用 SimpleMemberSchema）
    player1 = fields.Nested(SimpleMemberSchema, dump_only=True)
    player2 = fields.Nested(SimpleMemberSchema, dump_only=True, allow_none=True)
    player3 = fields.Nested(SimpleMemberSchema, dump_only=True)
    player4 = fields.Nested(SimpleMemberSchema, dump_only=True, allow_none=True)

    # 比分資訊
    a_games = fields.Int(dump_only=True)
    b_games = fields.Int(dump_only=True)
    total_games = fields.Method("get_total_games", dump_only=True)
    side_a_outcome = fields.Str(attribute="side_a_outcome.value", dump_only=True)

    # 比賽備註
    match_notes = fields.Str(dump_only=True, allow_none=True)

    def get_total_games(self, obj):
        """計算總局數"""
        return (obj.a_games or 0) + (obj.b_games or 0)

    class Meta:
        ordered = True


# --- 比賽統計查詢的 Schema ---
class MatchQuerySchema(Schema):
    """用於查詢比賽記錄的 Schema"""

    # 時間範圍
    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False)

    # 比賽類型篩選
    match_type = EnumField(MatchTypeEnum, by_value=True, required=False)
    match_format = EnumField(MatchFormatEnum, by_value=True, required=False)

    # 場地篩選
    court_surface = EnumField(CourtSurfaceEnum, by_value=True, required=False)
    court_environment = EnumField(CourtEnvironmentEnum, by_value=True, required=False)
    time_slot = EnumField(MatchTimeSlotEnum, by_value=True, required=False)

    # 球員篩選
    player_id = fields.Int(required=False)

    # 分頁
    page = fields.Int(required=False, validate=validate.Range(min=1), load_default=1)
    per_page = fields.Int(
        required=False, validate=validate.Range(min=1, max=100), load_default=20
    )

    # 排序
    sort_by = fields.Str(
        required=False,
        validate=validate.OneOf(["match_date", "duration_minutes", "total_games"]),
        load_default="match_date",
    )
    sort_order = fields.Str(
        required=False, validate=validate.OneOf(["asc", "desc"]), load_default="desc"
    )

    @validates_schema
    def validate_date_range(self, data, **kwargs):
        """驗證日期範圍"""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise ValidationError("開始日期不能晚於結束日期", field_name="start_date")


# --- 只顯示 Match 基本資訊的 Schema ---
class MatchBasicSchema(Schema):
    """用於顯示比賽基本資訊的簡化 Schema"""

    id = fields.Int(dump_only=True)
    match_date = fields.Date(dump_only=True)
    match_type = EnumField(MatchTypeEnum, by_value=True, dump_only=True)
    match_format = EnumField(MatchFormatEnum, by_value=True, dump_only=True)

    court_surface = EnumField(CourtSurfaceEnum, by_value=True, dump_only=True)
    court_environment = EnumField(CourtEnvironmentEnum, by_value=True, dump_only=True)
    time_slot = EnumField(
        MatchTimeSlotEnum, by_value=True, attribute="match_time_slot", dump_only=True
    )

    total_points = fields.Int(dump_only=True)
    duration_minutes = fields.Int(dump_only=True)
    youtube_url = fields.Str(dump_only=True)

    notes = fields.Str(dump_only=True)

    class Meta:
        ordered = True


# --- 更新比賽記錄的 Schema ---
class MatchUpdateSchema(Schema):
    """用於更新比賽資訊的 Schema"""

    # Match 相關欄位
    match_date = fields.Date(required=False)
    match_type = EnumField(MatchTypeEnum, by_value=True, required=False)
    match_format = EnumField(MatchFormatEnum, by_value=True, required=False)

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
        required=False, allow_none=True, validate=validate.Range(min=20, max=60)
    )
    youtube_url = fields.Url(required=False, allow_none=True)

    # MatchRecord 相關欄位
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

    match_notes = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=500)
    )

    @validates_schema
    def validate_players_selection(self, data, **kwargs):
        """驗證球員選擇的合理性"""
        match_type = data.get("match_type")

        # 只有在提供 match_type 時才進行驗證
        if match_type:
            # 驗證雙打模式下必須有4個球員
            if match_type == MatchTypeEnum.DOUBLES:
                required_players = [
                    "player1_id",
                    "player2_id",
                    "player3_id",
                    "player4_id",
                ]
                for player_field in required_players:
                    if player_field in data and not data.get(player_field):
                        raise ValidationError(
                            "雙打模式下必須選擇4個球員。", field_name="_schema"
                        )

            # 驗證單打模式下只能有2個球員
            elif match_type == MatchTypeEnum.SINGLES:
                if (data.get("player2_id") is not None) or (
                    data.get("player4_id") is not None
                ):
                    raise ValidationError(
                        "單打模式下只能選擇2個球員。", field_name="_schema"
                    )

    @validates_schema
    def validate_duration_against_games(self, data, **kwargs):
        """驗證比賽時長與局數的合理性"""
        duration = data.get("duration_minutes")
        a_games = data.get("a_games")
        b_games = data.get("b_games")

        if duration and a_games is not None and b_games is not None:
            total_games = a_games + b_games
            # 粗略估算：每局約2-4分鐘
            min_expected = total_games * 2
            max_expected = total_games * 4

            if duration < min_expected or duration > max_expected:
                raise ValidationError(
                    f"比賽時長 ({duration}分鐘) 與總局數 ({total_games}局) 不太合理。"
                    f"建議時長範圍：{min_expected}-{max_expected}分鐘",
                    field_name="duration_minutes",
                )
