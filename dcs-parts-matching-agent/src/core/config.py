"""
Configuration management for DCS Parts Matching Agent.

This module handles all configuration settings, environment variables,
and system parameters.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "DCS Parts Matching Agent"
    version: str = "1.0.0"
    debug: bool = False

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list = ["*"]

    # File Upload Settings
    max_upload_size_mb: int = 50
    allowed_extensions: set = {".pdf", ".jpg", ".jpeg", ".png", ".dwg", ".dxf", ".txt"}
    upload_dir: Path = Path("data/uploads")

    # AI Model Settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    use_vision_model: str = "gpt-4-vision-preview"  # or "claude-3-opus-20240229"
    use_embedding_model: str = "text-embedding-3-large"
    temperature: float = 0.1
    max_tokens: int = 4096

    # OCR Settings
    ocr_engine: str = "tesseract"  # tesseract, aws_textract, azure_form_recognizer
    tesseract_path: Optional[str] = None
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_key: Optional[str] = None

    # Vector Database Settings
    vector_db_type: str = "chromadb"  # chromadb, faiss, pinecone
    vector_db_path: Path = Path("data/vector_db")
    embedding_dimension: int = 3072  # for text-embedding-3-large
    collection_name_catalog: str = "dcs_parts_catalog"
    collection_name_drawings: str = "technical_drawings"

    # Matching Engine Settings
    confidence_weights: dict = {
        "exact_match": 1.0,
        "dimensional_match": 0.9,
        "specification_match": 0.85,
        "semantic_similarity": 0.7,
        "visual_similarity": 0.75
    }
    critical_specs_weight: float = 2.0
    dimensional_tolerance_percent: float = 5.0

    # Catalog Settings
    catalog_path: Path = Path("data/catalog")
    drawings_path: Path = Path("data/drawings")
    auto_index_on_startup: bool = True
    reindex_interval_hours: int = 24

    # Logging Settings
    log_level: str = "INFO"
    log_file: Path = Path("logs/app.log")
    log_rotation: str = "500 MB"
    log_retention: str = "30 days"
    enable_request_logging: bool = True

    # Performance Settings
    cache_ttl_seconds: int = 3600
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 300
    enable_caching: bool = True

    # Database Settings (if using persistent storage)
    database_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()


def ensure_directories():
    """Create necessary directories if they don't exist."""
    settings = get_settings()
    directories = [
        settings.upload_dir,
        settings.vector_db_path,
        settings.catalog_path,
        settings.drawings_path,
        settings.log_file.parent
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
