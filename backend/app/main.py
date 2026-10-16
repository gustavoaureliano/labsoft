from fastapi import FastAPI

from app.media.router import router as media_router

app = FastAPI(title="AprovaAí API")
app.include_router(media_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
