import re  # 用於 email 驗證 (如果 validate_email 不在 validators 中)

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError  # 確保匯入

from . import bp  # 假設 bp 是您的 API 藍圖
from ..extensions import db
from ..models.enums import GenderEnum, PositionEnum  # 確保匯入
from ..models.organization import Organization  # 用於驗證 organization_id
from ..models.user import User


# 假設您的 validators.py 包含以下函數，或類似的邏輯
# from ..tools.validators import validate_email, validate_gender_str, validate_position_str, validate_organization_id


# --- 為了範例完整，這裡定義一個簡化的 get_cleaned_string_or_none ---
def get_cleaned_string_or_none(data_dict, key_name):
    if key_name not in data_dict:
        return None
    value = data_dict[key_name]
    if value is None:
        return None
    stripped_value = str(value).strip()
    return stripped_value if stripped_value else None


# --- 假設的驗證函數 (實際應從 validators.py 匯入) ---
def _is_valid_email_format(email_str):  # 簡易 email 格式檢查
    if not email_str:
        return True  # 空值通過格式檢查，由是否必填來控制
    return bool(
        re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email_str)
    )


# ------------------------------------------------------------


@bp.route("/profile/me", methods=["GET"])
@jwt_required()
def get_my_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        current_app.logger.info(
            f"Attempt to access profile for non-existent or inactive user ID: {user_id}"
        )
        return jsonify({"msg": "User not found or account disabled."}), 404

    # User.to_dict() 應該能決定是否包含 team_member_profile 的詳細資訊
    # 或者我們在這裡明確組合
    user_profile_data = user.to_dict()  # User 模型自身的 to_dict
    team_member_data = {}
    if user.team_member_profile:
        team_member_data = user.team_member_profile.to_dict()  # Member 模型的 to_dict

    current_app.logger.debug(f"Fetched profile for user: {user.username}")
    return (
        jsonify(
            {"user_profile": user_profile_data, "team_member_profile": team_member_data}
        ),
        200,
    )


@bp.route("/profile/me", methods=["PUT"])
@jwt_required()
def update_my_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        current_app.logger.warning(
            f"Attempt to update profile for non-existent or inactive user ID: {user_id}"
        )
        return jsonify({"msg": "User not found or account disabled."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request payload must be JSON"}), 400

    errors = {}

    # --- 更新 User 模型的欄位 ---
    # Email (使用者可修改自己的 Email)
    if "email" in data:
        email_val = get_cleaned_string_or_none(data, "email")
        if email_val:  # 只有在提供了非空 email 時才驗證和更新
            if not _is_valid_email_format(email_val):  # 假設的驗證函數
                errors["email"] = "無效的電子郵件格式。"
            elif User.query.filter(User.id != user_id, User.email == email_val).first():
                errors["email"] = "此電子郵件已被其他帳號使用。"
            else:
                user.email = email_val
        elif (
            email_val is None and data.get("email", "NOT_SENTINEL") is not None
        ):  # 如果明確傳了 null 或空字串，則清空
            user.email = None

            # 使用者通常不能修改自己的 username(手機號) 或 role，這些應由管理員操作

    # --- 更新 Member (TeamMember) 模型的欄位 ---
    member = user.team_member_profile
    if not member:
        # 如果 User 必須有關聯的 Member profile 才能更新這些欄位，可以在此返回錯誤
        # 但如果允許 User 存在但沒有 Member profile (例如剛快速註冊還未完善資料)，則跳過 Member 更新
        current_app.logger.info(
            f"User {user.username} (ID: {user_id}) has no team_member_profile to update."
        )
        # return jsonify({"error": "Team member profile not found for this user."}), 404 # 或者不報錯，只更新 User 部分
    else:
        # 顯示名稱/綽號
        if "display_name" in data:
            display_name_val = get_cleaned_string_or_none(data, "display_name")
            # 如果 display_name 為空，Member 模型或其 get_display_name() 方法應能回退到 name
            member.display_name = (
                display_name_val  # 允許設為空，由 get_display_name 處理顯示
            )

        # 性別
        if "gender" in data:
            gender_str = get_cleaned_string_or_none(data, "gender")
            if gender_str:
                gender_enum = GenderEnum.get_by_name(
                    gender_str.upper()
                )  # 假設 get_by_name 處理大寫
                if gender_enum:
                    member.gender = gender_enum
                else:
                    errors["gender"] = f"無效的性別值: '{gender_str}'."
            else:  # 允許清空性別
                member.gender = None

        # 習慣位置
        if "position" in data:
            position_str = get_cleaned_string_or_none(data, "position")
            if position_str:
                position_enum = PositionEnum.get_by_name(position_str.upper())
                if position_enum:
                    member.position = position_enum
                else:
                    errors["position"] = f"無效的位置值: '{position_str}'."
            else:  # 允許清空位置
                member.position = None

        # 所屬組織 (接收 organization_id)
        if "organization_id" in data:
            org_id_payload = data.get("organization_id")
            if org_id_payload is not None and str(org_id_payload).strip() != "":
                try:
                    org_id_int = int(org_id_payload)
                    if org_id_int != 0 and not db.session.get(
                        Organization, org_id_int
                    ):  # 檢查組織是否存在 (0 或空通常表示不選擇)
                        errors["organization_id"] = (
                            f"找不到 ID 為 {org_id_int} 的組織。"
                        )
                    else:
                        member.organization_id = org_id_int if org_id_int != 0 else None
                except ValueError:
                    errors["organization_id"] = "組織 ID 必須是有效的數字或空。"
            else:  # 允許清空組織
                member.organization_id = None

        # 其他 Member 欄位如 name, student_id, mu, sigma, is_active, join_date, leaved_date
        # 通常不由使用者自己在此 API 修改，應由管理員的 Member CRUD API 處理。

    if errors:
        return jsonify({"message": "資料驗證失敗", "errors": errors}), 400

    try:
        db.session.commit()
        current_app.logger.info(
            f"Profile updated for user {user.username} (ID: {user_id})"
        )

        # 回傳更新後的數據，結構應與 GET /api/profile/me 一致
        updated_user_data = user.to_dict()
        updated_member_data = (
            user.team_member_profile.to_dict() if user.team_member_profile else {}
        )

        return (
            jsonify(
                {
                    "message": "個人資料已成功更新！",
                    "user_profile": updated_user_data,
                    "team_member_profile": updated_member_data,
                }
            ),
            200,
        )
    except IntegrityError as ie:  # 例如 email 唯一性衝突
        db.session.rollback()
        current_app.logger.error(
            f"Update profile IntegrityError for user {user.username}: {str(ie.orig)}",
            exc_info=True,
        )
        # 更具體的錯誤判斷
        err_detail_lower = str(ie.orig).lower()
        if (
            "users_email_key" in err_detail_lower
            or "users_email_idx" in err_detail_lower
        ):
            errors["email"] = f"電子郵件 '{data.get('email')}' 已被其他帳號使用。"
        else:
            errors["database"] = "資料庫錯誤，更新失敗。"
        return jsonify({"message": "更新失敗，資料衝突。", "errors": errors}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error updating profile for user {user.username}: {str(e)}", exc_info=True
        )
        return jsonify({"error": "更新個人資料時發生未預期的錯誤。"}), 500
