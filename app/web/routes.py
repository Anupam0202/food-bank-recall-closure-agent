from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import container
from app.security import new_csrf_token, require_csrf, verify_secret
from app.services.readiness_service import readiness_payload
from app.services.status_service import status_payload
from app.services.verification_service import VerificationService

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def context(request: Request, **extra):
    request.session.setdefault("csrf_token", new_csrf_token())
    return {
        "request": request,
        "settings": container.settings,
        "system_status": status_payload(container.settings),
        "readiness": readiness_payload(container.settings),
        "csrf_token": request.session["csrf_token"],
        "is_admin": bool(request.session.get("is_admin")),
        **extra,
    }


def render_template(request: Request, name: str, *, status_code: int = 200, **extra):
    """Render using Starlette 1.3's request-first TemplateResponse contract."""
    return templates.TemplateResponse(
        request=request,
        name=name,
        context=context(request, **extra),
        status_code=status_code,
    )


def incident_context(incident_id: str) -> dict:
    incident = container.repo.get("incidents", incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    matches = [match for match in container.repo.list("matches") if match.incident_id == incident_id]
    tasks = [task for task in container.repo.list("tasks") if task.incident_id == incident_id]
    inventory = container.repo.list("inventory")
    audit = sorted(
        [event for event in container.repo.list("audit_events") if event.incident_id == incident_id],
        key=lambda event: event.created_at,
    )
    recall = container.repo.get("recalls", incident.recall_id)
    source = container.repo.get("recall_sources", recall.source_id) if recall else None
    blockers = VerificationService.closure_blockers(matches, tasks, inventory)
    agencies = {agency.id: agency for agency in container.repo.list("agencies")}
    return {
        "incident": incident,
        "matches": matches,
        "tasks": tasks,
        "audit": audit,
        "recall": recall,
        "source": source,
        "agencies": agencies,
        "closure_blockers": blockers,
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    incidents = sorted(container.repo.list("incidents"), key=lambda item: item.created_at, reverse=True)
    inventory, tasks = container.repo.list("inventory"), container.repo.list("tasks")
    audit = sorted(container.repo.list("audit_events"), key=lambda item: item.created_at, reverse=True)[:6]
    counts = {
        "active": sum(1 for item in incidents if str(item.state) not in {"INTERNAL_CLOSED", "FAILED_TERMINAL"}),
        "closed": sum(1 for item in incidents if str(item.state) == "INTERNAL_CLOSED"),
        "quarantined": sum(1 for item in inventory if str(item.status) == "QUARANTINED"),
        "review": sum(1 for item in inventory if str(item.status) == "HUMAN_REVIEW"),
        "open_tasks": sum(1 for item in tasks if str(item.status) == "OPEN"),
    }
    return render_template(request, "dashboard.html", incidents=incidents, inventory=inventory, tasks=tasks, recent_audit=audit, counts=counts)


@router.get("/incidents/{incident_id}", response_class=HTMLResponse)
def incident_page(incident_id: str, request: Request):
    return render_template(request, "incident.html", print_mode=False, **incident_context(incident_id))


@router.get("/incidents/{incident_id}/print", response_class=HTMLResponse)
def incident_print(incident_id: str, request: Request):
    return render_template(request, "incident.html", print_mode=True, **incident_context(incident_id))


@router.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request):
    return render_template(request, "inventory.html", inventory=container.repo.list("inventory"), agencies={agency.id: agency for agency in container.repo.list("agencies")})


@router.get("/partner/tasks", response_class=HTMLResponse)
def partner_tasks(request: Request):
    incidents = {incident.id: incident for incident in container.repo.list("incidents")}
    recalls = {recall.id: recall for recall in container.repo.list("recalls")}
    return render_template(request, "partner_tasks.html", tasks=container.repo.list("tasks"), agencies={agency.id: agency for agency in container.repo.list("agencies")}, incidents=incidents, recalls=recalls)


@router.get("/readiness", response_class=HTMLResponse)
def readiness_page(request: Request):
    return render_template(request, "readiness.html")


@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return render_template(request, "about.html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render_template(request, "login.html", error=None)


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, token: str = Form(...)):
    if not verify_secret(token, container.settings.demo_admin_token):
        return render_template(request, "login.html", error="Invalid administrator token", status_code=403)
    request.session["is_admin"] = True
    request.session["csrf_token"] = new_csrf_token()
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    try:
        require_csrf(request.session, csrf_token)
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Invalid CSRF token") from exc
    request.session.clear()
    return RedirectResponse("/", status_code=303)
