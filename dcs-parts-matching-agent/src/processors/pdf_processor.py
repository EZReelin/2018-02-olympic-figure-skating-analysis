"""
PDF document processor.

Handles PDF files containing technical specifications, drawings, and datasheets.
Combines OCR for text extraction with vision analysis for diagrams.
"""

import re
from pathlib import Path
from typing import Optional, List
import PyPDF2
import pdfplumber

from ..core.models import ExtractedFeatures, DocumentType, Specification, SpecificationType
from ..core.config import get_settings
from ..utils.logger import get_logger
from .base_processor import BaseDocumentProcessor
from .vision_processor import VisionProcessor

logger = get_logger(__name__)


class PDFProcessor(BaseDocumentProcessor):
    """Process PDF documents with text and image content."""

    def __init__(self):
        """Initialize PDF processor."""
        super().__init__()
        self.supported_types = [DocumentType.PDF]
        self.settings = get_settings()
        self.vision_processor = VisionProcessor()

    async def process(self, file_path: Path, additional_context: Optional[str] = None) -> ExtractedFeatures:
        """
        Process PDF document.

        Args:
            file_path: Path to PDF file
            additional_context: Optional context

        Returns:
            ExtractedFeatures with combined text and image analysis
        """
        logger.info(f"Processing PDF: {file_path}")

        # Extract text from PDF
        text_content = self._extract_text(file_path)

        # Check if PDF has diagrams/drawings (low text content suggests drawings)
        has_drawings = len(text_content.strip()) < 500

        features = ExtractedFeatures(
            raw_ocr_text=text_content,
            extraction_metadata={"processor": "pdf", "has_drawings": has_drawings}
        )

        # If PDF appears to be primarily drawings, use vision analysis
        if has_drawings:
            logger.info("PDF appears to contain technical drawings, using vision analysis")
            # Convert first page to image and analyze
            vision_features = await self._analyze_pdf_with_vision(file_path, additional_context)
            features = self._merge_features(features, vision_features)
        else:
            # Extract structured information from text
            features = self._extract_from_text(text_content, features)

        return await self.postprocess(features)

    def _extract_text(self, file_path: Path) -> str:
        """
        Extract text from PDF.

        Args:
            file_path: Path to PDF

        Returns:
            Extracted text content
        """
        text_content = []

        try:
            # Try pdfplumber first (better for structured data)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}, trying PyPDF2")
            try:
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
            except Exception as e2:
                logger.error(f"PyPDF2 extraction also failed: {e2}")

        return "\n\n".join(text_content)

    def _extract_from_text(self, text: str, features: ExtractedFeatures) -> ExtractedFeatures:
        """
        Extract specifications from PDF text.

        Args:
            text: Extracted text
            features: Existing features to update

        Returns:
            Updated ExtractedFeatures
        """
        specifications = []

        # Extract part numbers
        part_number_patterns = [
            r'\b[A-Z]{2,4}[-\s]?\d{4,8}[-\s]?[A-Z0-9]{0,6}\b',  # Common part number format
            r'\bP/N:?\s*([A-Z0-9\-]+)\b',
            r'\bPart\s*Number:?\s*([A-Z0-9\-]+)\b'
        ]

        part_numbers = []
        for pattern in part_number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            part_numbers.extend(matches)

        features.detected_part_numbers = list(set(part_numbers))

        # Extract voltage ratings
        voltage_patterns = [
            r'(\d+\.?\d*)\s*-?\s*(\d+\.?\d*)?\s*V(?:DC|AC|)',
            r'Voltage:?\s*(\d+\.?\d*)\s*V',
            r'(\d+\.?\d*)\s*[Vv]olt'
        ]

        for pattern in voltage_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                value = match[0] if isinstance(match, tuple) else match
                specifications.append(
                    Specification(
                        spec_type=SpecificationType.VOLTAGE_RATING,
                        name="Voltage Rating",
                        value=value,
                        unit="V",
                        is_critical=True,
                        confidence=0.7
                    )
                )

        # Extract current ratings
        current_patterns = [
            r'(\d+\.?\d*)\s*[Aa]mp(?:ere)?s?',
            r'(\d+\.?\d*)\s*mA',
            r'Current:?\s*(\d+\.?\d*)\s*A'
        ]

        for pattern in current_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                value = match if isinstance(match, str) else match[0]
                specifications.append(
                    Specification(
                        spec_type=SpecificationType.CURRENT_RATING,
                        name="Current Rating",
                        value=value,
                        unit="A",
                        is_critical=True,
                        confidence=0.7
                    )
                )

        # Extract temperature ranges
        temp_patterns = [
            r'(-?\d+\.?\d*)\s*°?[CF]\s*to\s*(-?\d+\.?\d*)\s*°?[CF]',
            r'Operating\s*Temperature:?\s*(-?\d+\.?\d*)\s*to\s*(-?\d+\.?\d*)\s*°?[CF]'
        ]

        for pattern in temp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                value = f"{match[0]} to {match[1]}"
                specifications.append(
                    Specification(
                        spec_type=SpecificationType.TEMPERATURE_RANGE,
                        name="Operating Temperature",
                        value=value,
                        unit="°C",
                        is_critical=True,
                        confidence=0.7
                    )
                )

        # Extract pressure ratings
        pressure_patterns = [
            r'(\d+\.?\d*)\s*(?:PSI|bar|kPa)',
            r'Pressure:?\s*(\d+\.?\d*)'
        ]

        for pattern in pressure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match if isinstance(match, str) else match[0]
                specifications.append(
                    Specification(
                        spec_type=SpecificationType.PRESSURE_RATING,
                        name="Pressure Rating",
                        value=value,
                        is_critical=True,
                        confidence=0.6
                    )
                )

        # Extract dimensions
        dimension_patterns = [
            r'(\d+\.?\d*)\s*(?:mm|cm|inch|in)\s*[xX×]\s*(\d+\.?\d*)\s*(?:mm|cm|inch|in)',
            r'Dimensions?:?\s*(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)\s*[xX×]?\s*(\d+\.?\d*)?'
        ]

        for pattern in dimension_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take first match for dimensions
                break

        features.specifications = specifications
        features.text_description = self._extract_description(text)

        return features

    def _extract_description(self, text: str) -> str:
        """
        Extract product description from text.

        Args:
            text: Full text content

        Returns:
            Extracted description
        """
        # Look for description sections
        desc_patterns = [
            r'Description:?\s*([^\n]{50,500})',
            r'Product\s*Description:?\s*([^\n]{50,500})',
            r'Overview:?\s*([^\n]{50,500})'
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # Return first substantial paragraph if no description section found
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if len(para) > 100:
                return para[:500].strip()

        return ""

    async def _analyze_pdf_with_vision(
        self,
        file_path: Path,
        additional_context: Optional[str] = None
    ) -> ExtractedFeatures:
        """
        Analyze PDF pages as images using vision model.

        Args:
            file_path: Path to PDF
            additional_context: Optional context

        Returns:
            ExtractedFeatures from vision analysis
        """
        # For now, analyze first page
        # In production, you'd convert PDF pages to images
        # This is a simplified implementation
        logger.info("Vision analysis of PDF not fully implemented - would convert pages to images")

        return ExtractedFeatures(
            extraction_metadata={"vision_analysis": "not_implemented"}
        )

    def _merge_features(
        self,
        text_features: ExtractedFeatures,
        vision_features: ExtractedFeatures
    ) -> ExtractedFeatures:
        """
        Merge features from text and vision analysis.

        Args:
            text_features: Features from text extraction
            vision_features: Features from vision analysis

        Returns:
            Merged ExtractedFeatures
        """
        # Combine specifications, removing duplicates
        all_specs = text_features.specifications + vision_features.specifications

        # Prefer vision dimensions if available
        dimensions = vision_features.dimensions or text_features.dimensions

        # Combine part numbers
        part_numbers = list(set(
            text_features.detected_part_numbers +
            vision_features.detected_part_numbers
        ))

        return ExtractedFeatures(
            specifications=all_specs,
            dimensions=dimensions,
            text_description=text_features.text_description or vision_features.text_description,
            detected_part_numbers=part_numbers,
            visual_features=vision_features.visual_features,
            raw_ocr_text=text_features.raw_ocr_text,
            extraction_metadata={
                "merged_from": ["text", "vision"],
                **text_features.extraction_metadata,
                **vision_features.extraction_metadata
            }
        )
