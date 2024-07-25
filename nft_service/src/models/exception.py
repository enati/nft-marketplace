from pydantic import BaseModel


class BaseResponse(BaseModel):
    error: str
    detail: str


class ErrorExtra(BaseModel):
    model: str
    field: str
    value: str


class NotFoundError(BaseResponse):
    extra: ErrorExtra

    class Config:
        schema_extra = {
            "examples": [
                {
                    "error": "resource_not_found",
                    "detail": "Resource not found",
                    "extra": {
                        "model": "Template",
                        "field": "id",
                        "value": "5fbd0bb5cd85875f9825da6c",
                    },
                }
            ]
        }


class ConflictError(BaseResponse):
    extra: ErrorExtra

    class Config:
        schema_extra = {
            "examples": [
                {
                    "error": "resource_already_exists",
                    "detail": "Resource already exists",
                    "extra": {
                        "model": "Template",
                        "field": "name",
                        "value": "template_name",
                    },
                }
            ]
        }


class BadRequestError(BaseResponse):
    class Config:
        schema_extra = {"examples": [{"error": "invalid_request", "detail": "File extension not allowed"}]}


class ForbiddenError(BaseResponse):
    class Config:
        schema_extra = {
            "examples": [
                {
                    "error": "resource_forbiden",
                    "detail": "You dont have permission to access this resource",
                }
            ]
        }


class InternalServerError(BaseResponse):
    class Config:
        schema_extra = {"examples": [{"error": "internal_server", "detail": "No se pudo procesar la solicitud"}]}
