from __future__ import annotations

from pathlib import Path

from app.domain.enums import InventoryStatus
from app.domain.models import Agency, InventoryItem, Recall, new_id
from app.repositories.base import Repository
from app.services.gemini_service import GeminiService
from app.services.recall_sources import load_fixture, source_from_payload

ROOT = Path(__file__).resolve().parents[2]


def seed_demo(repo: Repository, gemini: GeminiService):
    repo.reset()
    agencies = [
        Agency("agency_north", "Northside Community Pantry", "North District", "Rina — site lead"),
        Agency("agency_river", "Riverside Family Shelf", "River District", "Morgan — volunteer lead"),
    ]
    for agency in agencies:
        repo.put("agencies", agency.id, agency)

    inventory = [
        InventoryItem(
            id="item_exact",
            agency_id="agency_north",
            name="Harvest Table Oat Bites 12 oz",
            brand="Harvest Table",
            upc="0-12345-67890-5",
            lot_code="HT-2409-A",
            date_code="2026-11-20",
            quantity=18,
            image_uri="/static/fixtures/exact-package.png",
            original_values={"status": InventoryStatus.AVAILABLE.value},
        ),
        InventoryItem(
            id="item_review",
            agency_id="agency_river",
            name="Harvest snack bites assorted",
            brand="Harvest Table",
            upc="012345678905",
            lot_code=None,
            date_code=None,
            quantity=6,
            image_uri="/static/fixtures/ambiguous-package.png",
            original_values={"status": InventoryStatus.AVAILABLE.value},
        ),
        InventoryItem(
            id="item_control",
            agency_id="agency_river",
            name="Meadow Rice Crackers 8 oz",
            brand="Meadow Pantry",
            upc="099999111112",
            lot_code="MP-0512",
            date_code="2027-01-12",
            quantity=24,
            image_uri="/static/fixtures/control-package.png",
            original_values={"status": InventoryStatus.AVAILABLE.value},
        ),
    ]
    for item in inventory:
        repo.put("inventory", item.id, item)

    payload = load_fixture(ROOT / "fixtures/recalls/synthetic_recall.json")
    source = source_from_payload(
        payload,
        provider="SYNTHETIC_DEMO",
        source_url="fixture://synthetic_recall.json",
        limitations="Synthetic demonstration data — not an official recall or public alert.",
    )
    extraction = gemini.extract_recall(payload)
    recall = Recall(
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
        source_id=source.id,
    )
    return source, recall
