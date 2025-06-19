# backend/app/schemas/leaderboard_schemas.py

from marshmallow import Schema, fields, validate


class LeaderboardPlayerSchema(Schema):
    """排行榜球員資訊 Schema"""

    # 基本資訊
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    display_name = fields.Method("get_display_name", dump_only=True)
    short_display_name = fields.Method("get_short_display_name", dump_only=True)
    nickname = fields.Method("get_nickname", dump_only=True)

    # 組織資訊
    organization_id = fields.Int(dump_only=True, allow_none=True)
    organization_name = fields.Method("get_organization_name", dump_only=True)

    # 排名和分數
    rank = fields.Method("get_rank", dump_only=True)
    conservative_score = fields.Float(dump_only=True)
    official_rank_score = fields.Float(dump_only=True)
    score = fields.Float(dump_only=True)

    # TrueSkill 原始數據
    mu = fields.Float(dump_only=True)
    sigma = fields.Float(dump_only=True)

    # 四維度評分
    potential_skill = fields.Float(dump_only=True)
    consistency_rating = fields.Int(dump_only=True)
    experience_level = fields.Str(dump_only=True)
    rating_confidence = fields.Int(dump_only=True)

    # 比賽統計
    wins = fields.Method("get_wins", dump_only=True)
    losses = fields.Method("get_losses", dump_only=True)
    total_matches = fields.Method("get_total_matches", dump_only=True)
    win_rate = fields.Method("get_win_rate", dump_only=True)

    # 為前端相容性提供的別名 (但邏輯相同)
    _total_matches = fields.Method("get_total_matches", dump_only=True)
    _wins = fields.Method("get_wins", dump_only=True)
    _losses = fields.Method("get_losses", dump_only=True)

    # 其他資訊
    last_match_date = fields.Method("get_last_match_date", dump_only=True)
    is_active = fields.Method("get_is_active", dump_only=True)
    is_guest = fields.Bool(dump_only=True)
    is_experienced_player = fields.Bool(dump_only=True)
    player_type = fields.Method("get_player_type", dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    joined_date = fields.Date(dump_only=True)

    def get_display_name(self, obj):
        return obj.display_name if obj else None

    def get_short_display_name(self, obj):
        return obj.short_display_name if obj else None

    def get_nickname(self, obj):
        if obj and hasattr(obj, "user") and obj.user:
            return obj.user.display_name
        return None

    def get_organization_name(self, obj):
        if obj and hasattr(obj, "organization") and obj.organization:
            return obj.organization.short_name
        return None

    def get_is_active(self, obj):
        return obj.is_active if obj else False

    def get_player_type(self, obj):
        return obj.player_type if obj else None

    def get_rank(self, obj):
        return getattr(obj, "_rank", None)

    def get_wins(self, obj):
        return getattr(obj, "_wins", 0)

    def get_losses(self, obj):
        return getattr(obj, "_losses", 0)

    def get_total_matches(self, obj):
        return getattr(obj, "_total_matches", 0)

    def get_win_rate(self, obj):
        return getattr(obj, "_win_rate", 0.0)

    def get_last_match_date(self, obj):
        return getattr(obj, "_last_match_date", None)

    class Meta:
        ordered = True


class LeaderboardQuerySchema(Schema):
    """排行榜查詢參數 Schema"""

    # 基本篩選
    include_guests = fields.Bool(
        load_default=True, metadata={"description": "是否包含訪客"}
    )
    include_inactive = fields.Bool(
        load_default=False, metadata={"description": "是否包含非活躍成員"}
    )

    # 數量和分頁
    limit = fields.Int(
        validate=validate.Range(min=1, max=500),
        load_default=50,
        metadata={"description": "限制返回數量"},
    )
    page = fields.Int(
        load_default=1, validate=validate.Range(min=1), metadata={"description": "頁碼"}
    )
    per_page = fields.Int(
        load_default=50,
        validate=validate.Range(min=10, max=200),
        metadata={"description": "每頁數量"},
    )

    # 篩選條件
    organization_id = fields.Int(
        allow_none=True, metadata={"description": "篩選特定組織"}
    )
    organization_ids = fields.List(
        fields.Int(), allow_none=True, metadata={"description": "篩選多個組織"}
    )
    experience_level = fields.Str(
        allow_none=True,
        validate=validate.OneOf(["新手", "初級", "中級", "高級", "資深"]),
        metadata={"description": "篩選經驗等級"},
    )
    min_matches = fields.Int(
        load_default=0,
        validate=validate.Range(min=0),
        metadata={"description": "最少比賽場次"},
    )
    min_win_rate = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0, max=100),
        metadata={"description": "最低勝率"},
    )

    # 排序選項
    sort_by = fields.Str(
        load_default="score",
        validate=validate.OneOf(
            [
                "score",
                "win_rate",
                "total_matches",
                "wins",
                "experience",
                "recent_activity",
                "join_date",
            ]
        ),
        metadata={"description": "排序依據"},
    )
    sort_order = fields.Str(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
        metadata={"description": "排序方向"},
    )

    # 時間範圍
    active_since = fields.Date(
        allow_none=True, metadata={"description": "活躍時間起始"}
    )
    joined_after = fields.Date(
        allow_none=True, metadata={"description": "加入時間起始"}
    )


