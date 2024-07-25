from nft_service.src.exceptions import BadRequest, Conflict, NotFound, InternalError
from nft_service.src.routers import nft_router, balance_router, user_router, transaction_router
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi import FastAPI, Request, status
from typing import Union, Any
from loguru import logger


def _setup_routers(app: FastAPI) -> None:
    app.include_router(nft_router.router, prefix=nft_router.ENDPOINT, tags=["NFT"])
    app.include_router(balance_router.router, prefix=balance_router.ENDPOINT, tags=["Use Balance"])
    app.include_router(user_router.router, prefix=user_router.ENDPOINT, tags=["User"])
    app.include_router(transaction_router.router, prefix=transaction_router.ENDPOINT, tags=["Transaction"])


def _setup_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    @app.exception_handler(Conflict)
    async def handle_custom_exception(
        request: Request,
        exc: Union[Conflict, NotFound],  # pylint: disable=unused-argument
    ) -> ORJSONResponse:
        logger.error("status={} error={} details={} extra={}", exc.status, exc.message, exc.details, exc.extra)
        extra = exc.extra if exc.extra else {}
        content: dict[str, Any] = dict(status_code=exc.status, error=exc.message, detail=exc.details, extra=extra)

        return ORJSONResponse(status_code=exc.status, content=content)

    @app.exception_handler(ValidationError)
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> ORJSONResponse:
        logger.error(
            "status={} error={} details={}", status.HTTP_422_UNPROCESSABLE_ENTITY, "validation_error", exc.errors()
        )
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(BadRequest)
    async def handle_bad_request_exception(
        request: Request,
        exc: Union[Conflict, NotFound],  # pylint: disable=unused-argument
    ) -> ORJSONResponse:
        logger.error("status={} error={} details={}", exc.status, exc.message, exc.details)
        content: dict[str, Any] = dict(status_code=exc.status, error=exc.message, detail=exc.details)
        return ORJSONResponse(status_code=exc.status, content=content)

    @app.exception_handler(InternalError)
    async def handle_internal_error_exception(
        request: Request,
        exc: Union[Conflict, NotFound],  # pylint: disable=unused-argument
    ) -> ORJSONResponse:
        logger.error("status={} error={} details={}", exc.status, exc.message, exc.details)
        content: dict[str, Any] = dict(status_code=exc.status, error=exc.message, detail=exc.details)
        return ORJSONResponse(status_code=exc.status, content=content)

    @app.exception_handler(Exception)
    async def handle_exception(request: Request, exc: Exception) -> ORJSONResponse:  # pylint: disable=unused-argument
        """Return a custom message and status code"""

        logger.exception("status=500 error=internal_server_error")

        content: dict[str, Any] = dict(error=f"Unknown error: '{str(exc)}'")

        return ORJSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
