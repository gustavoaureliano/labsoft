from fastapi import FastAPI
from app.identity_access import (
    Settings,
    create_router,
)
from app.database import get_session as get_db
app = FastAPI(title="AprovaAí API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(
    create_router(
        get_db,
        Settings.from_env(),
    )
)