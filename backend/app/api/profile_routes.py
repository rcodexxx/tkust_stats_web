# backend/app/api/profile_routes.py
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from . import api_bp  # 假設您的 Blueprint 叫做 api_bp
from ..schemas.profile_schemas import ProfileUpdateSchema, UserProfileResponseSchema
from ..services.profile_service import ProfileService
from ..tools.exceptions import AppException, UserNotFoundError, UserAlreadyExistsError

# 實例化 Schemas
profile_update_schema = ProfileUpdateSchema()
user_profile_response_schema = UserProfileResponseSchema()


@api_bp.route("/profile/me", methods=["GET"])
@jwt_required()
def get_my_profile():
    """獲取當前登入使用者的個人資料。"""
    current_user_id = get_jwt_identity()
    try:
        user = ProfileService.get_user_profile(int(current_user_id))
        # 使用 UserProfileResponseSchema 序列化包含 User 和 Member 資訊的完整回應
        return jsonify(user_profile_response_schema.dump(user)), 200
    except UserNotFoundError as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error getting profile for user ID {current_user_id}: {e}", exc_info=True)
        return jsonify({"error": "server_error", "message": "獲取個人資料時發生錯誤。"}), 500


@api_bp.route("/profile/me", methods=["PUT"])
@jwt_required()
def update_my_profile():
    """更新當前登入使用者的個人資料。"""
    current_user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # 1. 使用 Schema 驗證請求數據，partial=True 允許部分更新
        validated_data = profile_update_schema.load(json_data, partial=True)
    except MarshmallowValidationError as err:
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400

    try:
        # 2. 調用服務層來執行更新
        updated_user = ProfileService.update_user_profile(int(current_user_id), validated_data)

        # 3. 序列化並返回更新後的完整個人資料
        return (
            jsonify({"message": "個人資料已成功更新！", "profile": user_profile_response_schema.dump(updated_user)}),
            200,
        )

    except (UserNotFoundError, UserAlreadyExistsError) as e:
        # 處理已知的業務邏輯錯誤
        current_app.logger.warning(f"Failed to update profile for user ID {current_user_id}: {e.message}")
        return jsonify(e.to_dict()), e.status_code
    except AppException as e:
        # 處理其他已知的應用程式錯誤
        current_app.logger.error(f"Error updating profile for user ID {current_user_id}: {e.message}", exc_info=False)
        return jsonify(e.to_dict()), e.status_code
    except Exception:
        # 處理未預期的伺服器錯誤
        current_app.logger.error(f"Unexpected error updating profile for user ID {current_user_id}", exc_info=True)
        return jsonify({"error": "server_error", "message": "更新個人資料時發生未預期的錯誤。"}), 500
