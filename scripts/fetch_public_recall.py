#!/usr/bin/env python3
"""Operator-only fixed-domain openFDA fetch; it never issues a public alert."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.recall_sources import OPENFDA_LIMITATION, fetch_openfda_by_recall_number

parser = argparse.ArgumentParser()
parser.add_argument("recall_number")
args = parser.parse_args()
result = fetch_openfda_by_recall_number(args.recall_number)
print(json.dumps({"source_url": result["source_url"], "record": result["record"], "limitation": OPENFDA_LIMITATION}, indent=2))
