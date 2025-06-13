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

from ..models.enums import UserRoleEnum
from ..models.enums.bio_enums import BloodTypeEnum, GenderEnum
from ..models.enums.match_enums import MatchPositionEnum


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
    """完整的 Member Schema，支援正式會員和訪客"""

    # 基本資訊
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    display_name = fields.Method("get_display_name", dump_only=True)
    short_display_name = fields.Method("get_short_display_name", dump_only=True)
    student_id = fields.Str(dump_only=True, allow_none=True)

    # Bio 資訊
    gender = EnumField(GenderEnum, by_value=True, dump_only=True, allow_none=True)
    blood_type = EnumField(BloodTypeEnum, by_value=True, dump_only=True, allow_none=True)
    position = EnumField(MatchPositionEnum, by_value=True, dump_only=True, allow_none=True)

    # 狀態資訊
    is_active = fields.Method("get_is_active", dump_only=True)
    player_type = fields.Method("get_player_type", dump_only=True)
    joined_date = fields.Date(dump_only=True, allow_none=True)
    leaved_date = fields.Date(dump_only=True, allow_none=True)

    # TrueSkill 評分
    mu = fields.Float(dump_only=True)
    sigma = fields.Float(dump_only=True)
    score = fields.Int(dump_only=True)

    # 訪客相關資訊
    is_guest = fields.Bool(dump_only=True)
    guest_phone = fields.Str(dump_only=True, allow_none=True)
    guest_identifier = fields.Str(dump_only=True, allow_none=True)
    usage_count = fields.Int(dump_only=True, allow_none=True)
    last_used_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True, allow_none=True)

    # 關聯資訊
    organization = fields.Nested(SimpleOrganizationSchema, dump_only=True, allow_none=True)
    racket = fields.Nested(SimpleRacketSchema, dump_only=True, allow_none=True)
    user = fields.Nested(SimpleUserSchema, dump_only=True, allow_none=True)
    creator_info = fields.Nested(CreatorInfoSchema, dump_only=True, allow_none=True)

    # 備註
    notes = fields.Str(dump_only=True, allow_none=True)

    def get_display_name(self, obj):
        """獲取顯示名稱"""
        return obj.display_name

    def get_short_display_name(self, obj):
        """獲取短版顯示名稱"""
        return obj.short_display_name

    def get_is_active(self, obj):
        """獲取活躍狀態"""
        return obj.is_active

    def get_player_type(self, obj):
        """獲取球員類型"""
        return obj.player_type


# --- 排行榜專用 Schema ---
class LeaderboardMemberSchema(Schema):
    """排行榜專用的 Member Schema"""

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    display_name = fields.Method("get_display_name", dump_only=True)
    short_display_name = fields.Method("get_short_display_name", dump_only=True)
    score = fields.Int(dump_only=True)
    is_guest = fields.Bool(dump_only=True)
    player_type = fields.Method("get_player_type", dump_only=True)

    # 組織名稱
    organization_name = fields.Method("get_organization_display", dump_only=True)

    # 動態計算的統計數據（在 service 中附加）
    wins = fields.Int(dump_only=True, dump_default=0)
    losses = fields.Int(dump_only=True, dump_default=0)
    total_matches = fields.Int(dump_only=True, dump_default=0)
    win_rate = fields.Float(dump_only=True, dump_default=0.0)

    def get_display_name(self, obj):
        return obj.display_name

    def get_short_display_name(self, obj):
        return obj.short_display_name

    def get_player_type(self, obj):
        return obj.player_type

    def get_organization_display(self, obj):
        if obj.is_guest:
            return "訪客"
        elif obj.organization:
            return obj.organization.short_name or obj.organization.name
        return None


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
    student_id = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))

    # Bio 資訊
    gender = EnumField(GenderEnum, by_value=True, required=False, allow_none=True)
    blood_type = EnumField(BloodTypeEnum, by_value=True, required=False, allow_none=True)
    position = EnumField(MatchPositionEnum, by_value=True, required=False, allow_none=True)

    # 關聯 ID
    organization_id = fields.Int(required=False, allow_none=True)
    racket_id = fields.Int(required=False, allow_none=True)

    # 隊籍資訊
    joined_date = fields.Date(required=False, allow_none=True)

    # TrueSkill（通常使用預設值）
    mu = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0))
    sigma = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0))

    # 備註
    notes = fields.Str(required=False, allow_none=True)

    # 狀態
    is_active = fields.Bool(required=False, allow_none=True, load_default=True)

    class Meta:
        unknown = EXCLUDE


