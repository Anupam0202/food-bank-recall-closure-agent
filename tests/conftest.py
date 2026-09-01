"""Pytest configuration intentionally has no live-service side effects."""
import os

os.environ.setdefault("AI_MODE", "mock")
