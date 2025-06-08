# backend/app/schemas/profile_schemas.py
from marshmallow import Schema, fields, validate, pre_load
from marshmallow_enum import EnumField

from .member_schemas import MemberSchema  # 我們可以重用 MemberSchema 來顯示巢狀的隊員資料
from ..models.enums.bio_enums import GenderEnum
from ..models.enums.match_enums import MatchPositionEnum


class ProfileUpdateSchema(Schema):
    """
    用於驗證 (Validation) 更新個人資料的請求數據。
    所有欄位都是可選的，因為使用者可能只更新其中一部分。
    """

    # User Model Fields
    email = fields.Email(allow_none=True, metadata={"description": "電子郵件"})
    display_name = fields.Str(allow_none=True, validate=validate.Length(max=50), metadata={"description": "使用者暱稱"})

    # Member Model Fields
    name = fields.Str(validate=validate.Length(min=1, max=80), metadata={"description": "真實姓名"})
    student_id = fields.Str(
        allow_none=True,
        validate=validate.Regexp(r"^\d{7,9}$", error="學號必須是7到9位數字。"),
        metadata={"description": "學號"},
    )

    # Member Model Fields (如果使用者有關聯的 Member Profile)
    # 這些欄位是使用者可以自己修改的 bio
    gender = EnumField(GenderEnum, by_value=True, allow_none=True, metadata={"description": "性別"})
    position = EnumField(MatchPositionEnum, by_value=True, allow_none=True, metadata={"description": "擅長位置"})
    organization_id = fields.Int(allow_none=True, metadata={"description": "所屬組織ID"})
    # ... 您可以加入更多允許使用者自己更新的 Member 欄位，例如 notes, racket_id, blood_type 等

    @pre_load
    def clean_empty_strings(self, data, **kwargs):
        # 在載入驗證前，將空字串轉換為 None，以符合 allow_none=True 的行為
        for key, value in data.items():
            if isinstance(value, str) and not value.strip():
                data[key] = None
        return data


class UserProfileResponseSchema(Schema):
    """
    用於序列化 (Serialization) /profile/me 的 GET 回應。
    它結合了 User 和 Member 的資訊。
    """

    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True, allow_none=True)
    display_name = fields.Str(dump_only=True, allow_none=True)
    role = fields.Str(attribute="role.value", dump_only=True)  # 輸出 Enum 的 value
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # 巢狀顯示關聯的 Member Profile
    member_profile = fields.Nested(MemberSchema, dump_only=True, allow_none=True)

    class Meta:
        ordered = True
