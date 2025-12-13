"""
Location matching utility with semantic understanding.
Uses LLM to determine if locations match semantically.
"""
from typing import Optional, Dict, Tuple
from openai import OpenAI
from loguru import logger

from utils.config import get_settings


class LocationMatcher:
    """
    Semantic location matcher using LLM.
    Caches results to minimize API calls.
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url if settings.openai_base_url else None
        )
        self.model = "gpt-4o-mini"  # Fast and cheap for simple yes/no questions
        self.cache: Dict[Tuple[str, str, str], bool] = {}
    
    def matches_location(
        self,
        query_location: str,
        event_city: Optional[str],
        event_country: Optional[str]
    ) -> bool:
        """
        Determine if event location matches query location semantically.
        
        Args:
            query_location: User's location query (e.g., "Bay Area", "India", "Bangalore")
            event_city: Event's city (e.g., "San Francisco", "Bangalore")
            event_country: Event's country (e.g., "USA", "India")
            
        Returns:
            True if locations match semantically, False otherwise
        """
        # Normalize inputs
        query_location = query_location.strip()
        event_city = event_city.strip() if event_city else ""
        event_country = event_country.strip() if event_country else ""
        
        # Check cache
        cache_key = (query_location.lower(), event_city.lower(), event_country.lower())
        if cache_key in self.cache:
            logger.debug(f"Cache hit for location match: {cache_key}")
            return self.cache[cache_key]
        
        # Try LLM-based matching
        try:
            result = self._llm_match(query_location, event_city, event_country)
            self.cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"LLM location matching failed: {e}, falling back to substring match")
            # Fallback to substring matching
            result = self._substring_match(query_location, event_city, event_country)
            self.cache[cache_key] = result
            return result
    
    def _llm_match(
        self,
        query_location: str,
        event_city: str,
        event_country: str
    ) -> bool:
        """Use LLM to determine if locations match semantically."""
        
        # Build event location description
        event_location_parts = []
        if event_city:
            event_location_parts.append(event_city)
        if event_country:
            event_location_parts.append(event_country)
        event_location = ", ".join(event_location_parts)
        
        if not event_location:
            return False
        
        # Create prompt
        prompt = f"""Does the query location "{query_location}" match the event location "{event_location}"?

Consider:
- Exact matches (e.g., "Bangalore" matches "Bangalore, India")
- Alternative names (e.g., "Bengaluru" matches "Bangalore")
- Regional matches (e.g., "Bay Area" matches "San Francisco, USA")
- Country matches (e.g., "India" matches "Bangalore, India")
- Nearby cities in the same metro area (e.g., "San Jose" is close to "San Francisco")

Answer with ONLY "yes" or "no"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a geography expert. Answer only 'yes' or 'no'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        
        answer = response.choices[0].message.content.strip().lower()
        result = answer == "yes"
        
        logger.info(f"LLM location match: '{query_location}' vs '{event_location}' = {result}")
        return result
    
    def _substring_match(
        self,
        query_location: str,
        event_city: str,
        event_country: str
    ) -> bool:
        """Fallback substring matching."""
        query_loc = query_location.lower()
        
        if event_city and query_loc in event_city.lower():
            return True
        if event_country and query_loc in event_country.lower():
            return True
        
        return False


# Global instance
_location_matcher: Optional[LocationMatcher] = None


def get_location_matcher() -> LocationMatcher:
    """Get or create the global location matcher instance."""
    global _location_matcher
    if _location_matcher is None:
        _location_matcher = LocationMatcher()
    return _location_matcher


def matches_location(
    query_location: str,
    event_city: Optional[str],
    event_country: Optional[str]
) -> bool:
    """
    Convenience function to check if locations match semantically.
    
    Args:
        query_location: User's location query
        event_city: Event's city
        event_country: Event's country
        
    Returns:
        True if locations match, False otherwise
    """
    matcher = get_location_matcher()
    return matcher.matches_location(query_location, event_city, event_country)
