import re

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import bp  # 假設 bp 是您的 API 藍圖
from ..extensions import db
from ..models.enums import GenderEnum, PositionEnum  # 確保匯入
from ..models.member import Member
from ..models.user import User


@bp.route("/profile/me", methods=["GET"])
@jwt_required()
def get_my_profile():
    user_id = get_jwt_identity()
    # current_app.logger.debug(f"JWT Identity (user_id) from token: {user_id}")
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({"msg": "User not found or account disabled."}), 404

    user_data = user.to_dict()
    member_data = {}
    if user.team_member_profile:
        member_data = user.team_member_profile.to_dict()

    return jsonify({"user_profile": user_data, "team_member_profile": member_data}), 200


@bp.route("/profile/me", methods=["PUT"])
@jwt_required()
def update_my_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({"msg": "User not found or account disabled."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request payload must be JSON"}), 400

    errors = {}
    updated_user_fields = {}
    updated_member_fields = {}

    # --- 更新 User 模型的欄位 (例如 email) ---
    if "email" in data:
        email = data.get("email")
        if email and email.strip():  # 如果提供了 email 且不為空
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
                errors["email"] = "無效的電子郵件格式。"
            elif User.query.filter(User.id != user_id, User.email == email).first():
                errors["email"] = "此電子郵件已被其他帳號使用。"
            else:
                user.email = email
                updated_user_fields["email"] = email
        else:  # 如果傳來空字串或 null，則設為 null (如果模型允許)
            user.email = None
            updated_user_fields["email"] = None

    # --- 更新 TeamMember 模型的欄位 ---
    member = user.team_member_profile
    if not member:  # 理論上 User 應該都有 TeamMember profile
        return jsonify({"error": "Team member profile not found for this user."}), 404

    # 顯示名稱/綽號
    if "display_name" in data:
        display_name_val = data.get("display_name", "").strip()
        member.display_name = (
            display_name_val if display_name_val else member.name
        )  # 若為空則退回真實姓名
        updated_member_fields["display_name"] = member.display_name

    # 性別
    if "gender" in data and data.get("gender"):  # 允許傳空字串來清除性別
        gender_str = data.get("gender")
        if gender_str:
            gender_enum = GenderEnum.get_by_name(gender_str)
            if gender_enum:
                member.gender = gender_enum
                updated_member_fields["gender"] = gender_enum.name
            else:
                errors["gender"] = f"無效的性別值: '{gender_str}'."
        else:  # 傳空字串表示清除
            member.gender = None
            updated_member_fields["gender"] = None

    # 習慣位置
    if "position" in data and data.get("position"):
        position_str = data.get("position")
        if position_str:
            position_enum = PositionEnum.get_by_name(position_str)
            if position_enum:
                member.position = position_enum
                updated_member_fields["position"] = position_enum.name
            else:
                errors["position"] = f"無效的位置值: '{position_str}'."
        else:
            member.position = None
            updated_member_fields["position"] = None

    # 其他可編輯欄位
    editable_member_fields = [
        "organization_name",
        "racket_details",
        "notes",
    ]  # 真實姓名 name 和 student_id 通常不讓使用者隨意改
    for field in editable_member_fields:
        if field in data:
            setattr(member, field, data.get(field))
            updated_member_fields[field] = data.get(field)

    if "student_id" in data:
        student_id_val = data.get("student_id")
        if student_id_val and student_id_val.strip():
            if Member.query.filter(
                Member.id != member.id, Member.student_id == student_id_val
            ).first():
                errors["student_id"] = f"學號 '{student_id_val}' 已被其他成員使用。"
            else:
                member.student_id = student_id_val
                updated_member_fields["student_id"] = student_id_val
        else:
            member.student_id = None  # 允許清空學號
            updated_member_fields["student_id"] = None

    if errors:
        return jsonify({"message": "資料驗證失敗", "errors": errors}), 400

    try:
        db.session.commit()
        # 為了讓前端 Pinia store 能更新，回傳更新後的完整 User 和 Member 資訊
        user_data_resp = user.to_dict()
        member_data_resp = member.to_dict()

        # 合併到 user_data_resp 的 team_member_details
        if "team_member_details" in user_data_resp and isinstance(
            user_data_resp["team_member_details"], dict
        ):
            user_data_resp["team_member_details"].update(
                {
                    "display_name": member_data_resp.get("display_name"),
                    "gender": member_data_resp.get("gender"),  # 這裡會是 Enum 的 value
                    "position": member_data_resp.get("position"),  # Enum 的 value
                    "organization_name": member_data_resp.get("organization_name"),
                    "racket_details": member_data_resp.get("racket_details"),
                    "notes": member_data_resp.get("notes"),
                }
            )
        elif (
            "team_member_details" not in user_data_resp and member_data_resp
        ):  # 以防萬一
            user_data_resp["team_member_details"] = member_data_resp

        current_app.logger.info(
            f"Profile updated for user {user.username}. User fields: {updated_user_fields}, Member fields: {updated_member_fields}"
        )
        return (
            jsonify(
                {
                    "message": "個人資料已成功更新！",
                    "user": user_data_resp,  # 回傳 User 的 to_dict()，其中已包含 TeamMember 簡要資訊
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error updating profile for user {user.username}: {str(e)}", exc_info=True
        )
        return jsonify({"error": "更新個人資料時發生錯誤。"}), 500
