"""
Vector database integration supporting multiple backends.
"""
from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from models.event_schema import CanonicalEvent, RankedEvent
from utils.config import get_settings


class VectorDB(Protocol):
    """Protocol for vector database implementations."""
    
    def add_event(self, event: CanonicalEvent, embedding: List[float]) -> None:
        """Add or update an event in the vector database."""
        ...
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar events."""
        ...
    
    def get_event(self, event_id: str) -> Optional[CanonicalEvent]:
        """Retrieve a specific event by ID."""
        ...
    
    def delete_event(self, event_id: str) -> None:
        """Delete an event from the database."""
        ...


class ChromaVectorDB:
    """Chroma vector database implementation."""
    
    def __init__(self):
        settings = get_settings()
        
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="pitch_events",
            metadata={"description": "Startup pitch events collection"}
        )
        
        logger.info(f"Initialized Chroma DB at {settings.chroma_persist_dir}")
    
    def add_event(self, event: CanonicalEvent, embedding: List[float]) -> None:
        """Add or update an event in Chroma."""
        
        # Prepare metadata (Chroma requires flat dict)
        metadata = {
            "title": event.title,
            "start_utc": event.start_utc.isoformat(),
            "end_utc": event.end_utc.isoformat(),
            "venue_type": event.venue.type,
            "venue_city": event.venue.city or "",
            "venue_country": event.venue.country or "",
            "has_pitch_slots": event.pitch_slots is not None,
            "registration_type": event.registration.type,
            "registration_price": event.registration.price or 0.0,
            "organizer_name": event.organizer.name,
            "tags": ",".join(event.tags),
            "status": event.status,
        }
        
        # Store event JSON as document
        document = event.model_dump_json()
        
        # Upsert to collection
        self.collection.upsert(
            ids=[event.event_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )
        
        logger.info(f"Added event {event.event_id} to Chroma")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar events in Chroma."""
        
        # Build where clause from filters
        where = None
        if filters:
            where = self._build_where_clause(filters)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results["ids"]:
            for i, event_id in enumerate(results["ids"][0]):
                formatted.append({
                    "event_id": event_id,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                })
        
        return formatted
    
    def get_event(self, event_id: str) -> Optional[CanonicalEvent]:
        """Retrieve a specific event by ID."""
        result = self.collection.get(
            ids=[event_id],
            include=["documents"]
        )
        
        if result["documents"]:
            import json
            event_dict = json.loads(result["documents"][0])
            return CanonicalEvent(**event_dict)
        
        return None
    
    def delete_event(self, event_id: str) -> None:
        """Delete an event from Chroma."""
        self.collection.delete(ids=[event_id])
        logger.info(f"Deleted event {event_id} from Chroma")
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict:
        """Build Chroma where clause from filters."""
        where = {}
        
        if "venue_type" in filters:
            where["venue_type"] = filters["venue_type"]
        
        if "has_pitch_slots" in filters:
            where["has_pitch_slots"] = filters["has_pitch_slots"]
        
        if "status" in filters:
            where["status"] = filters["status"]
        
        return where if where else None


def get_vector_db() -> VectorDB:
    """Factory function to get the configured vector database."""
    settings = get_settings()
    
    if settings.vector_db_type == "chroma":
        return ChromaVectorDB()
    elif settings.vector_db_type == "pinecone":
        # TODO: Implement Pinecone
        raise NotImplementedError("Pinecone not yet implemented")
    elif settings.vector_db_type == "weaviate":
        # TODO: Implement Weaviate
        raise NotImplementedError("Weaviate not yet implemented")
    else:
        raise ValueError(f"Unknown vector DB type: {settings.vector_db_type}")
