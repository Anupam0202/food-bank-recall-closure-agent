#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import copy
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.coordinator import AdkCoordinator
from app.config import Settings
from app.domain.enums import MatchCategory
from app.domain.models import Recall, new_id
from app.repositories.memory import InMemoryRepository
from app.services.demo_data import seed_demo
from app.services.gemini_service import GeminiService
from app.services.recall_sources import load_fixture, source_from_payload
from app.services.readiness_service import readiness_payload
from app.services.status_service import status_payload
from app.services.verification_service import VerificationService
from app.workflows.recall_workflow import RecallWorkflow


def recall_from(extraction, source_id: str) -> Recall:
    return Recall(
        id=new_id("recall"),
        recall_number=extraction.recall_number,
        event_id=extraction.event_id,
        classification=extraction.classification,
        product_description=extraction.product_description,
        brands=extraction.brands,
        upc_candidates=extraction.upc_candidates,
        lot_codes=extraction.lot_codes,
        date_codes=extraction.date_codes,
        reason=extraction.reason,
        distribution_pattern=extraction.distribution_pattern,
        recalling_firm=extraction.recalling_firm,
        source_id=source_id,
    )


async def build_data():
    repo = InMemoryRepository()
    gemini = GeminiService("mock", "gemini-3.7-flash")
    workflow = RecallWorkflow(repo, AdkCoordinator("mock", "gemini-3.7-flash"), "gemini-3.7-flash")

    source1, recall1 = seed_demo(repo, gemini)
    incident1, _ = await workflow.process(source1, recall1)
    review1 = next(
        match
        for match in repo.list("matches")
        if match.incident_id == incident1.id
        and match.category in {MatchCategory.IDENTIFIER_REVIEW, MatchCategory.SEMANTIC_OR_VISUAL_REVIEW}
    )
    workflow.resolve_match(review1.id, "Partner inspected package: recalled lot code not present")
    for task in [item for item in repo.list("tasks") if item.incident_id == incident1.id]:
        workflow.acknowledge_task(task.id, "Demo partner lead", "Quarantine or review action acknowledged")

    payload = copy.deepcopy(load_fixture(ROOT / "fixtures/recalls/synthetic_recall.json"))
    payload["recall_number"] = "SYNTHETIC-FB-2026-002"
    payload["event_id"] = "SYNTHETIC-EVENT-002"
    payload["title"] = "Second Pantry Response Drill"
    source2 = source_from_payload(
        payload,
        "SYNTHETIC_DEMO",
        "fixture://synthetic_recall_second.json",
        "Synthetic demonstration data — not an official recall or public alert.",
    )
    recall2 = recall_from(gemini.extract_recall(payload), source2.id)
    incident2, _ = await workflow.process(source2, recall2)
    return repo, incident2


def fake_url_for(name: str, **kwargs) -> str:
    if name == "static":
        return (kwargs.get("path") or "").lstrip("/")
    return "#"


def request_for(path: str):
    return SimpleNamespace(url=SimpleNamespace(path=path))


def render() -> None:
    repo, active_incident = asyncio.run(build_data())
    output = ROOT / "preview"
    output.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "app/static/styles.css", output / "styles.css")
    shutil.copy2(ROOT / "app/static/app.js", output / "app.js")

    env = Environment(
        loader=FileSystemLoader(ROOT / "app/templates"),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["url_for"] = fake_url_for
    settings = Settings()
    common = {
        "settings": settings,
        "system_status": status_payload(settings),
        "readiness": readiness_payload(settings),
        "csrf_token": "preview-csrf",
        "is_admin": True,
    }

    incidents = sorted(repo.list("incidents"), key=lambda item: item.created_at, reverse=True)
    inventory = repo.list("inventory")
    tasks = repo.list("tasks")
    audit_events = repo.list("audit_events")
    recent_audit = sorted(audit_events, key=lambda item: item.created_at, reverse=True)[:6]
    counts = {
        "active": sum(1 for item in incidents if str(item.state) not in {"INTERNAL_CLOSED", "FAILED_TERMINAL"}),
        "closed": sum(1 for item in incidents if str(item.state) == "INTERNAL_CLOSED"),
        "quarantined": sum(1 for item in inventory if str(item.status) == "QUARANTINED"),
        "review": sum(1 for item in inventory if str(item.status) == "HUMAN_REVIEW"),
        "open_tasks": sum(1 for item in tasks if str(item.status) == "OPEN"),
    }
    dashboard = env.get_template("dashboard.html").render(
        **common,
        request=request_for("/"),
        incidents=incidents,
        inventory=inventory,
        tasks=tasks,
        recent_audit=recent_audit,
        counts=counts,
    )
    (output / "dashboard.html").write_text(dashboard, encoding="utf-8")

    incident = repo.get("incidents", active_incident.id)
    recall = repo.get("recalls", incident.recall_id)
    source = repo.get("recall_sources", recall.source_id)
    matches = [item for item in repo.list("matches") if item.incident_id == incident.id]
    incident_tasks = [item for item in tasks if item.incident_id == incident.id]
    incident_audit = sorted(
        [item for item in audit_events if item.incident_id == incident.id],
        key=lambda item: item.created_at,
    )
    agencies = {item.id: item for item in repo.list("agencies")}
    incident_html = env.get_template("incident.html").render(
        **common,
        request=request_for(f"/incidents/{incident.id}"),
        print_mode=False,
        incident=incident,
        recall=recall,
        source=source,
        matches=matches,
        tasks=incident_tasks,
        audit=incident_audit,
        agencies=agencies,
        closure_blockers=VerificationService.closure_blockers(matches, incident_tasks, inventory),
    )
    (output / "incident.html").write_text(incident_html, encoding="utf-8")

    incident_map = {item.id: item for item in incidents}
    recall_map = {item.id: item for item in repo.list("recalls")}
    tasks_html = env.get_template("partner_tasks.html").render(
        **common,
        request=request_for("/partner/tasks"),
        tasks=tasks,
        agencies=agencies,
        incidents=incident_map,
        recalls=recall_map,
    )
    (output / "partner-tasks.html").write_text(tasks_html, encoding="utf-8")

    inventory_html = env.get_template("inventory.html").render(
        **common,
        request=request_for("/inventory"),
        inventory=inventory,
        agencies=agencies,
    )
    (output / "inventory.html").write_text(inventory_html, encoding="utf-8")

    readiness_html = env.get_template("readiness.html").render(
        **common,
        request=request_for("/readiness"),
    )
    (output / "readiness.html").write_text(readiness_html, encoding="utf-8")

    print(
        json.dumps(
            {
                "dashboard_counts": counts,
                "active_incident": incident.id,
                "tasks": len(tasks),
                "audit_events": len(audit_events),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    render()
