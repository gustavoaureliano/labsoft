from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.analytics.router import router as analytics_router
from app.communication.router import router as communication_router
from app.database import get_session
from app.integrations import Integrations, get_integrations
from app.library_interaction.router import router as library_interaction_router
from app.moderation.router import router as moderation_router
from app.seed import reset_and_seed_daniel_data

app = FastAPI(title="AprovaAí API")
app.include_router(library_interaction_router)
app.include_router(communication_router)
app.include_router(analytics_router)
app.include_router(moderation_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/testing/reset")
def reset_demo_state(
    session: Annotated[Session, Depends(get_session)],
    _integrations: Annotated[Integrations, Depends(get_integrations)],
) -> dict[str, object]:
    """Reset and re-seed Daniel's tables for deterministic E2E test execution (requires LEARNING_DEMO_MODE=true)."""
    summary = reset_and_seed_daniel_data(session)
    return {"status": "reset", "seeded": summary}
