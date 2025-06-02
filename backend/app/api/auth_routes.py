# backend/app/api/auth_routes.py
import re

from flask import current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from sqlalchemy.exc import IntegrityError

from . import bp
from ..extensions import db
from ..models.enums import UserRoleEnum
from ..models.user import User
from ..services.member_service import create_member_with_user


@bp.route("/auth/register", methods=["POST"])
def quick_register_user():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "缺少 JSON 請求內容"}), 400

    username = data.get("phone_number")

    if not username:
        return jsonify({"msg": "必須提供手機號碼"}), 400

    if not re.match(r"^09\d{8}$", username):
        return jsonify({"msg": "無效的手機號碼格式"}), 400

    initial_name = f"隊員_{username[-4:]}"

    try:
        new_user, new_member, actual_password = create_member_with_user(
            username=username,
            name=initial_name,
            display_name=initial_name,
            password=username,
            role=UserRoleEnum.MEMBER,
            is_active=True,
        )
        db.session.commit()

        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)

        user_info = new_user.to_dict(include_member_info=True)

        return (
            jsonify(
                {
                    "msg": "快速註冊成功！請妥善保管您的初始密碼並盡快修改。",
                    "initial_password_info": f"您的初始密碼是：{actual_password}。強烈建議您首次登入後立即修改。",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user_info,
                }
            ),
            201,
        )

    except ValueError as ve:  # 捕捉服務函數中拋出的 ValueError (例如 username 已存在)
        db.session.rollback()
        return jsonify({"error": str(ve)}), 409  # 409 Conflict
    except IntegrityError as ie:  # 以防萬一，雖然服務函數內部也應檢查唯一性
        db.session.rollback()
        current_app.logger.error(
            f"Quick register IntegrityError for {username}: {str(ie.orig)}",
            exc_info=True,
        )
        return jsonify({"error": "資料庫完整性錯誤，該手機號碼可能已被註冊。"}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Quick register unexpected error for {username}: {str(e)}", exc_info=True
        )
        return jsonify({"error": "註冊過程中發生未預期的錯誤。"}), 500


@bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"msg": "缺少使用者名稱或密碼"}), 400

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({"msg": "此帳號已被停用。"}), 401

        identity = str(user.id)
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        user_info = user.to_dict()

        current_app.logger.info(f"User '{username}' logged in successfully.")
        return (
            jsonify(
                access_token=access_token, refresh_token=refresh_token, user=user_info
            ),
            200,
        )

    current_app.logger.warning(
        f"Login failed for username: '{username}' - Bad username or password."
    )
    return jsonify({"msg": "使用者名稱或密碼錯誤"}), 401


@bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)  # <--- 這個端點需要一個有效的 Refresh Token
def refresh_access():
    current_user_id_str = get_jwt_identity()  # Identity 已經是字串了
    # 可以選擇性地檢查 current_user_id_str 對應的 User 是否仍然有效
    # user = db.session.get(User, int(current_user_id_str))
    # if not user or not user.is_active:
    #     return jsonify({"msg": "User not found or inactive"}), 401

    new_access_token = create_access_token(
        identity=current_user_id_str, fresh=False
    )  # 新的 token 不是 fresh 的
    current_app.logger.info(
        f"Access token refreshed for user_id (str): {current_user_id_str}"
    )
    return jsonify(access_token=new_access_token), 200


@bp.route("/auth/change-password", methods=["POST"])
@jwt_required()  # 必須登入才能修改密碼
def change_password():
    """
    允許已登入使用者修改自己的密碼。
    需要 'old_password' 和 'new_password' 在請求的 JSON body 中。
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if not user or not user.is_active:
        current_app.logger.warning(
            f"Change password attempt for non-existent or inactive user ID: {current_user_id}"
        )
        return jsonify({"msg": "User not found or account disabled."}), 404  # 或者 401

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    old_password = data.get("old_password")
    new_password = data.get("new_password")
    # confirm_new_password = data.get('confirm_new_password') # 確認通常由前端處理，但後端也可以再做一次

    if not old_password or not new_password:
        return jsonify({"msg": "Old password and new password are required."}), 400

    # 基本密碼策略驗證 (範例：至少6位)
    if len(new_password) < 6:
        return jsonify({"msg": "New password must be at least 6 characters long."}), 400

    # (可選) 檢查新舊密碼是否相同
    if old_password == new_password:
        return (
            jsonify({"msg": "New password cannot be the same as the old password."}),
            400,
        )

    if not user.check_password(old_password):
        current_app.logger.warning(
            f"Incorrect old password attempt for user: {user.username}"
        )
        return (
            jsonify({"msg": "Incorrect old password."}),
            401,
        )  # 401 Unauthorized 更適合密碼錯誤

    # 設定新密碼
    user.set_password(new_password)

    try:
        db.session.commit()
        current_app.logger.info(
            f"Password changed successfully for user: {user.username}"
        )
        return jsonify({"msg": "Password updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error changing password for user {user.username}: {str(e)}", exc_info=True
        )
        return jsonify({"msg": "Failed to update password due to a server error."}), 500
