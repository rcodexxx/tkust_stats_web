# backend/app/schemas/member_schemas.py
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    validate,
    validates_schema,
)
from marshmallow_enum import EnumField

from ..models.enums import GuestRoleEnum, UserRoleEnum
from ..models.enums.bio_enums import BloodTypeEnum, GenderEnum
from ..models.enums.match_enums import MatchPositionEnum


# --- 四維度評分專用 Schema ---
class FourDimensionScoreSchema(Schema):
    """四維度評分 Schema"""

    official_rank = fields.Float(
        dump_only=True, metadata={"description": "官方排名分數"}
    )
    potential_skill = fields.Float(dump_only=True, metadata={"description": "潛在實力"})
    consistency = fields.Int(dump_only=True, metadata={"description": "穩定度 (0-100)"})
    experience_level = fields.Str(dump_only=True, metadata={"description": "經驗等級"})
    rating_confidence = fields.Int(
        dump_only=True, metadata={"description": "評分可信度 (0-100)"}
    )


class RatingSummarySchema(Schema):
    """評分摘要 Schema"""

    official_score = fields.Float(dump_only=True, metadata={"description": "官方分數"})
    raw_mu = fields.Float(dump_only=True, metadata={"description": "原始 μ 值"})
    raw_sigma = fields.Float(dump_only=True, metadata={"description": "原始 σ 值"})
    stability_rating = fields.Int(
        dump_only=True, metadata={"description": "穩定度評分"}
    )
    experience_level = fields.Str(dump_only=True, metadata={"description": "經驗等級"})
    confidence = fields.Int(dump_only=True, metadata={"description": "評分可信度"})
    is_experienced = fields.Bool(
        dump_only=True, metadata={"description": "是否為有經驗球員"}
    )


# --- 巢狀 Schema ---
class SimpleOrganizationSchema(Schema):
    """僅序列化組織的基礎資訊"""

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    short_name = fields.Str(dump_only=True)


class SimpleRacketSchema(Schema):
    """僅序列化球拍的基礎資訊"""

    id = fields.Int(dump_only=True)
    brand = fields.Str(dump_only=True)
    model_name = fields.Str(dump_only=True)


class SimpleUserSchema(Schema):
    """僅序列化使用者的基礎資訊"""

    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    display_name = fields.Str(dump_only=True)
    role = EnumField(UserRoleEnum, by_value=True, dump_only=True)
    is_active = fields.Bool(dump_only=True)


class CreatorInfoSchema(Schema):
    """訪客創建者資訊"""

    username = fields.Str(dump_only=True)
    display_name = fields.Str(dump_only=True)


