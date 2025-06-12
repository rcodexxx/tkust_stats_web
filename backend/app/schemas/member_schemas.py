# backend/app/schemas/member_schemas.py
from marshmallow import EXCLUDE, Schema, fields, validate
from marshmallow_enum import EnumField

from ..models.enums import UserRoleEnum
from ..models.enums.bio_enums import GenderEnum
from ..models.enums.match_enums import MatchPositionEnum

# --- 巢狀 Schema (用於在 Member 回應中顯示關聯物件的摘要) ---


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


# --- 主要的顯示用 Schema ---
class MemberSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    display_name = fields.Method("get_display_name", dump_only=True)
    student_id = fields.Str(dump_only=True, allow_none=True)
    gender = EnumField(GenderEnum, by_value=True, dump_only=True, allow_none=True)
    position = EnumField(
        MatchPositionEnum, by_value=True, dump_only=True, allow_none=True
    )
    mu = fields.Float(dump_only=True)
    sigma = fields.Float(dump_only=True)
    score = fields.Int(dump_only=True)
    is_active = fields.Bool(attribute="user.is_active", dump_only=True)
    organization = fields.Nested(
        SimpleOrganizationSchema, dump_only=True, allow_none=True
    )
    user = fields.Nested(SimpleUserSchema, dump_only=True)

    def get_display_name(self, obj):
        # 顯示名稱優先使用 User model 上的 display_name，若無則用 Member 的 name
        if obj.user and obj.user.display_name:
            return obj.user.display_name
        return obj.name


# --- 排行榜專用的 Member Schema ---
class LeaderboardMemberSchema(Schema):
    """
    專門用於序列化排行榜數據。
    這個 Schema 是自給自足的，不繼承自其他 Schema，以確保穩定性。
    """

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    display_name = fields.Method("get_display_name", dump_only=True)
    score = fields.Int(dump_only=True)

    # 組織名稱
    organization_name = fields.Method("get_organization_display", dump_only=True)

    # 動態計算的統計數據
    wins = fields.Int(dump_only=True, dump_default=0)
    losses = fields.Int(dump_only=True, dump_default=0)
    total_matches = fields.Int(dump_only=True, dump_default=0)
    win_rate = fields.Float(dump_only=True, dump_default=0.0)

    def get_display_name(self, obj):
        if obj.user and obj.user.display_name:
            return obj.user.display_name
        return obj.name

    def get_organization_display(self, obj):
        if obj.organization:
            return obj.organization.short_name or obj.organization.name
        return None


class MemberCreateSchema(Schema):
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

    # Member Bio 資訊
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    student_id = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(r"^\d{7,9}$", error="學號必須是7到9位數字。"),
    )
    gender = EnumField(GenderEnum, by_value=True, allow_none=True)
    position = EnumField(MatchPositionEnum, by_value=True, allow_none=True)
    organization_id = fields.Int(required=False, allow_none=True)
    is_active = fields.Bool(required=False)
    joined_date = fields.Date(required=False, allow_none=True)
    notes = fields.Str(required=False, allow_none=True)


class MemberUpdateSchema(Schema):
    """
    用於驗證 (Validation) 管理員更新成員的請求數據。
    所有欄位都是可選的（因為在路由中會使用 partial=True）。
    """

    # Member Fields
    name = fields.Str(validate=validate.Length(min=1, max=80))
    student_id = fields.Str(
        allow_none=True,
        validate=validate.Regexp(r"^\d{7,9}$", error="學號必須是7到9位數字。"),
    )
    gender = EnumField(GenderEnum, by_value=True, allow_none=True)
    position = EnumField(MatchPositionEnum, by_value=True, allow_none=True)
    organization_id = fields.Int(allow_none=True)
    joined_date = fields.Date(allow_none=True)
    leaved_date = fields.Date(allow_none=True)
    notes = fields.Str(allow_none=True)

    # User Fields (管理員可以修改這些)
    username = fields.Str(
        validate=validate.Regexp(r"^09\d{8}$", error="手機號碼格式無效。")
    )
    email = fields.Email(allow_none=True)
    display_name = fields.Str(allow_none=True, validate=validate.Length(max=50))
    role = EnumField(
        UserRoleEnum, by_value=True
    )  # by_value=True 表示它期望接收 'member', 'admin' 等字串
    is_active = fields.Bool()  # is_active 屬性現在被正確地歸類到 User Fields

    class Meta:
        unknown = EXCLUDE
