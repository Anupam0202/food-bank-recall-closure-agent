"""Google ADK discovery entrypoint for local `adk web` and deployment tooling."""
from app.agents.coordinator import build_root_agent
from app.config import settings

root_agent = build_root_agent(settings.model_name)
