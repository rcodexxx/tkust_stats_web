# your_project/app/schemas/member_schemas.py
from marshmallow import Schema, fields, validate
from marshmallow_enum import EnumField

# 假設您的 enums 和其他 schema 在這些路徑
from ..models.enums.bio_enums import GenderEnum, BloodTypeEnum
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


# --- 主要 Member Schema ---


class MemberSchema(Schema):
    """
    用於序列化 (Serialization) Member 物件，作為 API GET 回應。
    dump_only=True 表示此欄位只在序列化 (物件 -> JSON) 時出現。
    """

    # 基本識別資訊
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    display_name = fields.Method("get_display_name_from_user", dump_only=True)  # 使用 User 的暱稱作為主要顯示
    student_id = fields.Str(dump_only=True, allow_none=True)

    # Bio 資訊
    gender = EnumField(GenderEnum, by_value=True, dump_only=True, allow_none=True)
    blood_type = EnumField(BloodTypeEnum, by_value=True, dump_only=True, allow_none=True)
    position = EnumField(MatchPositionEnum, by_value=True, dump_only=True, allow_none=True)

    # 隊籍狀態
    is_active = fields.Bool(dump_only=True)  # 您 Member 模型中似乎遺漏了 is_active，但通常會有
    joined_date = fields.Date(dump_only=True, allow_none=True)
    leaved_date = fields.Date(dump_only=True, allow_none=True)

    # 評分系統
    mu = fields.Float(dump_only=True)
    sigma = fields.Float(dump_only=True)
    score = fields.Int(dump_only=True)  # 來自 @property

    # 關聯資訊 (巢狀)
    organization = fields.Nested(SimpleOrganizationSchema, dump_only=True, allow_none=True)
    racket = fields.Nested(SimpleRacketSchema, dump_only=True, allow_none=True)
    user = fields.Nested(SimpleUserSchema, dump_only=True)  # 每個 Member 都有 User

    notes = fields.Str(dump_only=True, allow_none=True)

    def get_display_name_from_user(self, obj):
        # 顯示名稱優先使用 User model 上的 display_name，若無則用 Member 的 name
        if obj.user and obj.user.display_name:
            return obj.user.display_name
        return obj.name


# --- 新增：排行榜專用的 Member Schema ---
class LeaderboardMemberSchema(MemberSchema):
    """
    繼承自 MemberSchema，並額外加入排行榜所需的統計欄位。
    """

    wins = fields.Int(dump_only=True, dump_default=0)
    losses = fields.Int(dump_only=True, dump_default=0)
    total_matches = fields.Int(dump_only=True, dump_default=0)
    win_rate = fields.Float(dump_only=True, dump_default=0.0)

    class Meta:
        ordered = True


class MemberCreateSchema(Schema):
    """
    用於驗證 (Validation) 創建新 Member 的請求數據。
    load_only=True 表示此欄位只在反序列化 (JSON -> 物件) 時接收，不會在回應中出現。
    """

    # User 帳號資訊
    username = fields.Str(
        required=True,
        validate=validate.Regexp(r"^09\d{8}$", error="手機號碼格式無效。"),
        metadata={"description": "手機號碼 (登入帳號)"},
    )
    email = fields.Email(required=False, allow_none=True, metadata={"description": "電子郵件 (可選)"})
    password = fields.Str(
        required=False,
        allow_none=True,
        load_only=True,
        validate=validate.Length(min=6),
        metadata={"description": "初始密碼 (可選，若無則預設為手機號碼)"},
    )

    # Member Bio 資訊
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80), metadata={"description": "真實姓名"})
    display_name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
        metadata={"description": "暱稱 (可選，預設與姓名相同)"},
    )
    student_id = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=20), metadata={"description": "學號 (可選)"}
    )
    gender = EnumField(GenderEnum, by_value=True, allow_none=True, metadata={"description": "性別 (可選)"})
    # ... 您可以根據需要在創建時加入更多可選的 bio 欄位 ...
    organization_id = fields.Int(required=False, allow_none=True, metadata={"description": "組織ID (可選)"})


class MemberUpdateSchema(Schema):
    """
    用於驗證 (Validation) 更新 Member 的請求數據。
    所有欄位都是可選的。
    """

    # Member Bio
    name = fields.Str(validate=validate.Length(min=1, max=80))
    student_id = fields.Str(allow_none=True, validate=validate.Length(max=20))
    gender = EnumField(GenderEnum, by_value=True, allow_none=True)
    blood_type = EnumField(BloodTypeEnum, by_value=True, allow_none=True)
    position = EnumField(MatchPositionEnum, by_value=True, allow_none=True)
    joined_date = fields.Date(allow_none=True)
    leaved_date = fields.Date(allow_none=True)
    notes = fields.Str(allow_none=True)

    # 關聯 IDs
    organization_id = fields.Int(allow_none=True)
    racket_id = fields.Int(allow_none=True)

    # 隊籍狀態
    is_active = fields.Bool()  # 您 Member 模型中似乎遺漏了 is_active，但通常會有

    # User Info (通常在獨立的 /api/me 或 /api/users/{id} 端點更新，但這裡也提供選項)
    email = fields.Email(allow_none=True)
    display_name = fields.Str(allow_none=True, validate=validate.Length(max=50))  # 更新 User 的暱稱
