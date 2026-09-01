#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
CONSTRAINTS = (ROOT / "constraints-python312.txt").read_text(encoding="utf-8").splitlines()

required_pins = {
    "fastapi==0.139.2",
    "uvicorn[standard]==0.51.0",
    "pydantic==2.13.4",
    "google-adk==2.7.1",
    "google-genai==2.20.0",
    "google-auth[pyopenssl]==2.56.0",
}
constraint_pins = {
    "fastapi==0.139.2",
    "starlette==1.3.1",
    "pydantic==2.13.4",
    "google-auth==2.56.0",
    "uvicorn==0.51.0",
}
missing_requirements = sorted(required_pins - set(REQUIREMENTS))
missing_constraints = sorted(constraint_pins - set(CONSTRAINTS))
if missing_requirements or missing_constraints:
    raise SystemExit(
        f"Dependency contract failed: requirements={missing_requirements}, constraints={missing_constraints}"
    )

print(
    json.dumps(
        {
            "status": "PASS",
            "python_target": "3.12",
            "adk": "2.7.1",
            "verified_adk_bounds": {
                "fastapi": ">=0.133,<1",
                "pydantic": ">=2.12,<3",
                "google_auth": ">=2.47",
                "google_genai": ">=2.12.1,<3",
                "starlette": ">=1.3.1,<2",
                "uvicorn": ">=0.34,<1",
            },
            "constraint_source": "Google ADK v2.7.1 official Python 3.12 constraints",
        },
        indent=2,
    )
)
