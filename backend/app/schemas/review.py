from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReviewIssueSchema(BaseModel):
    issue_id: Optional[str] = None
    severity: str
    line_number: int
    description: str
    rule_type: str
    ai_explanation: Optional[str] = None
    suggestion: Optional[str] = None
    source: Optional[str] = None  # "Static", "AI", or "Static + AI"
    confidence: Optional[int] = None
    file: Optional[str] = None


class ReviewBase(BaseModel):
    title: str = Field(..., max_length=255)
    language_id: Optional[Union[UUID, str]] = None


class ReviewCreateRequest(ReviewBase):
    source_code: Optional[str] = None
    repo_url: Optional[str] = Field(None, max_length=1024)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = None

    @model_validator(mode="after")
    def check_source_or_repo(self) -> ReviewCreateRequest:
        if not self.source_code and not self.repo_url:
            raise ValueError("Either source_code or repo_url must be provided.")
        return self


class LanguageSchema(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class ReviewResponse(ReviewBase):
    id: UUID
    user_id: UUID
    source_code: str
    improved_code: Optional[str] = None
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    quality_score: Optional[int] = None
    language: Optional[LanguageSchema] = None
    review_metadata: Dict[str, Any] = Field(default_factory=dict, serialization_alias="metadata")
    status: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    repo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int
    page: int
    size: int
