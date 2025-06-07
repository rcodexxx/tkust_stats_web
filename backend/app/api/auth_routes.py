# backend/app/api/auth_routes.py
from flask import current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError as MarshmallowValidationError

from . import api_bp  # 假設 bp 是在 app/api/__init__.py 中定義的 Blueprint
from ..schemas.auth_schemas import (
    QuickRegisterRequestSchema,
    LoginRequestSchema,
    PasswordChangeRequestSchema,
    TokenResponseSchema,
    AccessTokenResponseSchema,
)
from ..services.auth_service import AuthService
from ..tools.exceptions import (  # 導入自訂的業務異常
    AppException,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserInactiveError,
    IncorrectPasswordError,
    PasswordPolicyError,
    UserNotFoundError,
    TokenRefreshError,
)

# 實例化 Schemas 以便在路由中使用
quick_register_schema = QuickRegisterRequestSchema()
login_schema = LoginRequestSchema()
password_change_schema = PasswordChangeRequestSchema()
token_response_schema = TokenResponseSchema()
access_token_schema = AccessTokenResponseSchema()

# --- 認證相關 API 端點 ---


@api_bp.route("/auth/register", methods=["POST"])
def register_route():
    """
    快速註冊路由。
    僅需提供手機號碼 (phoneNumber) 即可創建帳號。
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # 1. 使用 Schema 驗證請求數據
        # validated_data 將會是 {'username': '09xxxxxxxx'}
        validated_data = quick_register_schema.load(json_data)
    except MarshmallowValidationError as err:
        current_app.logger.warning(f"註冊驗證失敗: {err.messages}")
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400

    try:
        # 2. 調用 AuthService 的 register 方法
        result = AuthService.register(validated_data["username"])

        # 3. 序列化並返回成功回應
        response_data = token_response_schema.dump(result)
        # 將服務層返回的初始密碼警告加入到最終的回應中
        if "initial_password_warning" in result:
            response_data["initial_password_warning"] = result["initial_password_warning"]

        return jsonify(response_data), 201

    except UserAlreadyExistsError as e:
        # 處理服務層拋出的特定業務異常
        current_app.logger.warning(f"註冊失敗 - {e.message}")
        return jsonify(e.to_dict()), e.status_code
    except AppException as e:
        # 處理其他已知的應用程式異常
        current_app.logger.error(f"註冊時發生應用程式錯誤: {e.message}", exc_info=False)
        return jsonify(e.to_dict()), e.status_code
    except Exception:
        # 處理未預期的伺服器錯誤
        current_app.logger.error(f"註冊時發生未預期錯誤", exc_info=True)
        return jsonify({"error": "registration_failed", "message": "註冊過程中發生未預期的錯誤。"}), 500


@api_bp.route("/auth/login", methods=["POST"])
def login_route():
    """
    使用者登入路由。
    可使用手機號碼或 Email 進行登入。
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # 1. 使用 Schema 驗證請求數據
        validated_data = login_schema.load(json_data)
    except MarshmallowValidationError as err:
        current_app.logger.warning(f"登入驗證失敗: {err.messages}")
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400

    try:
        # 2. 調用 AuthService 的 login 方法
        result = AuthService.login(validated_data["username"], validated_data["password"])
        current_app.logger.info(f"使用者 '{validated_data['username']}' 成功登入。")

        # 3. 序列化並返回成功回應
        return token_response_schema.dump(result), 200

    except (InvalidCredentialsError, UserInactiveError) as e:
        # 處理登入失敗的特定業務異常
        current_app.logger.warning(f"登入失敗 for '{validated_data.get('username')}': {e.message}")
        return jsonify(e.to_dict()), e.status_code
    except AppException as e:
        current_app.logger.error(
            f"登入時發生應用程式錯誤 for {validated_data.get('username')}: {e.message}", exc_info=False
        )
        return jsonify(e.to_dict()), e.status_code
    except Exception:
        current_app.logger.error(f"登入時發生未預期錯誤 for {validated_data.get('username')}", exc_info=True)
        return jsonify({"error": "login_failed", "message": "登入過程中發生未預期的錯誤。"}), 500


@api_bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_access_route():
    """
    使用 Refresh Token 獲取新的 Access Token。
    """
    current_user_id = get_jwt_identity()
    try:
        # 調用 AuthService 處理權杖刷新邏輯
        new_access_token = AuthService.refresh_access_token(str(current_user_id))
        current_app.logger.info(f"Access token 已為使用者 ID '{current_user_id}' 刷新。")

        # 序列化回應
        return access_token_schema.dump({"access_token": new_access_token}), 200

    except TokenRefreshError as e:
        current_app.logger.warning(f"刷新 token 失敗 for user ID '{current_user_id}': {e.message}")
        return jsonify(e.to_dict()), e.status_code
    except Exception:
        current_app.logger.error(f"刷新 token 時發生未預期錯誤 for user ID '{current_user_id}'", exc_info=True)
        return jsonify({"error": "token_refresh_failed", "message": "刷新 token 過程中發生錯誤。"}), 500


@api_bp.route("/auth/change-password", methods=["POST"])
@jwt_required()
def change_password_route():
    """
    已登入使用者修改自己的密碼。
    """
    current_user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "missing_json", "message": "缺少 JSON 請求內容。"}), 400

    try:
        # 1. 使用 Schema 驗證請求數據
        validated_data = password_change_schema.load(json_data)
    except MarshmallowValidationError as err:
        current_app.logger.warning(f"更改密碼驗證失敗 for user ID '{current_user_id}': {err.messages}")
        return jsonify({"error": "validation_error", "message": "輸入數據有誤。", "details": err.messages}), 400

    try:
        # 2. 調用 AuthService 處理密碼更改邏輯
        AuthService.change_user_password(
            int(current_user_id), validated_data["old_password"], validated_data["new_password"]
        )
        current_app.logger.info(f"使用者 ID '{current_user_id}' 的密碼已成功更改。")

        # 3. 返回成功訊息
        return jsonify({"message": "密碼已成功更新。"}), 200

    except (IncorrectPasswordError, PasswordPolicyError, UserNotFoundError, UserInactiveError) as e:
        # 處理更改密碼失敗的特定業務異常
        current_app.logger.warning(f"更改密碼失敗 for user ID '{current_user_id}': {e.message}")
        return jsonify(e.to_dict()), e.status_code
    except AppException as e:
        current_app.logger.error(
            f"更改密碼時發生應用程式錯誤 for user ID '{current_user_id}': {e.message}", exc_info=False
        )
        return jsonify(e.to_dict()), e.status_code
    except Exception:
        current_app.logger.error(f"更改密碼時發生未預期錯誤 for user ID '{current_user_id}'", exc_info=True)
        return jsonify({"error": "password_change_failed", "message": "更新密碼過程中發生錯誤。"}), 500
