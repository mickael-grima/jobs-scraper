import pydantic
from pydantic import Field


class Company(pydantic.BaseModel):
    name: str = ...
    url: str | None = None
    logo: str | None = None
    actively_hiring: bool | None = None


class Location(pydantic.BaseModel):
    full_location: str = ...
    city: str = None
    region: str = None
    country: str = None


class LinkedInJob(pydantic.BaseModel):
    url: str = ...
    title: str = ...
    company: Company = ...
    location: Location = ...
    posted_time: str | None = None

    # Parsed on the full job page
    description: str | None = None
    tags: set[str] = Field(default_factory=set)
    criteria: dict[str, str] = Field(default_factory=dict)
