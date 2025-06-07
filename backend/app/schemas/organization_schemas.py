# backend/app/schemas/organization_schemas.py
from marshmallow import Schema, fields, validate


# --- 用於 API 回應的主要組織 Schema ---
class OrganizationSchema(Schema):
    """
    用於序列化 (Serialization) Organization 物件，作為 API 回應。
    """

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    short_name = fields.Str(dump_only=True, allow_none=True)
    description = fields.Str(dump_only=True, allow_none=True)
    contact_person = fields.Str(dump_only=True, allow_none=True)
    contact_email = fields.Email(dump_only=True, allow_none=True)
    contact_phone = fields.Str(dump_only=True, allow_none=True)

    # 這個欄位將由路由層在序列化前動態添加，這裡定義它的型別和預設值
    members_count = fields.Int(dump_only=True, dump_default=0)

    class Meta:
        ordered = True


# --- 用於創建組織的請求 Schema ---
class OrganizationCreateSchema(Schema):
    """
    用於驗證 (Validation) 創建新組織的請求數據。
    """

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100), metadata={"description": "組織全名"})
    short_name = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=30), metadata={"description": "組織簡稱"}
    )
    description = fields.Str(required=False, allow_none=True, metadata={"description": "組織描述"})
    contact_person = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=50), metadata={"description": "主要聯絡人"}
    )
    contact_email = fields.Email(required=False, allow_none=True, metadata={"description": "聯絡Email"})
    contact_phone = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=30), metadata={"description": "聯絡電話"}
    )


# --- 用於更新組織的請求 Schema ---
class OrganizationUpdateSchema(OrganizationCreateSchema):
    """
    用於驗證 (Validation) 更新組織的請求數據。
    它繼承自創建 Schema，但在路由中使用 partial=True 時，所有欄位都變為可選。
    """

    pass
