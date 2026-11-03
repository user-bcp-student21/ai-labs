import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DB_PATH_ENV, DEFAULT_DB_PATH, DEFAULT_UPLOAD_DIR, UPLOAD_DIR_ENV
from app.database import open_database
from app.errors import ApiError, handle_api_error
from app.routes.health import build_health_router
from app.routes.requirements import build_requirements_router
from app.routes.tasks import build_tasks_router
from app.security import build_identity_dependency, load_jwt_secret


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_db = db_path or os.getenv(DB_PATH_ENV, DEFAULT_DB_PATH)
    selected_uploads = upload_dir or os.getenv(UPLOAD_DIR_ENV, DEFAULT_UPLOAD_DIR)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = open_database(selected_db)
    current_identity = build_identity_dependency(load_jwt_secret())

    app = FastAPI(title="Workshop Requirements API", version="0.1.0")
    app.state.connection = connection
    app.state.upload_dir = selected_uploads
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(ApiError, handle_api_error)
    app.include_router(build_tasks_router(connection, current_identity))
    app.include_router(build_requirements_router(Path(selected_uploads), current_identity))
    app.include_router(build_health_router(current_identity))

    @app.on_event("shutdown")
    def close_connection() -> None:
        connection.close()

    return app


app = create_app()
