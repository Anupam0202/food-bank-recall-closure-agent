from fastapi import APIRouter

from app.dependencies import container
from app.services.readiness_service import readiness_payload
from app.services.status_service import status_payload

router = APIRouter()


@router.get("/healthz")
def healthz():
    return status_payload(container.settings)


@router.get("/api/system-status")
def system_status():
    return status_payload(container.settings)


@router.get("/api/readiness")
def readiness():
    return readiness_payload(container.settings)
