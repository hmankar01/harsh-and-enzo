from typing import Optional

from pydantic import BaseModel, Field


class LocationSpec(BaseModel):
    """Workplace-type and location filters. All fields optional; an empty spec
    means "any workplace type, any location"."""

    remote: bool = False
    hybrid: bool = False
    onsite: bool = False
    cities: list[str] = Field(default_factory=list)
    radius_miles: Optional[int] = None


class SearchForm(BaseModel):
    """The structured recruiter form. Feeds BOTH the search query builder and the eval prompt."""

    experience_min: int = Field(0, ge=0, le=15)
    experience_max: int = Field(2, ge=0, le=20)
    exclude_seniority: list[str] = Field(default_factory=list)  # Senior/Staff/Principal/Lead
    skills: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    custom_domain: Optional[str] = None
    requires_sponsorship: bool = False
    location: LocationSpec = Field(default_factory=LocationSpec)
    exclusion_keywords: str = ""
    salary_floor: Optional[int] = None


class JobMatch(BaseModel):
    title: str = "Unknown title"
    company: str = "Unknown company"
    salary_range: str = "Not listed"
    experience_required: str = "Not stated"
    posted_date: str = "Unknown"
    url: str
    reason: str = ""
