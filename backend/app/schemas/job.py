from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JDParseRequest(BaseModel):
    title: str | None = None
    jd: str = Field(..., min_length=1)
    experience_required: str | None = None
    education_required: str | None = None


class JDParseResult(BaseModel):
    responsibilities: list[str] = Field(default_factory=list)
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    deal_breakers: list[str] = Field(default_factory=list)
    scoring_dimensions: list[str] = Field(default_factory=list)


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    department: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    salary_range: str | None = Field(default=None, max_length=120)
    experience_required: str | None = Field(default=None, max_length=120)
    education_required: str | None = Field(default=None, max_length=120)
    jd: str = Field(..., min_length=1)
    responsibilities: list[str] = Field(default_factory=list)
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    deal_breakers: list[str] = Field(default_factory=list)
    scoring_dimensions: list[str] = Field(default_factory=list)


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    department: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    salary_range: str | None = Field(default=None, max_length=120)
    experience_required: str | None = Field(default=None, max_length=120)
    education_required: str | None = Field(default=None, max_length=120)
    jd: str | None = Field(default=None, min_length=1)
    responsibilities: list[str] | None = None
    must_have: list[str] | None = None
    nice_to_have: list[str] | None = None
    deal_breakers: list[str] | None = None
    scoring_dimensions: list[str] | None = None
    status: str | None = Field(default=None, pattern="^(open|closed)$")


class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime
    updated_at: datetime


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    department: str | None
    location: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0
    high_match_count: int = 0
    pending_count: int = 0
