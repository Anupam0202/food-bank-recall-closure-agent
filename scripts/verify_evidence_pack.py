#!/usr/bin/env python3
"""Verify a Recall Closure evidence-pack ZIP without cloud access."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.evidence_pack_service import verify_evidence_pack


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    if not args.zip_path.is_file():
        raise SystemExit(f"Evidence pack not found: {args.zip_path}")
    try:
        result = verify_evidence_pack(args.zip_path.read_bytes())
    except Exception as exc:
        raise SystemExit(f"Evidence verification FAILED: {exc}") from exc
    print(json.dumps(result, indent=2))
    print("Authenticity note: this self-contained manifest is unsigned; compare its root with a separately trusted record.")


if __name__ == "__main__":
    main()