class PlayerComparisonSchema(Schema):
    """球員比較結果 Schema"""

    # 技能比較
    skill_advantage = fields.Float(
        dump_only=True, metadata={"description": "技術優勢分數"}
    )
    confidence_advantage = fields.Int(
        dump_only=True, metadata={"description": "可信度優勢"}
    )
    is_likely_stronger = fields.Bool(
        dump_only=True, metadata={"description": "是否可能更強"}
    )
    comparison_reliability = fields.Int(
        dump_only=True, metadata={"description": "比較可靠性 (0-100)"}
    )

    # 詳細比較數據
    score_difference = fields.Float(dump_only=True)
    mu_difference = fields.Float(dump_only=True)
    sigma_difference = fields.Float(dump_only=True)

    # 預測勝率
    predicted_win_probability = fields.Float(
        dump_only=True, metadata={"description": "預測勝率 (0-1)"}
    )


class LeaderboardStatisticsSchema(Schema):
    """排行榜統計資訊 Schema"""

    # 總體統計
    total_players = fields.Int(dump_only=True)
    total_members = fields.Int(dump_only=True)
    total_guests = fields.Int(dump_only=True)
    total_active_players = fields.Int(dump_only=True)
    total_matches = fields.Int(dump_only=True)

    # 平均數據
    average_matches_per_player = fields.Float(dump_only=True)

    # 更新時間
    last_updated = fields.DateTime(dump_only=True)
    data_freshness = fields.Str(dump_only=True)


class LeaderboardResponseSchema(Schema):
    """排行榜 API 響應 Schema"""

    message = fields.Str(dump_only=True)
    data = fields.Nested(LeaderboardPlayerSchema, many=True, dump_only=True)
    total = fields.Int(dump_only=True)
    page = fields.Int(dump_only=True)
    per_page = fields.Int(dump_only=True)
    total_pages = fields.Int(dump_only=True)
    statistics = fields.Nested(LeaderboardStatisticsSchema, dump_only=True)
    config = fields.Dict(dump_only=True)
    query_params = fields.Dict(dump_only=True)


class PlayerDetailSchema(Schema):
    """球員詳細資訊 Schema (用於排行榜詳情視圖)"""

    # 包含 LeaderboardPlayerSchema 的所有欄位
    player_info = fields.Nested(LeaderboardPlayerSchema, dump_only=True)

    # 額外的詳細統計
    match_history_summary = fields.Dict(dump_only=True)
    performance_trend = fields.List(fields.Dict(), dump_only=True)
    head_to_head_records = fields.List(fields.Dict(), dump_only=True)
    strengths_weaknesses = fields.Dict(dump_only=True)

    # 成就和里程碑
    achievements = fields.List(fields.Dict(), dump_only=True)
    milestones = fields.List(fields.Dict(), dump_only=True)
