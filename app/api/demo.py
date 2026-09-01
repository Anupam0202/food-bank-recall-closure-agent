from fastapi import APIRouter, Header, HTTPException, Request

from app.dependencies import container
from app.security import require_admin, require_csrf
from app.services.demo_data import seed_demo

router = APIRouter(prefix="/api/demo")


def _authorize(request: Request, csrf: str | None):
    try:
        require_admin(request.session)
        require_csrf(request.session, csrf)
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/reset")
def reset(request: Request, x_csrf_token: str | None = Header(default=None)):
    _authorize(request, x_csrf_token)
    source, recall = seed_demo(container.repo, container.gemini)
    return {"status": "seeded", "recall_id": recall.id, "source_id": source.id}


@router.post("/seed")
def seed(request: Request, x_csrf_token: str | None = Header(default=None)):
    return reset(request, x_csrf_token)


@router.post("/run-golden-path")
async def run_golden_path(request: Request, x_csrf_token: str | None = Header(default=None)):
    _authorize(request, x_csrf_token)
    source, recall = seed_demo(container.repo, container.gemini)
    incident, created = await container.workflow.process(source, recall)
    return {"incident": incident.to_dict(), "created": created}
