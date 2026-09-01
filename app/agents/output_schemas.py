from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ConfidenceName = Literal["SOURCE_EXACT", "SOURCE_INFERRED", "AMBIGUOUS", "MISSING"]


class EvidenceSnippet(BaseModel):
    field: str = Field(description="Extracted field supported by this short quote")
    quote: str = Field(max_length=240, description="Short verbatim source passage")
    source_location: str = Field(default="unknown", max_length=120)


class RecallExtraction(BaseModel):
    recall_number: str = Field(min_length=1, max_length=120)
    event_id: str = Field(default="", max_length=120)
    title: str = Field(default="Recall source record", max_length=240)
    classification: str = Field(default="Unclassified", max_length=120)
    product_description: str = Field(min_length=1, max_length=4000)
    brands: list[str] = Field(default_factory=list, max_length=40)
    upc_candidates: list[str] = Field(default_factory=list, max_length=100)
    lot_codes: list[str] = Field(default_factory=list, max_length=100)
    date_codes: list[str] = Field(default_factory=list, max_length=100)
    reason: str = Field(min_length=1, max_length=4000)
    distribution_pattern: str = Field(default="Not supplied", max_length=2000)
    recalling_firm: str = Field(default="Not supplied", max_length=500)
    evidence: list[str] = Field(default_factory=list, max_length=40)
    source_passages: list[EvidenceSnippet] = Field(default_factory=list, max_length=60)
    ambiguities: list[str] = Field(default_factory=list, max_length=40)
    confidence_category: ConfidenceName = "AMBIGUOUS"

    @field_validator("brands", "upc_candidates", "lot_codes", "date_codes", "evidence", "ambiguities")
    @classmethod
    def trim_values(cls, values: list[str]) -> list[str]:
        return [str(value).strip()[:500] for value in values if str(value).strip()]


class PackageAssessmentSchema(BaseModel):
    summary: str = Field(min_length=1, max_length=800)
    visible_identifiers: list[str] = Field(default_factory=list, max_length=50)
    confidence: ConfidenceName = "AMBIGUOUS"
    evidence: list[EvidenceSnippet] = Field(default_factory=list, max_length=30)
    requires_human_review: Literal[True] = True


class CoordinatorRecommendation(BaseModel):
    summary: str = Field(min_length=1, max_length=1500)
    open_action_count: int = Field(ge=0)
    review_required: bool
    prohibited_actions: list[str] = Field(default_factory=lambda: ["dispose", "public_alert", "declare_safe"])
