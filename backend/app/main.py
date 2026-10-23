from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.identity_access import (
    Settings,
    create_router,
)
from app.database import get_session as get_db

settings = Settings.from_env()
app = FastAPI(title="AprovaAí API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(
    create_router(
        get_db,
        settings,
    )
)