"""
Main DCS Parts Matching Agent.

Orchestrates the entire matching workflow from document ingestion
to final part recommendations.
"""

import time
from pathlib import Path
from typing import Optional
import uuid

from ..core.models import (
    DocumentSubmission, ProcessingRequest, MatchingResult,
    ExtractedFeatures, DocumentType, PartMatch
)
from ..core.config import get_settings
from ..database.vector_store import VectorStore
from ..processors.vision_processor import VisionProcessor
from ..processors.pdf_processor import PDFProcessor
from ..processors.text_processor import TextProcessor
from ..agents.matching_engine import MatchingEngine
from ..utils.logger import get_logger, RequestLogger
from ..utils.helpers import detect_document_type, generate_request_id

logger = get_logger(__name__)


class PartsMatchingAgent:
    """
    Main orchestration agent for DCS parts matching.

    Coordinates document processing, feature extraction, and intelligent matching.
    """

    def __init__(self):
        """Initialize the parts matching agent."""
        self.settings = get_settings()
        self.vector_store = VectorStore()
        self.matching_engine = MatchingEngine(self.vector_store)

        # Initialize processors
        self.vision_processor = VisionProcessor()
        self.pdf_processor = PDFProcessor()
        self.text_processor = TextProcessor()

        self.initialized = False

    async def initialize(self):
        """Initialize all components."""
        if not self.initialized:
            logger.info("Initializing Parts Matching Agent")
            await self.vector_store.initialize()
            self.initialized = True
            logger.info("Parts Matching Agent initialized successfully")

    async def process_request(
        self,
        request: ProcessingRequest
    ) -> MatchingResult:
        """
        Process a complete matching request.

        Args:
            request: ProcessingRequest with submission and parameters

        Returns:
            MatchingResult with matched parts and confidence scores

        Raises:
            ValueError: If request is invalid
            ProcessingError: If processing fails
        """
        if not self.initialized:
            await self.initialize()

        request_id = generate_request_id()
        start_time = time.time()

        with RequestLogger(request_id, "Parts Matching Request") as req_logger:
            try:
                # Step 1: Prepare document
                file_path = await self._prepare_document(request.submission)

                # Step 2: Extract features
                req_logger.info("Extracting features from submission")
                features = await self._extract_features(
                    file_path,
                    request.submission.document_type,
                    request.submission.text_description,
                    request.submission.additional_context
                )

                # Step 3: Find matching parts
                req_logger.info("Searching for matching parts")
                matches = await self.matching_engine.find_matches(
                    features,
                    max_alternatives=request.max_alternatives,
                    min_confidence=request.min_confidence_threshold
                )

                # Step 4: Build result
                result = self._build_result(
                    request_id,
                    features,
                    matches,
                    time.time() - start_time
                )

                req_logger.info(
                    f"Matching completed - Primary match: "
                    f"{result.primary_match.part.part_number if result.primary_match else 'None'} "
                    f"(confidence: {result.primary_match.confidence_score if result.primary_match else 0:.1f}%)"
                )

                return result

            except Exception as e:
                req_logger.error(f"Request processing failed: {e}")
                raise

    async def _prepare_document(self, submission: DocumentSubmission) -> Path:
        """
        Prepare document for processing.

        Args:
            submission: Document submission

        Returns:
            Path to prepared document

        Raises:
            ValueError: If no valid document source provided
        """
        if submission.file_path:
            return Path(submission.file_path)
        elif submission.file_url:
            # Download file (not implemented in this version)
            raise NotImplementedError("URL download not yet implemented")
        elif submission.file_bytes:
            # Save bytes to temp file
            temp_path = self.settings.upload_dir / f"temp_{uuid.uuid4()}.tmp"
            with open(temp_path, 'wb') as f:
                f.write(submission.file_bytes)
            return temp_path
        elif submission.text_description:
            # Create temp text file
            temp_path = self.settings.upload_dir / f"text_{uuid.uuid4()}.txt"
            with open(temp_path, 'w') as f:
                f.write(submission.text_description)
            return temp_path
        else:
            raise ValueError("No valid document source provided")

    async def _extract_features(
        self,
        file_path: Path,
        doc_type: DocumentType,
        text_description: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> ExtractedFeatures:
        """
        Extract features from document using appropriate processor.

        Args:
            file_path: Path to document
            doc_type: Document type
            text_description: Optional text description
            additional_context: Optional additional context

        Returns:
            ExtractedFeatures object
        """
        # Auto-detect type if unknown
        if doc_type == DocumentType.UNKNOWN:
            doc_type = detect_document_type(file_path)

        # Combine additional context with text description
        combined_context = []
        if text_description:
            combined_context.append(text_description)
        if additional_context:
            combined_context.append(additional_context)
        context = " | ".join(combined_context) if combined_context else None

        # Select and run appropriate processor
        if doc_type == DocumentType.PDF:
            features = await self.pdf_processor.process(file_path, context)
        elif doc_type == DocumentType.IMAGE:
            features = await self.vision_processor.process(file_path, context)
        elif doc_type == DocumentType.TEXT:
            features = await self.text_processor.process(file_path, context)
        elif doc_type in [DocumentType.CAD_DWG, DocumentType.CAD_DXF]:
            # CAD files would need specialized processing
            # For now, try vision processing on rendered image
            logger.warning(f"CAD file processing not fully implemented, using vision processor")
            features = await self.vision_processor.process(file_path, context)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

        # Merge text description into features if provided
        if text_description and not features.text_description:
            features.text_description = text_description

        return features

    def _build_result(
        self,
        request_id: str,
        features: ExtractedFeatures,
        matches: list[PartMatch],
        processing_time: float
    ) -> MatchingResult:
        """
        Build final MatchingResult from matches.

        Args:
            request_id: Request identifier
            features: Extracted features
            matches: List of matched parts
            processing_time: Processing time in seconds

        Returns:
            MatchingResult object
        """
        # Determine primary match and alternatives
        primary_match = matches[0] if matches else None
        alternative_matches = matches[1:] if len(matches) > 1 else []

        # Determine if human review is required
        requires_review = False
        review_reason = None

        if not primary_match:
            requires_review = True
            review_reason = "No suitable parts found in catalog"
        elif primary_match.confidence_score < 70:
            requires_review = True
            review_reason = f"Low confidence match ({primary_match.confidence_score:.1f}%)"
        elif primary_match.warnings:
            requires_review = True
            review_reason = f"Specification warnings: {'; '.join(primary_match.warnings[:2])}"

        return MatchingResult(
            request_id=request_id,
            extracted_features=features,
            primary_match=primary_match,
            alternative_matches=alternative_matches,
            processing_time_seconds=processing_time,
            requires_human_review=requires_review,
            review_reason=review_reason,
            metadata={
                "total_matches_found": len(matches),
                "primary_confidence": primary_match.confidence_score if primary_match else 0,
            }
        )

    async def get_system_health(self) -> dict:
        """
        Get system health status.

        Returns:
            Dictionary with health information
        """
        if not self.initialized:
            return {
                "status": "not_initialized",
                "message": "Agent not initialized"
            }

        try:
            stats = self.vector_store.get_stats()
            return {
                "status": "healthy",
                "vector_db_status": "connected",
                "catalog_entries_count": stats['catalog_count'],
                "drawing_repository_count": stats['drawings_count'],
                "version": self.settings.version
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
