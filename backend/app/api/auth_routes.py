# backend/app/api/auth_routes.py
import re

from flask import current_app, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError

from . import bp
from ..extensions import db
from ..models.enums import UserRoleEnum
from ..models.user import User
from ..services.member_service import create_member


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
        new_user, new_member, actual_password = create_member(
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

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        user_info = user.to_dict(include_member_info=True)

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
