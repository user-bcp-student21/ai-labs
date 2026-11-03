DB_PATH_ENV = "WORKSHOP_DB_PATH"
UPLOAD_DIR_ENV = "WORKSHOP_UPLOAD_DIR"
JWT_SECRET_ENV = "WORKSHOP_JWT_SECRET"
AUTH_HEALTH_URL_ENV = "AUTH_HEALTH_URL"

DEFAULT_DB_PATH = "./data/workshop.db"
DEFAULT_UPLOAD_DIR = "./uploads"
DEFAULT_AUTH_HEALTH_URL = "http://localhost:8080/q/health"

BEARER_PREFIX = "Bearer "
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "reqflow-auth"
JWT_AUDIENCE = "reqflow-api"
JWT_REQUIRED_CLAIMS = ("exp", "iat", "sub", "role")

HEALTH_TIMEOUT_SECONDS = 3.0

MAX_UPLOAD_BYTES = 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = frozenset({".txt", ".md"})

INVALID_TOKEN_DETAIL = "Invalid token"
OWNER_MISMATCH_DETAIL = "Owner differs from the authenticated identity"
UPLOAD_REJECTED_DETAIL = "File name or extension is not allowed"
UPLOAD_TOO_LARGE_DETAIL = "File exceeds the upload size limit"
UPLOAD_EXISTS_DETAIL = "A file with this name already exists"
BACKEND_UNREACHABLE_DETAIL = "Backend health endpoint is unreachable"
