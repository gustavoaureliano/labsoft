"""MOCK of the media/learning team's service. Fixed sample data, no storage.
The only real behavior: never hand out a content URL without asking AccessService first.
Replace with the real service at integration time, keeping the same two endpoints."""
import os

import httpx
from fastapi import FastAPI, HTTPException

ACCESS_URL = os.getenv("ACCESS_URL", "http://localhost:8001")
SAMPLE_VIDEO = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
SAMPLE_PDF = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

# item_id = catalog position + 1, same mapping the frontend uses (src/lib/api/commerce.ts)
LESSONS = {
    "demo-quantica-introducao": {"item_id": 1, "course_id": "fisica-quantica", "title": "Introdução e contexto histórico", "duration_seconds": 1080},
    "demo-quantica-corpo-negro": {"item_id": 1, "course_id": "fisica-quantica", "title": "Radiação de corpo negro", "duration_seconds": 1440},
    "demo-mecanica-leis-newton": {"item_id": 2, "course_id": "fisica-enem-mecanica", "title": "Leis de Newton e suas aplicações", "duration_seconds": 1440},
}
DOCUMENTS = {
    "mapa-quantica": {"item_id": 1, "title": "Dualidade onda-partícula"},
    "exercicios-quantica": {"item_id": 1, "title": "Lista de exercícios: modelos atômicos"},
    "resumo-celula": {"item_id": 3, "title": "Resumo: organelas celulares"},
}

# item_id -> owner (teacher) id
OWNERS = {1: 101, 2: 102, 3: 103, 4: 102, 5: 104}

app = FastAPI(title="Mock de Conteudo")


async def require_access(user_id: int, item_id: int, content_type: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                f"{ACCESS_URL}/api/access",
                params={"user_id": user_id, "item_id": item_id, "content_type": content_type},
            )
            r.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(503, "access check unavailable")  # fail closed
    if r.json()["access"] != "allowed":
        raise HTTPException(403, "Você não tem acesso a este conteúdo.")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/items/owners")
def owners() -> dict[str, int]:
    return {str(k): v for k, v in OWNERS.items()}


@app.get("/api/learning/lessons/{lesson_id}/playback")
async def playback(lesson_id: str, user_id: int = 1) -> dict:
    lesson = LESSONS.get(lesson_id)
    if lesson is None:
        raise HTTPException(404, "lesson not found")
    await require_access(user_id, lesson["item_id"], "video")
    return {
        "id": lesson_id, "course_id": lesson["course_id"], "title": lesson["title"], "description": "",
        "position": 1, "media_id": f"media-{lesson_id}", "duration_seconds": lesson["duration_seconds"],
        "playable": True, "position_seconds": 0, "completed": False, "content_url": SAMPLE_VIDEO,
    }


@app.get("/api/documents/{document_id}")
async def document(document_id: str, user_id: int = 1) -> dict:
    doc = DOCUMENTS.get(document_id)
    if doc is None:
        raise HTTPException(404, "document not found")
    await require_access(user_id, doc["item_id"], "resumo")
    return {"id": document_id, "title": doc["title"], "content_url": SAMPLE_PDF}
