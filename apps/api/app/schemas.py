from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChangeReason(str, Enum):
    BETTER_MACHINE_CAPACITY = "Better machine capacity"
    AVOID_SMALL_BATCH = "Avoid a small batch"
    PREFER_EQUAL_BATCH_SIZES = "Prefer equal batch sizes"
    QUALITY_REQUIREMENT = "Quality requirement"
    DELIVERY_URGENCY = "Delivery urgency"
    OTHER = "Other"


class OrderCreateRequest(BaseModel):
    # Cross-field business rules (max >= min, feasibility, duplicate preferred
    # sizes, ...) are deliberately left to services/validate.py rather than
    # duplicated here, so there is one place those rules can drift out of sync.
    # Omit to have the server assign the next sequential id (ORD-001, ORD-002, ...).
    order_id: str | None = None
    order_quantity_kg: float = Field(gt=0)
    available_batch_sizes_kg: list[float] = Field(default_factory=list)
    minimum_batch_size_kg: float = Field(gt=0)
    maximum_batch_size_kg: float = Field(gt=0)

    # Optional fields from the assignment's example (§2). Not persisted yet,
    # reserved for later ranking/history refinements.
    machine_capacity_kg: float | None = None
    delivery_priority: str | None = None
    product_type: str | None = None
    planner_id: str | None = None


class SuggestionOut(BaseModel):
    rank: int
    batches: list[float]
    score: float
    recommended: bool
    historically_preferred: bool
    explanation: str
    explanation_polished: str | None = None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    order_id: str
    suggestions: list[SuggestionOut]


class DecisionRequest(BaseModel):
    final_batches: list[float]
    change_reason: ChangeReason | None = None
    comment: str | None = None


class DecisionResponse(BaseModel):
    order_id: str
    final_batches: list[float]
    accepted_without_changes: bool
    change_count: int
    change_types: list[str]
    change_reason: str | None = None
    similarity_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderDetailResponse(BaseModel):
    order_id: str
    order_quantity_kg: float
    status: str
    suggestions: list[SuggestionOut]
    decision: DecisionResponse | None = None


class AnalyticsSummaryResponse(BaseModel):
    total_completed_orders: int
    acceptance_rate: float
    average_changes: float
    most_selected_batch_size: float | None
    most_common_change_reason: str | None
    average_similarity_score: float


class PreferencesResponse(BaseModel):
    batch_acceptance_rates: dict[str, float]
    similar_order_patterns: dict
