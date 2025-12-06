"""
EmbedderAgent - Create embeddings for canonical events.
"""
from typing import List
from openai import OpenAI
from loguru import logger

from models.event_schema import CanonicalEvent
from utils.config import get_settings


class EmbedderAgent:
    """
    EmbedderAgent: Create embeddings for canonical event text + metadata.
    Produces embedding vector and short canonical summary.
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
    
    def embed_event(self, event: CanonicalEvent) -> tuple[List[float], str]:
        """
        Create embedding and summary for an event.
        
        Args:
            event: CanonicalEvent to embed
            
        Returns:
            Tuple of (embedding_vector, short_summary)
        """
        # Generate summary first
        summary = self._generate_summary(event)
        
        # Create embedding text
        embedding_text = self._create_embedding_text(event)
        
        # Get embedding from OpenAI
        embedding = self._get_embedding(embedding_text)
        
        logger.info(f"Created embedding for event: {event.title}")
        
        return embedding, summary
    
    def _generate_summary(self, event: CanonicalEvent) -> str:
        """Generate 50-80 word summary of the event."""
        
        # Build summary from key fields
        parts = [event.title]
        
        # Add date
        date_str = event.start_utc.strftime("%B %d, %Y")
        parts.append(f"on {date_str}")
        
        # Add location
        if event.venue.type == "in-person" and event.venue.city:
            parts.append(f"in {event.venue.city}")
        elif event.venue.type == "online":
            parts.append("(online)")
        
        # Add pitch slots info
        if event.pitch_slots and event.pitch_slots.available:
            if event.pitch_slots.slot_count:
                parts.append(f"with {event.pitch_slots.slot_count} pitch slots available")
            else:
                parts.append("with pitch slots available")
        
        # Add registration info
        if event.registration.price == 0:
            parts.append("(free)")
        else:
            parts.append(f"({event.registration.currency} {event.registration.price})")
        
        # Add tags
        if event.tags:
            parts.append(f"Tags: {', '.join(event.tags[:3])}")
        
        summary = ". ".join(parts) + "."
        
        # Truncate if too long
        if len(summary) > 400:
            summary = summary[:397] + "..."
        
        return summary
    
    def _create_embedding_text(self, event: CanonicalEvent) -> str:
        """Create text for embedding from event fields."""
        
        parts = [
            f"Title: {event.title}",
            f"Description: {event.description[:500]}",  # Limit description length
        ]
        
        # Add organizer
        parts.append(f"Organizer: {event.organizer.name}")
        
        # Add location context
        if event.venue.city:
            parts.append(f"Location: {event.venue.city}, {event.venue.country or ''}")
        
        # Add tags
        if event.tags:
            parts.append(f"Tags: {', '.join(event.tags)}")
        
        # Add pitch slot context
        if event.pitch_slots and event.pitch_slots.available:
            parts.append("Pitch slots available for founders")
        
        return " | ".join(parts)
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector from OpenAI."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536  # text-embedding-3-small dimension


# Agent prompt for documentation
EMBEDDER_AGENT_PROMPT = """
You are EmbedderAgent: create embeddings for canonical events.

Input:
Canonical event JSON

Task:
1. Summarize the event in 50–80 words for quick scanning
2. Create embedding text from [title + description + tags + organizer + location]
3. Return embedding vector using the configured embedding model

Output:
{
  "summary": "50-80 word summary",
  "embedding": [0.123, 0.456, ...]
}

Notes:
- Use text-embedding-3-small or configured model
- Include pitch slot availability in embedding text
- Keep summary concise and scannable
"""
