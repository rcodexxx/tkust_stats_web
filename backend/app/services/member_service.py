# backend/app/services/user_member_service.py
import datetime
import os

from ..extensions import db
from ..models.member import Member
from ..models.user import User
from ..tools.validators import (
    validate_username,
    validate_email,
    validate_member_student_id,
    validate_role_str,
    validate_gender_str_for_member,
    validate_position_str_for_member,
    validate_organization_id_for_member,
    validate_password,
)

GENERAL_DEFAULT_INITIAL_PASSWORD = os.environ.get(
    "DEFAULT_INITIAL_PASSWORD", "password"
)


class UserMemberServiceError(ValueError):  # 自訂錯誤類別，方便 API 層捕捉
    def __init__(self, message="操作失敗", errors=None):
        super().__init__(message)
        self.errors = errors if errors is not None else {}


def create_member_with_user(data: dict):
    """
    創建新的 Member 及其關聯的 User 帳號。
    'username' (手機號) 和 'name' (Member 真實姓名) 為必填。
    密碼邏輯：如果 data 中有 'password'，則使用它；否則使用 'username' (手機號) 作為密碼。
    成功則返回 (user, member, password_used_for_user)。
    失敗則拋出 UserMemberServiceError。
    """
    errors = {}

    # User data
    username = data.get("username", "").strip()
    password_from_payload = data.get("password")
    email = data.get("email", "").strip() or None
    role_str = data.get("role", "PLAYER").upper()  # 管理員新增時可指定角色
    is_active_user = data.get("is_active_user", True)

    # Member data
    member_name = data.get("name", "").strip()
    display_name = data.get("display_name", "").strip() or member_name
    student_id = data.get("student_id", "").strip() or None
    gender_str = data.get("gender")
    position_str = data.get("position")
    organization_id_payload = data.get("organization_id")
    mu_payload = data.get("mu")
    sigma_payload = data.get("sigma")
    join_date_payload = data.get("join_date")
    is_active_payload = data.get("is_active", True)  # Member 的 is_active
    notes_payload = data.get("notes")

    # --- 執行驗證 ---
    err = validate_username(username)
    if err:
        errors["username"] = err

    err = validate_email(email)
    if err:
        errors["email"] = err

    if not member_name:
        errors["name"] = "成員真實姓名為必填。"

    err = validate_member_student_id(student_id)
    if err:
        errors["student_id"] = err

    err_role, role_enum = validate_role_str(role_str)
    if err_role:
        errors["role"] = err_role

    err_gender, gender_enum = validate_gender_str_for_member(gender_str)
    if err_gender:
        errors["gender"] = err_gender

    err_pos, position_enum = validate_position_str_for_member(position_str)
    if err_pos:
        errors["position"] = err_pos

    err_org, org_id_int = validate_organization_id_for_member(organization_id_payload)
    if err_org:
        errors["organization_id"] = err_org

    actual_password_to_set = password_from_payload
    if not actual_password_to_set:
        if username:
            actual_password_to_set = username  # 手機號即密碼
        else:
            actual_password_to_set = GENERAL_DEFAULT_INITIAL_PASSWORD  # 備用

    err_pass = validate_password(actual_password_to_set, is_required=True)  # 密碼必填
    if err_pass:
        errors["password"] = err_pass

    if errors:
        raise UserMemberServiceError("資料驗證失敗", errors_dict=errors)

    # --- 創建實例 ---
    new_user = User(
        username=username, email=email, role=role_enum, is_active=is_active_user
    )
    new_user.set_password(actual_password_to_set)

    new_member = Member(
        name=member_name,
        display_name=display_name,
        student_id=student_id,
        gender=gender_enum,
        position=position_enum,
        mu=float(mu_payload) if mu_payload is not None else Member.mu.default.arg,
        sigma=(
            float(sigma_payload)
            if sigma_payload is not None
            else Member.sigma.default.arg
        ),
        organization_id=org_id_int,
        joined_date=(
            datetime.datetime.strptime(join_date_payload, "%Y-%m-%d").date()
            if join_date_payload
            else (
                Member.joined_date.default.arg
                if Member.joined_date.default
                else datetime.date.today()
            )
        ),
        is_active=is_active_payload,  # Member.is_active
        notes=notes_payload,
        user_account=new_user,  # 建立關聯
    )
    db.session.add(new_member)  # add Member 會級聯 add User (如果 cascade 設定正確)
    # 或者 db.session.add_all([new_user, new_member]) 更明確
    return new_user, new_member, actual_password_to_set
