#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.agents.coordinator import build_root_agent

agent = build_root_agent("gemini-3.7-flash")
assert agent is not None
print(f"ADK construction PASS: {getattr(agent, 'name', 'RecallCoordinatorAgent')}")
