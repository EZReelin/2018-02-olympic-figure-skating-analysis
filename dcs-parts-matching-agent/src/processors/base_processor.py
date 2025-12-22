"""
Base document processor interface.

Defines the abstract base class for all document processors.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from ..core.models import ExtractedFeatures, DocumentType


class BaseDocumentProcessor(ABC):
    """Abstract base class for document processors."""

    def __init__(self):
        """Initialize the processor."""
        self.supported_types: list[DocumentType] = []

    @abstractmethod
    async def process(self, file_path: Path, additional_context: Optional[str] = None) -> ExtractedFeatures:
        """
        Process a document and extract features.

        Args:
            file_path: Path to the document
            additional_context: Optional additional context or instructions

        Returns:
            ExtractedFeatures object containing all extracted information

        Raises:
            ProcessingError: If processing fails
        """
        pass

    def supports(self, document_type: DocumentType) -> bool:
        """
        Check if this processor supports the given document type.

        Args:
            document_type: Type of document

        Returns:
            True if supported, False otherwise
        """
        return document_type in self.supported_types

    async def preprocess(self, file_path: Path) -> Path:
        """
        Preprocess document before feature extraction.

        Can be used for image enhancement, PDF page extraction, etc.

        Args:
            file_path: Path to the document

        Returns:
            Path to preprocessed file (may be same as input)
        """
        return file_path

    async def postprocess(self, features: ExtractedFeatures) -> ExtractedFeatures:
        """
        Postprocess extracted features.

        Can be used for validation, normalization, enrichment.

        Args:
            features: Extracted features

        Returns:
            Processed features
        """
        return features
