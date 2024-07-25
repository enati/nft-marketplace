from nft_service.src.models.exception import ErrorExtra
import sys
from typing import Any, Optional


class BaseException(Exception):
    def __init__(
        self,
        status: int = 500,
        message: str = "unknown_error",
        details: Optional[str] = None,
        exception: Optional[Exception] = None,
        context: Optional[Any] = None,
        extra: Optional[ErrorExtra] = None,
    ):
        super().__init__()
        self.status = status
        self.message = message
        self.details = details
        self.context = context
        self.exception = exception if exception else sys.exc_info()[1]
        self.extra = extra

    def __str__(self) -> str:
        exception_name = self.__class__.__name__
        return f"Exception: {exception_name} status: {self.status} message: {self.message} details: {self.details} "

    def __repr__(self) -> str:
        exception_name = self.__class__.__name__
        return (
            f"{exception_name}(status={self.status}, "
            f"message={self.message}, details={self.details} "
            f"context={self.context}, exception={self.exception})"
        )


class BadRequest(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["status"] = 400

        if "message" not in kwargs:
            kwargs["message"] = "invalid_request"

        super().__init__(*args, **kwargs)


class Unauthorized(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["status"] = 401

        if "message" not in kwargs:
            kwargs["message"] = "not_authorized"

        super().__init__(*args, **kwargs)


class Forbidden(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["status"] = 403

        if "message" not in kwargs:
            kwargs["message"] = "resource_forbiden"

        super().__init__(*args, **kwargs)


class NotFound(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["status"] = 404

        if "message" not in kwargs:
            kwargs["message"] = "resource_not_found"

        super().__init__(*args, **kwargs)


class Conflict(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["status"] = 409

        if "message" not in kwargs:
            kwargs["message"] = "resource_already_exists"

        super().__init__(*args, **kwargs)


class InternalError(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["status"] = 500

        if "message" not in kwargs:
            kwargs["message"] = "internal_error"

        super().__init__(*args, **kwargs)
