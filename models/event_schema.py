"""
Canonical event schema using Pydantic models.
Defines the structure for normalized startup pitch events.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, HttpUrl
from uuid import uuid4


class Venue(BaseModel):
    """Physical or virtual venue information."""
    type: Literal["in-person", "online", "hybrid"]
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    coordinates: Optional[dict] = None  # {"lat": float, "lon": float}


class PitchSlots(BaseModel):
    """Information about pitch slot availability."""
    available: bool
    slot_count: Optional[int] = None
    application_deadline: Optional[datetime] = None
    application_url: Optional[HttpUrl] = None
    requirements: Optional[str] = None


class Registration(BaseModel):
    """Registration and ticketing information."""
    type: Literal["ticket", "rsvp", "application", "invite-only", "free"]
    url: Optional[HttpUrl] = None
    price: Optional[float] = 0.0
    currency: str = "USD"
    deadline: Optional[datetime] = None
    capacity: Optional[int] = None
    spots_remaining: Optional[int] = None


class Organizer(BaseModel):
    """Event organizer contact information."""
    name: str
    contact_email: Optional[str] = None
    website: Optional[HttpUrl] = None
    social_media: Optional[dict] = None  # {"twitter": "...", "linkedin": "..."}
    credibility_score: float = 0.5  # 0.0 to 1.0


class EventSource(BaseModel):
    """Provenance tracking for event data sources."""
    source: str  # "tavily", "eventbrite", "meetup", etc.
    source_id: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Optional[dict] = None


class CanonicalEvent(BaseModel):
    """
    Canonical event schema - the normalized representation
    of a startup pitch event from multiple sources.
    """
    # Core identifiers
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Basic information
    title: str
    description: str
    short_summary: Optional[str] = None  # 50-80 words for quick scanning
    
    # Temporal information
    start_utc: datetime
    end_utc: datetime
    timezone: str = "UTC"
    
    # Location
    venue: Venue
    online_url: Optional[HttpUrl] = None
    
    # Pitch-specific
    pitch_slots: Optional[PitchSlots] = None
    
    # Registration
    registration: Registration
    
    # Organizer
    organizer: Organizer
    
    # Categorization
    tags: List[str] = Field(default_factory=list)  # ["seed", "fintech", "demo-day"]
    industry: Optional[str] = None
    stage: Optional[List[str]] = None  # ["pre-seed", "seed", "series-a"]
    
    # Provenance & metadata
    sources: List[EventSource] = Field(default_factory=list)
    embedding_id: Optional[str] = None
    last_canonicalized_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["active", "cancelled", "past", "full"] = "active"
    
    # Computed fields
    credibility_score: float = 0.5  # Aggregate credibility
    last_verified_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Startup Pitch Night — Bangalore",
                "description": "Monthly pitch event for seed-stage startups...",
                "start_utc": "2026-01-20T14:00:00Z",
                "end_utc": "2026-01-20T17:00:00Z",
                "timezone": "Asia/Kolkata",
                "venue": {
                    "type": "in-person",
                    "name": "Namma Startup Hub",
                    "city": "Bangalore",
                    "country": "India"
                },
                "pitch_slots": {
                    "available": True,
                    "slot_count": 10,
                    "application_deadline": "2026-01-01T00:00:00Z"
                },
                "registration": {
                    "type": "ticket",
                    "url": "https://eventbrite.com/...",
                    "price": 0.0
                },
                "organizer": {
                    "name": "StartupX",
                    "contact_email": "hello@startupx.com"
                },
                "tags": ["seed", "demo-day", "fintech"]
            }
        }


class UserProfile(BaseModel):
    """User profile for personalized matching."""
    persona: Literal["founder", "investor"]
    name: Optional[str] = None
    startup_name: Optional[str] = None
    stage: Optional[str] = None  # "pre-seed", "seed", etc.
    industry: Optional[List[str]] = None
    location: Optional[str] = None
    pitch_deck_url: Optional[HttpUrl] = None
    preferences: dict = Field(default_factory=dict)


class SearchQuery(BaseModel):
    """User search query with filters."""
    intent: str  # Natural language query
    persona: Literal["founder", "investor"]
    
    # Filters
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    location: Optional[str] = None
    region: Optional[str] = None
    industry: Optional[List[str]] = None
    max_price: Optional[float] = None
    pitch_only: bool = False  # Only events with pitch slots
    online_only: bool = False
    
    # Pagination
    max_results: int = 10


class RankedEvent(BaseModel):
    """Event with ranking score and explanation."""
    event: CanonicalEvent
    score: float  # 0.0 to 1.0
    explanation: str  # Why this event matches
    match_factors: dict  # Breakdown of scoring factors
