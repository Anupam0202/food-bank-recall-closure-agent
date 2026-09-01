#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

if os.getenv("RUN_LIVE_GEMINI_TESTS") != "1":
    raise SystemExit("NOT RUN: set RUN_LIVE_GEMINI_TESTS=1 and GEMINI_API_KEY explicitly")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.gemini_service import GeminiService

payload = json.loads((ROOT / "fixtures/recalls/synthetic_recall.json").read_text())
service = GeminiService("live", os.getenv("MODEL_NAME", "gemini-3.7-flash"), os.environ["GEMINI_API_KEY"])
result = service.extract_recall(payload)
print(json.dumps({"status": "PASS", "model": service.model_name, "recall_number": result.recall_number, "metadata": service.last_call.__dict__}, indent=2))
