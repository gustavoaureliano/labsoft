from fastapi import FastAPI

from app.learning.router import router as learning_router
from app.learning.certificates import router as certificate_router
from app.media.router import router as media_router

app = FastAPI(title="AprovaAí API")
app.include_router(media_router)
app.include_router(learning_router)
app.include_router(certificate_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
