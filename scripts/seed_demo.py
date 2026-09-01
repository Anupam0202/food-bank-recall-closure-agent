#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.repositories.memory import InMemoryRepository
from app.services.demo_data import seed_demo
from app.services.gemini_service import GeminiService

repo = InMemoryRepository()
source, recall = seed_demo(repo, GeminiService("mock", "gemini-3.7-flash"))
print(f"Seeded source={source.id} recall={recall.recall_number} agencies={len(repo.list('agencies'))} inventory={len(repo.list('inventory'))}")
