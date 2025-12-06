"""
SearchAgent - Real-time web researcher for startup pitch events.
Uses Tavily API and platform APIs to find event listings.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from tavily import TavilyClient
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from models.event_schema import SearchQuery
from utils.config import get_settings


class SearchAgent:
    """
    SearchAgent: High-recall web researcher for startup pitch events.
    Uses Tavily and configured platform APIs.
    """
    
    def __init__(self):
        settings = get_settings()
        self.tavily_client = TavilyClient(api_key=settings.tavily_api_key)
        self.max_results = settings.search_max_results
        
        # Platform-specific domains to prioritize
        self.event_domains = [
            "eventbrite.com",
            "meetup.com",
            "linkedin.com",
            "facebook.com",
            "luma.com",
            "lu.ma",
            "partiful.com",
            "eventbrite.co.uk",
            "eventbrite.in",
        ]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def search(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """
        Execute high-recall search for pitch events.
        
        Args:
            query: SearchQuery with user intent and filters
            
        Returns:
            List of raw search hits with metadata
        """
        logger.info(f"SearchAgent executing query: {query.intent}")
        
        # Build Tavily search query
        search_params = self._build_search_params(query)
        
        # Execute Tavily search
        tavily_results = self._search_tavily(search_params)
        
        # TODO: Add platform-specific API searches
        # eventbrite_results = self._search_eventbrite(query)
        # meetup_results = self._search_meetup(query)
        
        # Combine and deduplicate by URL
        all_results = tavily_results
        unique_results = self._deduplicate_by_url(all_results)
        
        logger.info(f"SearchAgent found {len(unique_results)} unique results")
        return unique_results[:self.max_results]
    
    def _build_search_params(self, query: SearchQuery) -> Dict[str, Any]:
        """Build Tavily search parameters from user query."""
        
        # Enhance query with pitch-specific keywords
        enhanced_query = self._enhance_query(query)
        
        params = {
            "query": enhanced_query,
            "search_depth": "advanced",  # Use advanced for more comprehensive results
            "max_results": self.max_results,
            "include_domains": self.event_domains,
            "include_answer": False,  # We don't need AI-generated answers
            "include_raw_content": False,  # Save bandwidth
        }
        
        # Add date filters if specified
        if query.date_from or query.date_to:
            # Tavily doesn't have native date filtering, so we add it to the query
            if query.date_from:
                params["query"] += f" after:{query.date_from.strftime('%Y-%m-%d')}"
            if query.date_to:
                params["query"] += f" before:{query.date_to.strftime('%Y-%m-%d')}"
        
        return params
    
    def _enhance_query(self, query: SearchQuery) -> str:
        """Enhance user query with pitch-specific keywords."""
        base_query = query.intent
        
        # Add pitch-specific terms
        pitch_terms = ["startup pitch", "pitch event", "demo day", "pitch competition"]
        
        # Add persona-specific terms
        if query.persona == "founder":
            pitch_terms.extend(["pitch opportunity", "apply to pitch", "pitch slots"])
        else:  # investor
            pitch_terms.extend(["investor event", "pitch session", "startup showcase"])
        
        # Add location if specified
        location_part = ""
        if query.location:
            location_part = f" in {query.location}"
        elif query.region:
            location_part = f" in {query.region}"
        
        # Add industry if specified
        industry_part = ""
        if query.industry:
            industry_part = f" {' '.join(query.industry)}"
        
        # Combine: base query + location + industry + pitch terms (OR)
        enhanced = f"{base_query}{location_part}{industry_part} ({' OR '.join(pitch_terms[:3])})"
        
        return enhanced
    
    def _search_tavily(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute Tavily search and normalize results."""
        try:
            response = self.tavily_client.search(**params)
            
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", ""),
                    "source": "tavily",
                    "source_id": None,
                    "publish_date": item.get("published_date"),
                    "score": item.get("score", 0.5),
                    "raw_content": item.get("raw_content"),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
    
    def _search_eventbrite(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """
        Search Eventbrite API for pitch events.
        TODO: Implement Eventbrite API integration.
        """
        # Placeholder for Eventbrite API integration
        logger.info("Eventbrite search not yet implemented")
        return []
    
    def _search_meetup(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """
        Search Meetup API for pitch events.
        TODO: Implement Meetup API integration.
        """
        # Placeholder for Meetup API integration
        logger.info("Meetup search not yet implemented")
        return []
    
    def _deduplicate_by_url(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results by URL."""
        seen_urls = set()
        unique = []
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(result)
        
        return unique


# Agent prompt for documentation
SEARCH_AGENT_PROMPT = """
You are SearchAgent: high-recall web researcher for startup pitch events.

Input:
{
  "intent": "user's natural language query",
  "persona": "founder" | "investor",
  "date_from": "ISO datetime or null",
  "date_to": "ISO datetime or null",
  "location": "city/region or null",
  "industry": ["tag1", "tag2"] or null,
  "pitch_only": boolean
}

Task:
1. Use Tavily to execute high-recall searches for event pages
2. Search configured platform APIs (Eventbrite, Meetup, etc.)
3. Return top 50 raw hits with metadata

Output:
[
  {
    "title": "Event title",
    "snippet": "Brief description",
    "url": "https://...",
    "source": "tavily" | "eventbrite" | "meetup",
    "source_id": "platform-specific ID or null",
    "publish_date": "ISO datetime or null",
    "score": 0.0-1.0
  }
]

Notes:
- Prioritize event platform domains (eventbrite, meetup, luma, etc.)
- Use search depth "advanced" for comprehensive results
- Throttle requests to avoid rate limits
- Tag results by platform for downstream processing
"""
