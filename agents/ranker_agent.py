"""
RankerAgent - Score and rank events for user queries.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import math
from loguru import logger

from models.event_schema import CanonicalEvent, SearchQuery, RankedEvent


class RankerAgent:
    """
    RankerAgent: Score canonical events for a given user request.
    Combines semantic similarity, recency, proximity, pitch-slot availability, and credibility.
    """
    
    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        "semantic_similarity": 0.50,
        "recency": 0.15,
        "logistics": 0.15,
        "pitch_slot_availability": 0.15,
        "credibility": 0.05,
    }
    
    def rank(
        self,
        query: SearchQuery,
        candidates: List[Dict[str, Any]],  # From vector DB search
    ) -> List[RankedEvent]:
        """
        Rank candidate events for the user query.
        
        Args:
            query: User's search query with filters
            candidates: List of dicts with 'event_id', 'document', 'score' from vector DB
            
        Returns:
            List of RankedEvent with scores and explanations
        """
        ranked = []
        
        for candidate in candidates:
            # Parse event from document
            import json
            event_dict = json.loads(candidate["document"])
            event = CanonicalEvent(**event_dict)
            
            # Calculate component scores
            scores = self._calculate_scores(query, event, candidate["score"])
            
            # Weighted total score
            total_score = sum(
                scores[key] * self.WEIGHTS[key]
                for key in self.WEIGHTS.keys()
            )
            
            # Generate explanation
            explanation = self._generate_explanation(query, event, scores)
            
            ranked.append(RankedEvent(
                event=event,
                score=total_score,
                explanation=explanation,
                match_factors=scores,
            ))
        
        # Sort by score descending
        ranked.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Ranked {len(ranked)} events")
        return ranked
    
    def _calculate_scores(
        self,
        query: SearchQuery,
        event: CanonicalEvent,
        semantic_score: float
    ) -> Dict[str, float]:
        """Calculate individual scoring components."""
        
        return {
            "semantic_similarity": semantic_score,
            "recency": self._score_recency(event),
            "logistics": self._score_logistics(query, event),
            "pitch_slot_availability": self._score_pitch_slots(query, event),
            "credibility": self._score_credibility(event),
        }
    
    def _score_recency(self, event: CanonicalEvent) -> float:
        """Score based on how soon the event is happening."""
        now = datetime.utcnow()
        days_until = (event.start_utc - now).days
        
        if days_until < 0:
            # Past event
            return 0.0
        elif days_until <= 7:
            # Very soon - highest score
            return 1.0
        elif days_until <= 30:
            # Within a month - good score
            return 0.8
        elif days_until <= 90:
            # Within 3 months - moderate score
            return 0.5
        else:
            # Far future - lower score
            return 0.3
    
    def _score_logistics(self, query: SearchQuery, event: CanonicalEvent) -> float:
        """Score based on location match and accessibility."""
        from utils.location_matcher import matches_location
        
        score = 0.5  # Base score
        
        # Online events are always accessible
        if event.venue.type == "online":
            score = 1.0
        
        # Location match using semantic matching
        if query.location:
            # Check if location matches semantically
            if matches_location(query.location, event.venue.city, event.venue.country):
                # Give higher score for city-level match, lower for country-level
                if event.venue.city:
                    score = 1.0
                else:
                    score = 0.7
        
        # Price consideration
        if query.max_price is not None:
            if event.registration.price <= query.max_price:
                score = min(score + 0.2, 1.0)
            else:
                score *= 0.5  # Penalize if over budget
        
        return score
    
    def _score_pitch_slots(self, query: SearchQuery, event: CanonicalEvent) -> float:
        """Score based on pitch slot availability."""
        
        # If user wants pitch-only and event doesn't have slots
        if query.pitch_only and not event.pitch_slots:
            return 0.0
        
        # No pitch slots
        if not event.pitch_slots or not event.pitch_slots.available:
            return 0.3  # Still some value for networking
        
        # Has pitch slots
        score = 1.0
        
        # Check deadline
        if event.pitch_slots.application_deadline:
            now = datetime.utcnow()
            days_until_deadline = (event.pitch_slots.application_deadline - now).days
            
            if days_until_deadline < 0:
                # Deadline passed
                return 0.0
            elif days_until_deadline <= 3:
                # Very urgent
                score = 0.7
            elif days_until_deadline <= 7:
                # Urgent
                score = 0.9
        
        return score
    
    def _score_credibility(self, event: CanonicalEvent) -> float:
        """Score based on organizer credibility and event quality."""
        
        score = event.organizer.credibility_score
        
        # Boost for multiple sources (cross-verified)
        if len(event.sources) > 1:
            score = min(score + 0.2, 1.0)
        
        # Boost for complete information
        completeness = 0.0
        if event.organizer.contact_email:
            completeness += 0.1
        if event.registration.url:
            completeness += 0.1
        if event.pitch_slots and event.pitch_slots.application_url:
            completeness += 0.1
        
        score = min(score + completeness, 1.0)
        
        return score
    
    def _generate_explanation(
        self,
        query: SearchQuery,
        event: CanonicalEvent,
        scores: Dict[str, float]
    ) -> str:
        """Generate human-readable explanation for the match."""
        
        reasons = []
        
        # Semantic match
        if scores["semantic_similarity"] > 0.7:
            reasons.append("strong semantic match to your query")
        
        # Location
        if query.location and event.venue.city:
            if query.location.lower() in event.venue.city.lower():
                reasons.append(f"located in {event.venue.city}")
        
        if event.venue.type == "online":
            reasons.append("online event (accessible anywhere)")
        
        # Pitch slots
        if event.pitch_slots and event.pitch_slots.available:
            if event.pitch_slots.application_deadline:
                deadline_str = event.pitch_slots.application_deadline.strftime("%b %d")
                reasons.append(f"pitch slots available (deadline {deadline_str})")
            else:
                reasons.append("pitch slots available")
        
        # Tags
        if query.industry and event.tags:
            matching_tags = set(query.industry) & set(event.tags)
            if matching_tags:
                reasons.append(f"matches {', '.join(matching_tags)}")
        
        # Price
        if event.registration.price == 0:
            reasons.append("free event")
        
        # Timing
        days_until = (event.start_utc - datetime.utcnow()).days
        if 0 < days_until <= 7:
            reasons.append("happening soon")
        
        if not reasons:
            reasons.append("relevant to your search")
        
        return "; ".join(reasons).capitalize()


# Agent prompt for documentation
RANKER_AGENT_PROMPT = """
You are RankerAgent: score and rank events for user queries.

Input:
{
  "user_profile": {...},
  "user_constraints": {...},
  "candidate_events": [...]
}

Task:
Score each candidate [0..1] using weighted features:
- semantic_similarity (0.5): from vector search
- recency (0.15): how soon is the event
- logistics (0.15): location match, price, accessibility
- pitch_slot_availability (0.15): slots available, deadline
- credibility (0.05): organizer trust, source count

Output:
Top N events with score and explanation

Example explanation:
"Strong semantic match to 'seed fintech'; located in Bangalore; pitch slots available (deadline Jan 1); free event"
"""
