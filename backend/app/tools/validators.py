# backend/app/validators.py
import re

from ..extensions import db
from ..models.enums import UserRoleEnum, GenderEnum, PositionEnum
from ..models.member import Member
from ..models.organization import Organization
from ..models.user import User


# --- User Validation ---
def validate_username(username, existing_user_id=None):
    """Validates username (phone number) format and uniqueness."""
    if not username or not username.strip():
        return "登入帳號 (手機號碼) 為必填。"
    if not re.match(r"^09\d{8}$", username):  # 台灣手機號碼範例
        return "登入帳號手機號碼格式無效 (應為09開頭10位數字)。"
    query = User.query.filter(User.username == username)
    if existing_user_id:
        query = query.filter(User.id != existing_user_id)
    if query.first():
        return f"登入帳號 '{username}' 已被使用。"
    return None


def validate_password(password, is_required=True):
    """Validates password format (e.g., minimum length)."""
    if is_required and (not password or not password.strip()):
        return "密碼為必填。"
    if password and len(password) < 6:  # 密碼長度至少6位
        return "密碼長度至少需要6位。"
    return None


def validate_email(email, existing_user_id=None):
    """Validates email format and uniqueness (if email is not empty)."""
    if not email or not email.strip():
        return None  # Email is optional
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return "無效的電子郵件格式。"
    query = User.query.filter(User.email == email)
    if existing_user_id:
        query = query.filter(User.id != existing_user_id)
    if query.first():
        return f"電子郵件 '{email}' 已被使用。"
    return None


def validate_role_str(role_str, default_role=UserRoleEnum.MEMBER):
    """Validates role string and returns Enum member or default."""
    if not role_str or not role_str.strip():
        return None, default_role  # 如果未提供，返回預設角色

    role_enum = UserRoleEnum.get_by_name(role_str.upper())
    if not role_enum:
        return (
            f"無效的角色值: '{role_str}'. 有效值為 {[r.name for r in UserRoleEnum]}.",
            None,
        )
    return None, role_enum


# --- Member Validation ---
def validate_member_name(name):
    if not name or not name.strip():
        return "成員真實姓名為必填。"
    if len(name) > 100:
        return "成員真實姓名長度不可超過100字元。"
    return None


def validate_display_name(display_name):
    if display_name and len(display_name) > 100:  # 可選，但若提供則檢查長度
        return "成員顯示名稱長度不可超過100字元。"
    return None


def validate_member_student_id(student_id, existing_member_id=None):
    """Validates Member's student_id format and uniqueness (if not empty)."""
    if not student_id or not student_id.strip():
        return None  # 學號可選
    if not re.match(r"^\d{7,9}$", student_id):
        return "學號必須是7到9位數字。"
    query = Member.query.filter(Member.student_id == student_id)
    if existing_member_id:
        query = query.filter(Member.id != existing_member_id)
    if query.first():
        return f"學號 '{student_id}' 已被其他成員使用。"
    return None


def validate_gender_str_for_member(gender_str):
    if not gender_str or not gender_str.strip():
        return None, None
    gender_enum = GenderEnum.get_by_name(gender_str.upper())
    if not gender_enum:
        return f"無效的性別值: '{gender_str}'.", None
    return None, gender_enum


def validate_position_str_for_member(position_str):
    if not position_str or not position_str.strip():
        return None, None
    position_enum = PositionEnum.get_by_name(position_str.upper())
    if not position_enum:
        return f"無效的位置值: '{position_str}'.", None
    return None, position_enum


def validate_organization_id_for_member(org_id_val):
    if org_id_val is None or str(org_id_val).strip() == "":
        return None, None
    try:
        org_id_int = int(org_id_val)
        org = db.session.get(
            Organization, org_id_int
        )  # Use db.session.get for querying by PK
        if not org:
            return f"找不到 ID 為 {org_id_int} 的組織。", None
        return None, org_id_int
    except ValueError:
        return "組織 ID 必須是有效的數字。", None