# --- 主要的 Member Schema ---
class MemberSchema(Schema):
    """完整的 Member Schema，已整合四維度評分系統"""

    # 基本資訊
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    display_name = fields.Method("get_display_name", dump_only=True)
    short_display_name = fields.Method("get_short_display_name", dump_only=True)
    student_id = fields.Str(dump_only=True, allow_none=True)

    # Bio 資訊
    gender = EnumField(GenderEnum, by_value=True, dump_only=True, allow_none=True)
    blood_type = EnumField(
        BloodTypeEnum, by_value=True, dump_only=True, allow_none=True
    )
    position = EnumField(
        MatchPositionEnum, by_value=True, dump_only=True, allow_none=True
    )

    # 狀態資訊
    is_active = fields.Method("get_is_active", dump_only=True)
    player_type = fields.Method("get_player_type", dump_only=True)
    joined_date = fields.Date(dump_only=True, allow_none=True)
    leaved_date = fields.Date(dump_only=True, allow_none=True)

    # === 四維度評分系統 ===
    # 主要評分
    official_rank_score = fields.Float(
        dump_only=True, metadata={"description": "官方排名分數 (主要排序依據)"}
    )
    conservative_score = fields.Float(
        dump_only=True, metadata={"description": "保守評分"}
    )
    potential_skill = fields.Float(
        dump_only=True, metadata={"description": "潛在實力 (μ值)"}
    )
    consistency_rating = fields.Int(
        dump_only=True, metadata={"description": "穩定度評分 (0-100)"}
    )
    experience_level = fields.Str(dump_only=True, metadata={"description": "經驗等級"})
    rating_confidence = fields.Int(
        dump_only=True, metadata={"description": "評分可信度 (0-100)"}
    )
    is_experienced_player = fields.Bool(
        dump_only=True, metadata={"description": "是否為有經驗球員"}
    )

    # 原始 TrueSkill 數據
    mu = fields.Float(dump_only=True, metadata={"description": "TrueSkill μ 值"})
    sigma = fields.Float(dump_only=True, metadata={"description": "TrueSkill σ 值"})
    score = fields.Float(
        dump_only=True, metadata={"description": "傳統評分 (向後兼容)"}
    )

    # 結構化的四維度數據
    four_dimensions = fields.Nested(FourDimensionScoreSchema, dump_only=True)
    rating_summary = fields.Nested(RatingSummarySchema, dump_only=True)

    # 訪客相關資訊
    is_guest = fields.Bool(dump_only=True)
    guest_phone = fields.Str(dump_only=True, allow_none=True)
    guest_role = fields.Str(dump_only=True, allow_none=True)
    guest_role_display = fields.Method("get_guest_role_display", dump_only=True)
    usage_count = fields.Int(dump_only=True, allow_none=True)
    last_used_at = fields.DateTime(dump_only=True, allow_none=True)

    # 關聯資訊
    organization = fields.Nested(
        SimpleOrganizationSchema, dump_only=True, allow_none=True
    )
    racket = fields.Nested(SimpleRacketSchema, dump_only=True, allow_none=True)
    user = fields.Nested(SimpleUserSchema, dump_only=True, allow_none=True)

    total_matches = fields.Method("get_total_matches", dump_only=True)

    # 備註
    notes = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)

    def get_display_name(self, obj):
        return obj.display_name if obj else None

    def get_short_display_name(self, obj):
        return obj.short_display_name if obj else None

    def get_is_active(self, obj):
        return obj.is_active if obj else False

    def get_player_type(self, obj):
        return obj.player_type if obj else None

    def get_guest_role_display(self, obj):
        if obj and obj.is_guest:
            return obj.get_guest_role_display()
        return None

    def get_total_matches(self, obj):
        """獲取正確的總比賽場次"""
        # 優先使用計算出的場次
        if hasattr(obj, "_calculated_match_count"):
            return obj._calculated_match_count

        # 如果沒有計算值，實時計算
        try:
            from sqlalchemy import or_

            from ..models import MatchRecord

            count = (
                db.session.query(MatchRecord)
                .filter(
                    or_(
                        MatchRecord.player1_id == obj.id,
                        MatchRecord.player2_id == obj.id,
                        MatchRecord.player3_id == obj.id,
                        MatchRecord.player4_id == obj.id,
                    )
                )
                .count()
            )

            return count
        except Exception:
            # 最後備用方案
            if obj and hasattr(obj, "match_stats_records"):
                return obj.match_stats_records.count()
            return 0

    class Meta:
        ordered = True


