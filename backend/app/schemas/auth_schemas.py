# backend/app/schemas/auth_schemas.py
from marshmallow import Schema, fields, validate
from marshmallow_enum import EnumField

from ..models.enums.user_enums import UserRoleEnum


# --- Request Schemas ---
class QuickRegisterRequestSchema(Schema):
    phone_number = fields.Str(
        required=True,
        validate=[
            validate.Length(min=10, max=10, error="手機號碼必須是10位數字。"),
            validate.Regexp(r"^09\d{8}$", error="手機號碼格式無效 (應為09開頭10位數字)。"),
        ],
        data_key="phoneNumber",
        attribute="username",
    )


class LoginRequestSchema(Schema):
    username = fields.Str(required=True, metadata={"description": "手機號碼或使用者名稱"})
    password = fields.Str(required=True, metadata={"description": "登入密碼"})


class PasswordChangeRequestSchema(Schema):
    old_password = fields.Str(required=True, metadata={"description": "舊密碼"})
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=6, error="新密碼長度至少需要6位。"),
        metadata={"description": "新密碼"},
    )
    # confirm_new_password = fields.Str(required=True) # 可選，通常前端做確認

    # 如果需要在 schema 層級做更複雜的驗證，例如新舊密碼不能相同：
    # from marshmallow import validates_schema
    # @validates_schema
    # def validate_passwords(self, data, **kwargs):
    #     if data.get('old_password') == data.get('new_password'):
    #         raise MarshmallowValidationError("新密碼不能與舊密碼相同。", field_name="new_password")


# --- Response Schemas ---
class UserAuthResponseSchema(Schema):
    """用於序列化使用者基本資訊和 Member 資訊 (如果有關聯)"""

    id = fields.Int(dump_only=True, metadata={"description": "使用者ID"})
    username = fields.Str(dump_only=True, metadata={"description": "使用者名稱"})
    email = fields.Email(dump_only=True, metadata={"description": "電子郵件"})
    display_name = fields.Str(
        dump_only=True, metadata={"description": "使用者設定的暱稱"}
    )  # User model 上的 display_name
    role = EnumField(
        UserRoleEnum, by_value=True, dump_only=True, metadata={"description": "使用者角色"}
    )  # by_value=True 表示輸出 Enum 的 value
    created_at = fields.DateTime(dump_only=True, metadata={"description": "帳號創建時間"})

    # 這裡可以選擇性地巢狀 Member 資訊
    # member_id = fields.Int(attribute="member_profile.id", dump_only=True, allow_none=True)
    # member_display_name = fields.Str(attribute="member_profile.display_name", dump_only=True, allow_none=True) # Member 的暱稱

    class Meta:
        ordered = True  # 保持欄位順序


class TokenResponseSchema(Schema):
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=False)  # 登入時才回傳 refresh_token
    user = fields.Nested(UserAuthResponseSchema, required=True, metadata={"description": "使用者資訊"})

    class Meta:
        ordered = True


class AccessTokenResponseSchema(Schema):
    access_token = fields.Str(required=True)

    class Meta:
        ordered = True