class GuestPlayerCreateSchema(Schema):
    """創建訪客球員的 Schema"""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))
    notes = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))

    class Meta:
        unknown = EXCLUDE


class MemberUpdateSchema(Schema):
    """更新會員資訊的 Schema"""

    # 可更新的基本資訊
    name = fields.Str(required=False, validate=validate.Length(min=1, max=80))
    student_id = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))

    # Bio 資訊
    gender = EnumField(GenderEnum, by_value=True, required=False, allow_none=True)
    blood_type = EnumField(BloodTypeEnum, by_value=True, required=False, allow_none=True)
    position = EnumField(MatchPositionEnum, by_value=True, required=False, allow_none=True)

    # 關聯 ID
    organization_id = fields.Int(required=False, allow_none=True)
    racket_id = fields.Int(required=False, allow_none=True)

    # 隊籍資訊
    joined_date = fields.Date(required=False, allow_none=True)
    leaved_date = fields.Date(required=False, allow_none=True)

    # 備註
    notes = fields.Str(required=False, allow_none=True)

    # User 相關（如果有對應的 User）
    user_display_name = fields.Str(required=False, allow_none=True, validate=validate.Length(max=50))
    user_email = fields.Email(required=False, allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_dates(self, data, **kwargs):
        """驗證日期邏輯"""
        joined_date = data.get('joined_date')
        leaved_date = data.get('leaved_date')

        if joined_date and leaved_date and leaved_date <= joined_date:
            raise ValidationError('離隊日期必須晚於入隊日期')


class GuestPromotionSchema(Schema):
    """訪客升級為正式會員的 Schema"""

    # 必要的 User 帳號資訊
    username = fields.Str(
        required=True,
        validate=validate.Regexp(r"^09\d{8}$", error="手機號碼格式無效。"),
    )
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6))

    # 可選的資訊
    email = fields.Email(required=False, allow_none=True)
    display_name = fields.Str(required=False, allow_none=True, validate=validate.Length(max=50))
    role = EnumField(UserRoleEnum, by_value=True, required=False, load_default=UserRoleEnum.MEMBER)

    # 可選的會員資訊更新
    student_id = fields.Str(required=False, allow_none=True, validate=validate.Length(max=20))
    organization_id = fields.Int(required=False, allow_none=True)

    class Meta:
        unknown = EXCLUDE


# --- 搜尋和篩選 Schema ---
class MemberQuerySchema(Schema):
    """會員查詢參數 Schema"""

    # 基本篩選
    all = fields.Str(required=False, validate=validate.OneOf(['true', 'false']))
    name = fields.Str(required=False)
    include_guests = fields.Str(required=False, validate=validate.OneOf(['true', 'false']))
    active_only = fields.Str(required=False, validate=validate.OneOf(['true', 'false']))

    # 分頁
    page = fields.Int(required=False, validate=validate.Range(min=1), load_default=1)
    per_page = fields.Int(required=False, validate=validate.Range(min=1, max=100), load_default=20)

    # 排序
    sort_by = fields.Str(
        required=False,
        validate=validate.OneOf(['name', 'score', 'joined_date', 'created_at']),
        load_default='name'
    )
    sort_order = fields.Str(
        required=False,
        validate=validate.OneOf(['asc', 'desc']),
        load_default='asc'
    )

    # 類型篩選
    player_type = fields.Str(
        required=False,
        validate=validate.OneOf(['member', 'guest', 'all'])
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
