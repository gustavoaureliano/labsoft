from fastapi import FastAPI

app = FastAPI(title="AprovaAí API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
