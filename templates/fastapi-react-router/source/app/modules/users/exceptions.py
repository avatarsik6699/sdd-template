from app.core.exceptions import AppException


class UserNotFound(AppException):
    status_code = 404
    detail = "User not found"


class EmailAlreadyExists(AppException):
    status_code = 409
    detail = "Email already exists"
