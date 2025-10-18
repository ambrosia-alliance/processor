from pydantic import BaseModel, Field
from typing import List, Dict


class ClassificationRequest(BaseModel):
    text: str = Field(..., description="Text to classify")


class SentenceResult(BaseModel):
    text: str
    confidence: float


class CategoryResult(BaseModel):
    count: int
    avg_confidence: float
    sentences: List[SentenceResult]


class ClassificationResponse(BaseModel):
    categories: Dict[str, CategoryResult]


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str


class CategoriesResponse(BaseModel):
    categories: List[str]

