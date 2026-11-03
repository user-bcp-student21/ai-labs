from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


async def handle_api_error(_: Request, error: ApiError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
