from functools import wraps

from flask import current_app, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models.enums import UserRoleEnum
from ..models.user import User


def roles_required(*required_roles: UserRoleEnum):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                current_app.logger.warning(
                    f"Roles required: JWT verification failed: {str(e)}"
                )
                return jsonify(msg="Missing or invalid token"), 401

            user_id = get_jwt_identity()
            if not user_id:
                current_app.logger.warning("Roles required: No user identity in JWT.")
                return jsonify(msg="Invalid user identity in token"), 401

            user = db.session.get(User, user_id)
            if not user or not user.is_active:
                current_app.logger.warning(
                    f"Roles required: User {user_id} not found or inactive."
                )
                return (
                    jsonify(msg="User not found, account disabled, or token invalid."),
                    401,
                )

            # 檢查使用者角色是否在允許的角色列表中
            if user.role not in required_roles:
                allowed_roles_str = ", ".join([r.name for r in required_roles])
                current_app.logger.warning(
                    f"Access denied for user {user.username} (Role: {user.role.name}). "
                    f"Required one of: {allowed_roles_str}"
                )
                return (
                    jsonify(
                        msg=f"Access denied. Required role(s): {allowed_roles_str}."
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
