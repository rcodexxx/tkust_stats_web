import datetime

from flask import current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from . import bp
from ..auth_utils import admin_required
from ..extensions import db
from ..models.enums import GenderEnum, PositionEnum, UserRoleEnum
from ..models.member import Member
from ..services.member_service import create_member


@bp.route("/members", methods=["GET"])  # 通常用 /members 獲取所有成員列表
def get_all_members(active_only=None):
    """獲取所有活躍球員列表，主要用於表單選擇等，按姓名排序"""
    try:
        query = Member.query
        if active_only:
            query = query.filter_by(is_active=True)

        members = query.order_by(Member.name).all()

        member_data = []
        for member in members:
            member_data.append(
                {
                    "id": member.id,
                    "name": member.name,
                    "display_name": member.display_name,
                    "organization": member.organization,
                    "score": member.score,
                    "student_id": member.student_id,
                    "gender": (member.gender.value if member.gender else None),
                    "position": member.position.value if member.position else None,
                    "is_active": member.is_active,
                    "notes": member.notes,
                }
            )
        return jsonify(member_data)
    except Exception as e:
        print(f"Error in get_all_members: {e}")  # 伺服器端日誌
        return jsonify({"error": "An error occurred while fetching members."}), 500


@bp.route("/members", methods=["POST"])
@admin_required  # 只有管理員可以執行這個完整的成員新增
def admin_create_full_member():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request payload must be JSON"}), 400

    # 從 payload 提取所有 User 和 TeamMember 的欄位
    # User fields
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role_str = data.get("role", "PLAYER")
    is_active_user = data.get("is_active_user", True)

    # TeamMember fields
    name = data.get("name")
    display_name = data.get("display_name")
    student_id = data.get("student_id")
    gender_str = data.get("gender")
    position_str = data.get("position")
    mu_str = data.get("mu")
    sigma_str = data.get("sigma")
    join_date_str = data.get("join_date")
    is_active_member = data.get("is_active_member", True)
    notes = data.get("notes")

    # --- 基本驗證 (您可以做得更詳細) ---
    errors = {}
    if not username:
        errors["username"] = "Username for login is required."
    if not name:
        errors["name"] = "Member's real name is required."

    role_enum = UserRoleEnum.get_by_name(role_str)
    if not role_enum:
        errors["role"] = f"Invalid role: {role_str}."

    gender_enum = GenderEnum.get_by_name(gender_str) if gender_str else None
    if gender_str and not gender_enum:
        errors["gender"] = f"Invalid gender: {gender_str}."

    position_enum = PositionEnum.get_by_name(position_str) if position_str else None
    if position_str and not position_enum:
        errors["position"] = f"Invalid position: {position_str}."

    join_date_obj = None
    if join_date_str:
        try:
            join_date_obj = datetime.datetime.strptime(join_date_str, "%Y-%m-%d").date()
        except ValueError:
            errors["join_date"] = "Invalid date format for join_date."

    mu_val = None
    if mu_str is not None:
        try:
            mu_val = float(mu_str)
        except ValueError:
            errors["mu"] = "Mu must be a number."

    sigma_val = None
    if sigma_str is not None:
        try:
            sigma_val = float(sigma_str)
        except ValueError:
            errors["sigma"] = "Sigma must be a number."

    if errors:
        return jsonify({"message": "Input validation failed", "errors": errors}), 400

    try:
        new_user, new_member, actual_password = create_member(
            username=username,
            name=name,
            password=password,  # 傳給輔助函數，如果為 None，輔助函數會用預設
            # email=email,
            role=role_enum,
            display_name=display_name,
            student_id=student_id,
            gender=gender_enum,
            position=position_enum,
            mu=mu_val,
            sigma=sigma_val,
            join_date=join_date_obj,
            is_active_user=is_active_user,
            is_active_member=is_active_member,
            notes=notes,
        )
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "User and TeamMember created successfully by admin.",
                    "user": new_user.to_dict(),
                    "member": new_member.to_dict(),
                    "initial_password_if_default": (
                        actual_password if not password else "Set by admin"
                    ),
                }
            ),
            201,
        )

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 409
    except IntegrityError as ie:
        db.session.rollback()
        current_app.logger.error(
            f"Admin create member IntegrityError: {str(ie.orig)}", exc_info=True
        )
        return jsonify({"error": "Database integrity error."}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Admin create member unexpected error: {str(e)}", exc_info=True
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500
