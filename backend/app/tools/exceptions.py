# your_project/app/exceptions.py


class AppException(Exception):
    """應用程式自訂錯誤的基底類別。"""

    status_code = 500
    error_code = "app_error"
    message = "發生未預期的應用程式錯誤。"

    def __init__(self, message: str = None, status_code: int = None, error_code: str = None, payload: dict = None):
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.payload = payload

    def to_dict(self) -> dict:
        rv = dict(self.payload or ())
        rv["error"] = self.error_code
        rv["message"] = self.message
        return rv


class ValidationError(AppException):
    """請求數據驗證失敗時拋出的錯誤。"""

    status_code = 400  # 或 422 Unprocessable Entity
    error_code = "validation_error"
    message = "輸入數據驗證失敗。"

    def __init__(self, errors: dict, message: str = None):
        super().__init__(message or self.message)
        self.errors = errors  # Marshmallow schema.validate() 返回的錯誤字典

    def to_dict(self) -> dict:
        rv = super().to_dict()
        rv["details"] = self.errors  # 加入詳細的欄位錯誤
        return rv


class UserAlreadyExistsError(AppException):
    status_code = 409  # Conflict
    error_code = "user_already_exists"
    # message 會在拋出時設定, 例如 "使用者名稱已被使用" 或 "電子郵件已被註冊"


class InvalidCredentialsError(AppException):
    status_code = 401  # Unauthorized
    error_code = "invalid_credentials"
    message = "使用者名稱或密碼錯誤。"


class UserInactiveError(AppException):
    status_code = 401  # Unauthorized (或 403 Forbidden)
    error_code = "user_inactive"
    message = "此帳號已被停用。"


class IncorrectPasswordError(AppException):
    status_code = 401  # Unauthorized
    error_code = "incorrect_password"
    message = "舊密碼不正確。"


class PasswordPolicyError(AppException):
    status_code = 400  # Bad Request
    error_code = "password_policy_violation"
    # message 會在拋出時設定, 例如 "新密碼長度不足"


class UserNotFoundError(AppException):
    status_code = 404  # Not Found
    error_code = "user_not_found"
    message = "找不到指定的使用者。"


class TokenRefreshError(AppException):
    status_code = 401
    error_code = "token_refresh_error"
    message = "無法刷新 Token，可能使用者已不存在或被停用。"
