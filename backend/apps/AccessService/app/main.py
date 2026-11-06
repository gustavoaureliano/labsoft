import os
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException

SUBSCRIPTION_URL = os.getenv("SUBSCRIPTION_URL", "http://localhost:8003")

COMPLETE_PLAN_ITEM = 0  # reserved item_id: subscription to the whole catalog

app = FastAPI(title="Servico de Acesso")


class ContentType(str, Enum):
    VIDEO = "video"
    RESUMO = "resumo"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/access")
async def check_access(user_id: int, item_id: int, content_type: ContentType) -> dict:
    """Prototype rule: allowed iff the user subscribes to the item or to the complete plan."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{SUBSCRIPTION_URL}/api/subscriptions/{user_id}")
            r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"subscription service error: {e}")

    owned = r.json()["item_ids"]
    allowed = item_id in owned or COMPLETE_PLAN_ITEM in owned
    return {
        "user_id": user_id,
        "item_id": item_id,
        "content_type": content_type,
        "access": "allowed" if allowed else "denied",
    }
