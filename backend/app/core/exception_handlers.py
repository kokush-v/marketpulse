from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    if is_error_response_payload(exc.detail):
        content = exc.detail
    else:
        content = {"detail": exc.detail}

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Request validation failed.",
        },
    )


def is_error_response_payload(detail: object) -> bool:
    return (
        isinstance(detail, dict)
        and isinstance(detail.get("code"), str)
        and isinstance(detail.get("message"), str)
    )
