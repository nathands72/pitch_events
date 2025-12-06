"""
ParserAgent - Extract and normalize event data from raw HTML or API responses.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import pytz
from loguru import logger

from models.event_schema import (
    CanonicalEvent,
    Venue,
    PitchSlots,
    Registration,
    Organizer,
    EventSource,
)


class ParserAgent:
    """
    ParserAgent: Extract structured event data from raw HTML or API JSON.
    Prioritizes machine-readable data (JSON-LD, microdata), falls back to heuristics.
    """
    
    def parse(
        self,
        raw_data: Dict[str, Any],
        source: str = "unknown"
    ) -> Optional[CanonicalEvent]:
        """
        Parse raw HTML or API JSON into canonical event.
        
        Args:
            raw_data: Dict with 'html', 'url', 'api_json', etc.
            source: Source identifier (tavily, eventbrite, etc.)
            
        Returns:
            CanonicalEvent or None if parsing fails
        """
        try:
            # Try JSON-LD first (most reliable)
            if "html" in raw_data:
                event = self._parse_jsonld(raw_data["html"])
                if event:
                    logger.info(f"Parsed event from JSON-LD: {event.title}")
                    return self._enrich_event(event, raw_data, source)
            
            # Try API JSON (for platform APIs)
            if "api_json" in raw_data:
                event = self._parse_api_json(raw_data["api_json"], source)
                if event:
                    logger.info(f"Parsed event from API: {event.title}")
                    return self._enrich_event(event, raw_data, source)
            
            # Fallback to heuristic parsing
            if "html" in raw_data:
                event = self._parse_heuristic(raw_data["html"], raw_data.get("url"))
                if event:
                    logger.info(f"Parsed event heuristically: {event.title}")
                    return self._enrich_event(event, raw_data, source)
            
            # Fallback to snippet-based parsing (for search results without HTML)
            if "snippet" in raw_data and "title" in raw_data:
                event = self._parse_snippet(raw_data)
                if event:
                    logger.info(f"Parsed event from snippet: {event.title}")
                    return self._enrich_event(event, raw_data, source)
            
            logger.warning(f"Failed to parse event from {source} - {raw_data}")
            return None
            
        except Exception as e:
            logger.error(f"Parser error: {e}")
            return None
    
    def _parse_jsonld(self, html: str) -> Optional[CanonicalEvent]:
        """Extract event from JSON-LD structured data."""
        import json
        
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Handle arrays
                if isinstance(data, list):
                    data = next((d for d in data if d.get('@type') == 'Event'), None)
                
                if data and data.get('@type') == 'Event':
                    return self._build_event_from_jsonld(data)
                    
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return None
    
    def _build_event_from_jsonld(self, data: Dict) -> CanonicalEvent:
        """Build CanonicalEvent from JSON-LD data."""
        
        # Parse dates
        start_date = self._parse_date(data.get('startDate'))
        end_date = self._parse_date(data.get('endDate')) or start_date
        
        # Parse location
        venue = self._parse_location_jsonld(data.get('location', {}))
        
        # Parse organizer
        organizer_data = data.get('organizer', {})
        organizer = Organizer(
            name=organizer_data.get('name', 'Unknown'),
            contact_email=organizer_data.get('email'),
            website=organizer_data.get('url'),
        )
        
        # Parse offers (registration/tickets)
        offers = data.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        
        registration = Registration(
            type=self._infer_registration_type(offers),
            url=offers.get('url'),
            price=float(offers.get('price', 0)),
            currency=offers.get('priceCurrency', 'USD'),
        )
        
        # Detect pitch slots from description
        description = data.get('description', '')
        pitch_slots = self._detect_pitch_slots(description)
        
        return CanonicalEvent(
            title=data.get('name', 'Untitled Event'),
            description=description,
            start_utc=start_date,
            end_utc=end_date,
            venue=venue,
            online_url=data.get('url') if venue.type == 'online' else None,
            pitch_slots=pitch_slots,
            registration=registration,
            organizer=organizer,
            tags=self._extract_tags(description),
        )
    
    def _parse_location_jsonld(self, location: Dict) -> Venue:
        """Parse location from JSON-LD."""
        if not location:
            return Venue(type="online")
        
        location_type = location.get('@type', '')
        
        if location_type == 'VirtualLocation':
            return Venue(type="online", name="Online Event")
        
        if location_type == 'Place':
            address = location.get('address', {})
            if isinstance(address, str):
                address_str = address
                city = None
                country = None
            else:
                address_str = address.get('streetAddress', '')
                city = address.get('addressLocality')
                country = address.get('addressCountry')
            
            return Venue(
                type="in-person",
                name=location.get('name'),
                address=address_str,
                city=city,
                country=country,
            )
        
        return Venue(type="online")
    
    def _parse_api_json(self, data: Dict, source: str) -> Optional[CanonicalEvent]:
        """Parse platform-specific API JSON (Eventbrite, Meetup, etc.)."""
        
        if source == "eventbrite":
            return self._parse_eventbrite_json(data)
        elif source == "meetup":
            return self._parse_meetup_json(data)
        
        return None
    
    def _parse_eventbrite_json(self, data: Dict) -> Optional[CanonicalEvent]:
        """Parse Eventbrite API response."""
        # TODO: Implement Eventbrite-specific parsing
        return None
    
    def _parse_meetup_json(self, data: Dict) -> Optional[CanonicalEvent]:
        """Parse Meetup API response."""
        # TODO: Implement Meetup-specific parsing
        return None
    
    def _parse_heuristic(self, html: str, url: Optional[str]) -> Optional[CanonicalEvent]:
        """Fallback heuristic parsing from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find title
        title = None
        for selector in ['h1', 'title', '.event-title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        if not title:
            return None
        
        # Extract text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Try to find dates
        dates = self._extract_dates_from_text(text)
        if not dates:
            return None
        
        start_date = dates[0]
        end_date = dates[1] if len(dates) > 1 else start_date
        
        return CanonicalEvent(
            title=title,
            description=text[:500],  # First 500 chars
            start_utc=start_date,
            end_utc=end_date,
            venue=Venue(type="online"),  # Default to online
            registration=Registration(type="rsvp", url=url),
            organizer=Organizer(name="Unknown"),
            pitch_slots=self._detect_pitch_slots(text),
            tags=self._extract_tags(text),
        )
    
    def _parse_snippet(self, raw_data: Dict[str, Any]) -> Optional[CanonicalEvent]:
        """
        Parse event from search result snippet (when HTML is not available).
        This is a lightweight parser for Tavily search results.
        """
        title = raw_data.get("title", "").strip()
        snippet = raw_data.get("snippet", "").strip()
        url = raw_data.get("url")
        
        if not title or not snippet:
            return None
        
        # Combine title and snippet for analysis
        combined_text = f"{title} {snippet}"
        
        # Try to extract dates from snippet
        dates = self._extract_dates_from_text(combined_text)
        
        # Detect pitch slots to determine if this is likely an event
        pitch_slots = self._detect_pitch_slots(combined_text)
        
        # If no dates found, check if this looks like a pitch event
        if not dates:
            # Check for event-related keywords
            event_keywords = ['summit', 'conference', 'event', 'meetup', 'demo day', 
                            'pitch', 'competition', 'hackathon', 'workshop']
            text_lower = combined_text.lower()
            is_likely_event = any(keyword in text_lower for keyword in event_keywords)
            
            if is_likely_event or pitch_slots:
                # Create event with estimated future date
                from datetime import timedelta
                default_date = datetime.utcnow() + timedelta(days=30)
                logger.warning(f"No dates found in snippet for: {title}. Using default date: {default_date}")
                
                # Extract tags and add 'date-uncertain' tag
                tags = self._extract_tags(combined_text)
                tags.append('date-uncertain')
                
                # Extract location hints from snippet
                venue = self._extract_venue_from_text(combined_text)
                
                return CanonicalEvent(
                    title=title,
                    description=snippet[:500] + " [Date uncertain - please verify]",
                    start_utc=default_date,
                    end_utc=default_date,
                    venue=venue,
                    registration=Registration(type="rsvp", url=url),
                    organizer=Organizer(name="Unknown"),
                    pitch_slots=pitch_slots,
                    tags=tags,
                )
            else:
                logger.debug(f"No dates found in snippet for: {title} and no event indicators")
                return None
        
        start_date = dates[0]
        end_date = dates[1] if len(dates) > 1 else start_date
        
        # Extract location hints from snippet
        venue = self._extract_venue_from_text(combined_text)
        
        # Extract tags
        tags = self._extract_tags(combined_text)
        
        return CanonicalEvent(
            title=title,
            description=snippet[:500],  # Use snippet as description
            start_utc=start_date,
            end_utc=end_date,
            venue=venue,
            registration=Registration(type="rsvp", url=url),
            organizer=Organizer(name="Unknown"),
            pitch_slots=pitch_slots,
            tags=tags,
        )
    
    def _extract_venue_from_text(self, text: str) -> Venue:
        """Extract venue information from text."""
        text_lower = text.lower()
        
        # Check for online indicators
        online_keywords = ['online', 'virtual', 'webinar', 'zoom', 'teams', 'meet']
        if any(keyword in text_lower for keyword in online_keywords):
            return Venue(type="online", name="Online Event")
        
        # Try to extract city names (simple heuristic)
        # Look for common patterns like "in [City]" or "at [Location]"
        city_pattern = r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        city_match = re.search(city_pattern, text)
        
        if city_match:
            city = city_match.group(1)
            return Venue(
                type="in-person",
                name=f"Event in {city}",
                city=city,
            )
        
        # Default to online if unclear
        return Venue(type="online")
    
    def _detect_pitch_slots(self, text: str) -> Optional[PitchSlots]:
        """Detect if event has pitch slots from text."""
        pitch_keywords = [
            'pitch', 'apply', 'demo', 'speaker', 'present',
            'application', 'submit', 'slot', 'opportunity'
        ]
        
        text_lower = text.lower()
        has_pitch = any(keyword in text_lower for keyword in pitch_keywords)
        
        if has_pitch:
            # Try to extract slot count
            slot_match = re.search(r'(\d+)\s*(?:pitch|slot|speaker)', text_lower)
            slot_count = int(slot_match.group(1)) if slot_match else None
            
            # Try to find deadline
            deadline = self._extract_deadline(text)
            
            return PitchSlots(
                available=True,
                slot_count=slot_count,
                application_deadline=deadline,
            )
        
        return None
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        
        # Stage keywords
        stage_keywords = {
            'pre-seed': ['pre-seed', 'preseed', 'idea stage'],
            'seed': ['seed stage', 'seed funding', 'seed round'],
            'series-a': ['series a', 'series-a'],
        }
        
        # Industry keywords
        industry_keywords = {
            'fintech': ['fintech', 'financial technology', 'payments'],
            'healthtech': ['healthtech', 'health tech', 'medical'],
            'saas': ['saas', 'software as a service'],
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml'],
            'ecommerce': ['ecommerce', 'e-commerce', 'retail'],
        }
        
        text_lower = text.lower()
        
        for tag, keywords in {**stage_keywords, **industry_keywords}.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)
        
        # Event type tags
        if 'demo day' in text_lower:
            tags.append('demo-day')
        if 'competition' in text_lower:
            tags.append('competition')
        
        return tags
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse ISO date string to datetime."""
        if not date_str:
            return datetime.utcnow()
        
        try:
            dt = date_parser.parse(date_str)
            # Convert to UTC if timezone-aware
            if dt.tzinfo:
                dt = dt.astimezone(pytz.UTC).replace(tzinfo=None)
            return dt
        except:
            return datetime.utcnow()
    
    def _extract_dates_from_text(self, text: str) -> List[datetime]:
        """Extract dates from plain text."""
        # Comprehensive regex patterns for various date formats
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO format: 2025-12-06
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY: 12/06/2025
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY: 06-12-2025
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}',  # Month DD, YYYY
            r'\d{1,2}(?:st|nd|rd|th)? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}',  # DD Month YYYY
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?',  # Month DD (current/next year)
            r'\d{1,2}(?:st|nd|rd|th)? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*',  # DD Month (current/next year)
        ]
        
        dates = []
        matched_strings = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match in matched_strings:
                    continue  # Skip duplicates
                    
                try:
                    dt = date_parser.parse(match, fuzzy=True)
                    # If no year specified, assume current or next year
                    if dt.year < datetime.now().year:
                        dt = dt.replace(year=datetime.now().year)
                    dates.append(dt)
                    matched_strings.append(match)
                    logger.debug(f"Extracted date '{match}' -> {dt}")
                except Exception as e:
                    logger.debug(f"Failed to parse date '{match}': {e}")
                    continue
                    
                if len(dates) >= 2:  # Take first 2 dates max
                    break
            
            if len(dates) >= 2:
                break
        
        if dates:
            logger.debug(f"Found {len(dates)} date(s) in text")
        else:
            logger.debug(f"No dates found. Tried patterns: {date_patterns}")
            logger.debug(f"Text sample: {text[:200]}")
        
        return dates
    
    def _extract_deadline(self, text: str) -> Optional[datetime]:
        """Extract application deadline from text."""
        deadline_pattern = r'deadline[:\s]+([A-Za-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})'
        match = re.search(deadline_pattern, text, re.IGNORECASE)
        
        if match:
            try:
                return date_parser.parse(match.group(1))
            except:
                pass
        
        return None
    
    def _infer_registration_type(self, offers: Dict) -> str:
        """Infer registration type from offers data."""
        price = float(offers.get('price', 0))
        
        if price == 0:
            return "free"
        else:
            return "ticket"
    
    def _enrich_event(
        self,
        event: CanonicalEvent,
        raw_data: Dict,
        source: str
    ) -> CanonicalEvent:
        """Add source provenance to event."""
        # Prepare raw_data dict for EventSource (must be dict, not string)
        source_raw_data = {
            'snippet': raw_data.get('snippet'),
            'title': raw_data.get('title'),
            'url': raw_data.get('url'),
        }
        
        event.sources.append(
            EventSource(
                source=source,
                source_url=raw_data.get('url'),
                fetched_at=datetime.utcnow(),
                raw_data=source_raw_data,
            )
        )
        return event


# Agent prompt for documentation
PARSER_AGENT_PROMPT = """
You are ParserAgent: extract structured event data from raw HTML or API JSON.

Input:
{
  "url": "https://...",
  "html": "raw HTML content",
  "api_json": {...} or null
}

Task:
1. Prioritize machine-readable data (JSON-LD, microdata)
2. If pitch-slot info present (words: 'pitch', 'apply', 'demo', 'speaker'),
   capture accurate slot info and deadlines
3. Normalize times to UTC and include timezone
4. Extract tags from description

Output:
Canonical event JSON (see schema)

Notes:
- Prefer JSON-LD over heuristics
- Use NER for organizer and pitch-slot detection
- Handle missing fields gracefully
"""
