import urllib3

from app.config import BACKEND_UNREACHABLE_DETAIL, HEALTH_TIMEOUT_SECONDS
from app.errors import ApiError


def fetch_backend_health(url: str) -> tuple[int, str]:
    try:
        with urllib3.PoolManager() as http:
            response = http.request("GET", url, timeout=HEALTH_TIMEOUT_SECONDS)
    except urllib3.exceptions.HTTPError as error:
        raise ApiError(502, BACKEND_UNREACHABLE_DETAIL) from error
    return response.status, response.data.decode("utf-8", errors="replace")
