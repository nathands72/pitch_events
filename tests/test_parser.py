"""
Example test for ParserAgent.
"""
import pytest
from datetime import datetime
from agents.parser_agent import ParserAgent
from models.event_schema import CanonicalEvent


def test_parse_jsonld():
    """Test parsing event from JSON-LD structured data."""
    
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": "Startup Pitch Night",
            "description": "Monthly pitch event for seed-stage startups in fintech",
            "startDate": "2026-01-20T14:00:00Z",
            "endDate": "2026-01-20T17:00:00Z",
            "location": {
                "@type": "Place",
                "name": "Tech Hub",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "123 Main St",
                    "addressLocality": "San Francisco",
                    "addressCountry": "US"
                }
            },
            "organizer": {
                "@type": "Organization",
                "name": "StartupX",
                "email": "hello@startupx.com"
            },
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "url": "https://example.com/register"
            }
        }
        </script>
    </head>
    <body>
        <h1>Startup Pitch Night</h1>
    </body>
    </html>
    """
    
    parser = ParserAgent()
    event = parser.parse({"html": html, "url": "https://example.com"}, source="test")
    
    assert event is not None
    assert event.title == "Startup Pitch Night"
    assert "fintech" in event.tags
    assert event.venue.city == "San Francisco"
    assert event.registration.price == 0.0


def test_detect_pitch_slots():
    """Test pitch slot detection from text."""
    
    html = """
    <html>
    <head><title>Demo Day 2026</title></head>
    <body>
        <h1>Demo Day 2026</h1>
        <p>We have 10 pitch slots available for seed-stage startups.
        Application deadline is January 1, 2026.</p>
        <p>Event date: January 20, 2026</p>
    </body>
    </html>
    """
    
    parser = ParserAgent()
    event = parser.parse({"html": html, "url": "https://example.com"}, source="test")
    
    assert event is not None
    assert event.pitch_slots is not None
    assert event.pitch_slots.available is True
    assert event.pitch_slots.slot_count == 10


def test_extract_tags():
    """Test tag extraction from description."""
    
    parser = ParserAgent()
    
    text = "Seed-stage fintech startups pitch to investors. AI and machine learning focus."
    tags = parser._extract_tags(text)
    
    assert "seed" in tags
    assert "fintech" in tags
    assert "ai" in tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
