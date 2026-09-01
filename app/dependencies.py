from __future__ import annotations

from dataclasses import dataclass

from app.agents.coordinator import AdkCoordinator
from app.config import Settings, settings
from app.media.cloud_storage import CloudStorageMediaStore
from app.media.local import LocalMediaStore
from app.repositories.firestore import FirestoreRepository
from app.repositories.memory import InMemoryRepository
from app.services.gemini_service import GeminiService
from app.workflows.recall_workflow import RecallWorkflow


@dataclass
class Container:
    settings: Settings
    repo: object
    media: object
    gemini: GeminiService
    coordinator: AdkCoordinator
    workflow: RecallWorkflow


def build_container(config: Settings = settings) -> Container:
    config.validate()
    repo = FirestoreRepository(config.google_cloud_project, config.firestore_database) if config.use_firestore else InMemoryRepository()
    media = CloudStorageMediaStore(config.gcs_bucket or "") if config.use_cloud_storage else LocalMediaStore(config.runtime_upload_dir)
    gemini = GeminiService(config.ai_mode, config.model_name, config.gemini_api_key, config.model_max_attempts)
    coordinator = AdkCoordinator(config.ai_mode, config.model_name)
    workflow = RecallWorkflow(repo, coordinator, config.model_name, config.model_max_attempts)
    return Container(config, repo, media, gemini, coordinator, workflow)


container = build_container()
