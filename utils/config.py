"""
Configuration management for the pitch event finder.
Loads settings from environment variables.
"""
import os
from typing import Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # API Keys
    openai_api_key: str = ""
    tavily_api_key: str = ""
    eventbrite_api_key: str = ""
    meetup_api_key: str = ""
    
    # Vector Database
    vector_db_type: Literal["chroma", "pinecone", "weaviate"] = "chroma"
    chroma_persist_dir: str = "./data/chroma"
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "pitch-events"
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Models
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4-turbo-preview"
    
    # Search Settings
    search_max_results: int = 50
    cache_ttl_minutes: int = 30
    
    # Monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
