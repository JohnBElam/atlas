from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def envelope(
    data: Any = None,
    error: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "data": data,
        "error": error,
        "meta": meta or {},
    }


def success(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return envelope(data=data, error=None, meta=meta)


def error_envelope(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=envelope(data=None, error=message),
    )
