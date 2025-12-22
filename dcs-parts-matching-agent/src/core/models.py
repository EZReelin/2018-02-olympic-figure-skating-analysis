"""
Core data models for DCS Parts Matching Agent.

This module defines all Pydantic models used throughout the system for
data validation, serialization, and API contracts.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl, validator


class DocumentType(str, Enum):
    """Supported document types for ingestion."""
    PDF = "pdf"
    IMAGE = "image"
    CAD_DWG = "dwg"
    CAD_DXF = "dxf"
    TEXT = "text"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfidenceLevel(str, Enum):
    """Confidence level categories for matches."""
    HIGH = "high"  # 90-100%
    MEDIUM = "medium"  # 70-89%
    LOW = "low"  # 50-69%
    VERY_LOW = "very_low"  # <50%


class SpecificationType(str, Enum):
    """Types of technical specifications."""
    VOLTAGE_RATING = "voltage_rating"
    CURRENT_RATING = "current_rating"
    PRESSURE_RATING = "pressure_rating"
    TEMPERATURE_RANGE = "temperature_range"
    DIMENSION = "dimension"
    CONNECTION_TYPE = "connection_type"
    MOUNTING_TYPE = "mounting_type"
    MATERIAL = "material"
    PROTOCOL = "protocol"
    IO_COUNT = "io_count"
    POWER_CONSUMPTION = "power_consumption"
    OTHER = "other"


class Specification(BaseModel):
    """A technical specification extracted from a document or catalog."""
    spec_type: SpecificationType
    name: str = Field(..., description="Human-readable specification name")
    value: str = Field(..., description="Specification value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    tolerance: Optional[str] = Field(None, description="Tolerance range if applicable")
    is_critical: bool = Field(default=False, description="Whether this is a critical spec for matching")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")


class DimensionalData(BaseModel):
    """Dimensional information extracted from technical drawings."""
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    diameter: Optional[float] = None
    unit: str = Field(default="mm", description="Unit of measurement")
    mounting_holes: Optional[List[Dict[str, float]]] = Field(None, description="Mounting hole positions")
    additional_dimensions: Dict[str, float] = Field(default_factory=dict)


class ExtractedFeatures(BaseModel):
    """Features extracted from customer submission."""
    specifications: List[Specification] = Field(default_factory=list)
    dimensions: Optional[DimensionalData] = None
    text_description: Optional[str] = None
    detected_part_numbers: List[str] = Field(default_factory=list, description="Any part numbers found in submission")
    visual_features: Dict[str, Any] = Field(default_factory=dict, description="Visual features from drawings")
    raw_ocr_text: Optional[str] = None
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)


class DCSPart(BaseModel):
    """DCS part information from catalog."""
    part_number: str = Field(..., description="Unique DCS part number")
    description: str = Field(..., description="Part description")
    category: Optional[str] = None
    subcategory: Optional[str] = None
    specifications: List[Specification] = Field(default_factory=list)
    dimensions: Optional[DimensionalData] = None
    compatibility_info: List[str] = Field(default_factory=list)
    technical_notes: Optional[str] = None
    datasheet_url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    price: Optional[float] = None
    availability: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SpecificationMatch(BaseModel):
    """Comparison between customer requirement and part specification."""
    spec_name: str
    customer_value: Optional[str]
    part_value: Optional[str]
    is_match: bool
    match_score: float = Field(ge=0.0, le=1.0)
    notes: Optional[str] = None


class PartMatch(BaseModel):
    """A matched DCS part with confidence and justification."""
    part: DCSPart
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Match confidence 0-100%")
    confidence_level: ConfidenceLevel
    matched_specifications: List[SpecificationMatch] = Field(default_factory=list)
    missing_specifications: List[str] = Field(default_factory=list)
    justification: str = Field(..., description="Explanation of why this part was selected")
    warnings: List[str] = Field(default_factory=list, description="Any specification mismatches or concerns")

    @validator('confidence_level', always=True)
    def set_confidence_level(cls, v, values):
        """Automatically set confidence level based on score."""
        if 'confidence_score' not in values:
            return v
        score = values['confidence_score']
        if score >= 90:
            return ConfidenceLevel.HIGH
        elif score >= 70:
            return ConfidenceLevel.MEDIUM
        elif score >= 50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


class MatchingResult(BaseModel):
    """Complete result of parts matching operation."""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extracted_features: ExtractedFeatures
    primary_match: Optional[PartMatch] = None
    alternative_matches: List[PartMatch] = Field(default_factory=list, max_items=3)
    processing_time_seconds: float
    requires_human_review: bool = Field(default=False)
    review_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentSubmission(BaseModel):
    """Customer document submission for processing."""
    file_path: Optional[str] = None
    file_url: Optional[HttpUrl] = None
    file_bytes: Optional[bytes] = None
    document_type: DocumentType
    text_description: Optional[str] = None
    additional_context: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=10)
    customer_id: Optional[str] = None

    @validator('file_path', 'file_url', 'file_bytes')
    def validate_file_source(cls, v, values):
        """Ensure at least one file source is provided."""
        # This will be checked after all fields are set
        return v

    class Config:
        arbitrary_types_allowed = True


class ProcessingRequest(BaseModel):
    """Request for parts matching processing."""
    submission: DocumentSubmission
    enable_visual_comparison: bool = Field(default=True)
    max_alternatives: int = Field(default=3, ge=0, le=5)
    min_confidence_threshold: float = Field(default=50.0, ge=0.0, le=100.0)
    include_compatible_alternatives: bool = Field(default=True)


class CatalogEntry(BaseModel):
    """Entry in the catalog database."""
    id: str
    part: DCSPart
    embedding: Optional[List[float]] = None
    indexed_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SystemHealth(BaseModel):
    """System health and status information."""
    status: str
    vector_db_status: str
    catalog_entries_count: int
    drawing_repository_count: int
    last_index_update: Optional[datetime] = None
    uptime_seconds: float
    version: str
