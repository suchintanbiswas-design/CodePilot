"""Test how Pydantic parses language_id in ReviewCreateRequest"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Union
from uuid import UUID

class ReviewBase(BaseModel):
    title: str = Field(..., max_length=255)
    language_id: Optional[Union[UUID, str]] = None

class ReviewCreateRequest(ReviewBase):
    source_code: Optional[str] = None
    repo_url: Optional[str] = Field(None, max_length=1024)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = None

    @model_validator(mode="after")
    def check_source_or_repo(self):
        if not self.source_code and not self.repo_url:
            raise ValueError("Either source_code or repo_url must be provided.")
        return self

# Test 1: Frontend sends language name "Python"
req1 = ReviewCreateRequest(title="Test", language_id="Python", source_code="x=1")
print("Test 1: language_id='Python'")
print("  type:", type(req1.language_id))
print("  value:", repr(req1.language_id))
print("  isinstance(str):", isinstance(req1.language_id, str))
print("  isinstance(UUID):", isinstance(req1.language_id, UUID))
print()

# Test 2: Frontend sends UUID string
req2 = ReviewCreateRequest(title="Test", language_id="724264b2-0c3b-4cdf-99c5-bcc6722952ff", source_code="x=1")
print("Test 2: language_id='724264b2-0c3b-...'")
print("  type:", type(req2.language_id))
print("  value:", repr(req2.language_id))
print("  isinstance(str):", isinstance(req2.language_id, str))
print("  isinstance(UUID):", isinstance(req2.language_id, UUID))
print()

# Test 3: What the JSON payload from the frontend looks like
import json
data = json.loads('{"title": "Test Review", "language_id": "Python", "source_code": "def hello(): pass"}')
req3 = ReviewCreateRequest(**data)
print("Test 3: From JSON (simulating frontend)")
print("  type:", type(req3.language_id))
print("  value:", repr(req3.language_id))
print("  isinstance(str):", isinstance(req3.language_id, str))
print()

# Now test what submit_review does with these values
print("=== submit_review logic ===")
for label, req in [("Python name", req1), ("UUID string", req2), ("JSON Python", req3)]:
    lang_id = None
    if isinstance(req.language_id, UUID):
        lang_id = req.language_id
        print(f"  {label}: Branch UUID => lang_id = {lang_id}")
    elif isinstance(req.language_id, str):
        print(f"  {label}: Branch str => would do DB lookup for '{req.language_id}'")
    else:
        print(f"  {label}: No branch matched! type={type(req.language_id)}")