# --- 創建 Schema ---
class MemberCreateSchema(Schema):
    """創建正式會員的 Schema"""

    # User 帳號資訊
    username = fields.Str(
        required=True,
        validate=validate.Regexp(r"^09\d{8}$", error="手機號碼格式無效。"),
    )
    email = fields.Email(required=False, allow_none=True)
    password = fields.Str(
        required=False, allow_none=True, load_only=True, validate=validate.Length(min=6)
    )
    display_name = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=50)
    )
    role = EnumField(UserRoleEnum, by_value=True, required=True)

    # Member 基本資訊
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    student_id = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=20)
    )

    # Bio 資訊
    gender = EnumField(GenderEnum, by_value=True, required=False, allow_none=True)
    blood_type = EnumField(
        BloodTypeEnum, by_value=True, required=False, allow_none=True
    )
    position = EnumField(
        MatchPositionEnum, by_value=True, required=False, allow_none=True
    )

    # 關聯 ID
    organization_id = fields.Int(required=False, allow_none=True)
    racket_id = fields.Int(required=False, allow_none=True)

    # 隊籍資訊
    joined_date = fields.Date(required=False, allow_none=True)

    # TrueSkill（通常使用預設值）
    mu = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0))
    sigma = fields.Float(
        required=False, allow_none=True, validate=validate.Range(min=0)
    )

    # 備註
    notes = fields.Str(required=False, allow_none=True)

    # 狀態
    is_active = fields.Bool(required=False, allow_none=True, load_default=True)

    class Meta:
        unknown = EXCLUDE


class GuestPlayerCreateSchema(Schema):
    """創建訪客球員的 Schema"""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    phone = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=20)
    )
    notes = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=200)
    )

    class Meta:
        unknown = EXCLUDE


class MemberUpdateSchema(Schema):
    """更新會員資訊的 Schema"""

    # 可更新的基本資訊
    name = fields.Str(required=False, validate=validate.Length(min=1, max=80))
    student_id = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=20)
    )

    # Bio 資訊
    gender = EnumField(GenderEnum, by_value=True, required=False, allow_none=True)
    blood_type = EnumField(
        BloodTypeEnum, by_value=True, required=False, allow_none=True
    )
    position = EnumField(
        MatchPositionEnum, by_value=True, required=False, allow_none=True
    )

    # 關聯 ID
    organization_id = fields.Int(required=False, allow_none=True)
    racket_id = fields.Int(required=False, allow_none=True)

    # 隊籍資訊
    joined_date = fields.Date(required=False, allow_none=True)
    leaved_date = fields.Date(required=False, allow_none=True)

    # 備註
    notes = fields.Str(required=False, allow_none=True)

    # User 相關（如果有對應的 User）
    user_display_name = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=50)
    )
    user_email = fields.Email(required=False, allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_dates(self, data, **kwargs):
        """驗證日期邏輯"""
        joined_date = data.get("joined_date")
        leaved_date = data.get("leaved_date")

        if joined_date and leaved_date and leaved_date <= joined_date:
            raise ValidationError("離隊日期必須晚於入隊日期")


class GuestPromotionSchema(Schema):
    """訪客升級為正式會員的 Schema"""

    # 必要的 User 帳號資訊
    username = fields.Str(
        required=True,
        validate=validate.Regexp(r"^09\d{8}$", error="手機號碼格式無效。"),
    )
    password = fields.Str(
        required=True, load_only=True, validate=validate.Length(min=6)
    )

    # 可選的資訊
    email = fields.Email(required=False, allow_none=True)
    display_name = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=50)
    )
    role = EnumField(
        UserRoleEnum, by_value=True, required=False, load_default=UserRoleEnum.MEMBER
    )

    # 可選的會員資訊更新
    student_id = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=20)
    )
    organization_id = fields.Int(required=False, allow_none=True)

    class Meta:
        unknown = EXCLUDE


# --- 搜尋和篩選 Schema ---
class MemberQuerySchema(Schema):
    """會員查詢參數 Schema"""

    # 基本篩選
    all = fields.Str(required=False, validate=validate.OneOf(["true", "false"]))
    name = fields.Str(required=False)
    include_guests = fields.Str(
        required=False, validate=validate.OneOf(["true", "false"])
    )
    active_only = fields.Str(required=False, validate=validate.OneOf(["true", "false"]))

    # 分頁
    page = fields.Int(required=False, validate=validate.Range(min=1), load_default=1)
    per_page = fields.Int(
        required=False, validate=validate.Range(min=1, max=100), load_default=20
    )

    # 排序
    sort_by = fields.Str(
        required=False,
        validate=validate.OneOf(["name", "score", "joined_date", "created_at"]),
        load_default="name",
    )
    sort_order = fields.Str(
        required=False, validate=validate.OneOf(["asc", "desc"]), load_default="asc"
    )

    # 類型篩選
    player_type = fields.Str(
        required=False, validate=validate.OneOf(["member", "guest", "all"])
    )

    # 組織篩選
    organization_id = fields.Int(required=False)

    class Meta:
        unknown = EXCLUDE


