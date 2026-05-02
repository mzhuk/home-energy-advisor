from collections.abc import Sequence
from typing import Any, Literal

from asgi_correlation_id import correlation_id
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

ErrorCode = Literal[
    "validation_error",
    "not_found",
    "advice_not_found",
    "llm_unavailable",
    "llm_auth_error",
    "llm_timeout",
    "llm_bad_response",
    "prompt_injection_blocked",
    "off_topic_blocked",
    "pii_scrubbed_and_failed",
    "internal_error",
]


class AppError(Exception):
    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str = "The requested resource was not found.") -> None:
        super().__init__(
            code="not_found",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AdviceNotFoundError(AppError):
    def __init__(self, message: str = "No advice has been generated for this home yet.") -> None:
        super().__init__(
            code="advice_not_found",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class LLMUnavailableError(AppError):
    def __init__(self, message: str = "The configured model provider is unavailable.") -> None:
        super().__init__(
            code="llm_unavailable",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class LLMAuthError(AppError):
    def __init__(
        self,
        message: str = "The configured model provider rejected the request.",
    ) -> None:
        super().__init__(
            code="llm_auth_error",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class LLMTimeoutError(AppError):
    def __init__(self, message: str = "The configured model provider timed out.") -> None:
        super().__init__(
            code="llm_timeout",
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


class LLMBadResponseError(AppError):
    def __init__(self, message: str = "The configured model returned an invalid response.") -> None:
        super().__init__(
            code="llm_bad_response",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class PromptInjectionBlockedError(AppError):
    def __init__(self, message: str = "This request could not be sent to the advisor.") -> None:
        super().__init__(
            code="prompt_injection_blocked",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class OffTopicBlockedError(AppError):
    def __init__(
        self,
        message: str = "Please keep questions focused on home energy improvements.",
    ) -> None:
        super().__init__(
            code="off_topic_blocked",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PIIScrubFailedError(AppError):
    def __init__(self, message: str = "The request could not be handled safely.") -> None:
        super().__init__(
            code="pii_scrubbed_and_failed",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InternalAppError(AppError):
    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        super().__init__(
            code="internal_error",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def current_request_id() -> str:
    return correlation_id.get() or "req_unknown"


def error_response(
    *,
    code: ErrorCode,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": current_request_id(),
            }
        },
    )


def validation_details(errors: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "fields": [
            {
                "loc": list(error.get("loc", [])),
                "message": str(error.get("msg", "Invalid value.")),
                "type": str(error.get("type", "value_error")),
            }
            for error in errors
        ]
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            code="validation_error",
            message="The request payload or parameters are invalid.",
            status_code=422,
            details=validation_details(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return error_response(
                code="not_found",
                message="The requested resource was not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return error_response(
            code="internal_error",
            message="The request could not be completed.",
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
        return error_response(
            code="internal_error",
            message="An unexpected error occurred.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