# --- 響應 Schema ---
class MemberListResponseSchema(Schema):
    """會員列表響應 Schema"""

    success = fields.Bool(dump_only=True)
    data = fields.Nested(MemberSchema, many=True, dump_only=True)
    total = fields.Int(dump_only=True)
    pagination = fields.Dict(dump_only=True, allow_none=True)

    class Meta:
        ordered = True


class MemberDetailResponseSchema(Schema):
    """會員詳情響應 Schema"""

    success = fields.Bool(dump_only=True)
    data = fields.Nested(MemberSchema, dump_only=True)
    message = fields.Str(dump_only=True, allow_none=True)

    class Meta:
        ordered = True


# 創建新的訪客創建 Schema：
class GuestCreateSchema(Schema):
    """創建訪客的請求 Schema"""

    # 基本資訊
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=20),
        metadata={"description": "訪客姓名"},
    )
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(r"^[0-9\-+\s()]*$", error="請輸入有效的電話號碼"),
        metadata={"description": "聯絡電話"},
    )

    # 身份和歸屬
    guest_role = EnumField(
        GuestRoleEnum,
        by_value=True,
        required=False,
        load_default=GuestRoleEnum.NEUTRAL,
        metadata={"description": "訪客身份類型"},
    )
    organization_id = fields.Int(
        required=False, allow_none=True, metadata={"description": "所屬組織ID"}
    )

    # 備註
    notes = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=200),
        metadata={"description": "備註說明"},
    )

    class Meta:
        unknown = EXCLUDE


# 訪客更新 Schema：
class GuestUpdateSchema(Schema):
    """更新訪客資訊的請求 Schema"""

    name = fields.Str(required=False, validate=validate.Length(min=2, max=20))
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(r"^[0-9\-+\s()]*$", error="請輸入有效的電話號碼"),
    )
    guest_role = EnumField(GuestRoleEnum, by_value=True, required=False)
    organization_id = fields.Int(required=False, allow_none=True)
    notes = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=200)
    )

    class Meta:
        unknown = EXCLUDE


# 訪客查詢 Schema（用於搜尋我的訪客）：
class GuestQuerySchema(Schema):
    """訪客查詢參數 Schema"""

    q = fields.Str(required=False, metadata={"description": "搜尋關鍵字"})
    guest_role = EnumField(GuestRoleEnum, by_value=True, required=False)
    organization_id = fields.Int(required=False)
    limit = fields.Int(
        required=False, validate=validate.Range(min=1, max=50), load_default=10
    )

    class Meta:
        unknown = EXCLUDE


# 訪客選項 Schema（用於前端選擇器）：
class GuestRoleOptionSchema(Schema):
    """訪客身份選項 Schema"""

    value = fields.Str(dump_only=True)
    label = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)


# 響應 Schema：
class GuestCreateResponseSchema(Schema):
    """創建訪客響應 Schema"""

    success = fields.Bool(dump_only=True)
    message = fields.Str(dump_only=True)
    member = fields.Nested(MemberSchema, dump_only=True)

    class Meta:
        ordered = True


class GuestListResponseSchema(Schema):
    """訪客列表響應 Schema"""

    success = fields.Bool(dump_only=True)
    guests = fields.Nested(MemberSchema, many=True, dump_only=True)
    total = fields.Int(dump_only=True)

    class Meta:
        ordered = True
