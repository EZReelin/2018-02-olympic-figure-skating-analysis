"""
Catalog management system for DCS parts.

Handles indexing, updating, and managing the DCS parts catalog
from Smart Click PDF and other sources.
"""

import json
import csv
from pathlib import Path
from typing import List, Optional, Dict, Any
import re

from ..core.models import DCSPart, Specification, SpecificationType, DimensionalData
from ..database.vector_store import VectorStore
from ..core.config import get_settings
from ..utils.logger import get_logger
from ..processors.pdf_processor import PDFProcessor

logger = get_logger(__name__)


class CatalogManager:
    """
    Manages DCS parts catalog indexing and updates.

    Supports multiple catalog formats:
    - Smart Click PDF catalogs
    - CSV/Excel part lists
    - JSON structured data
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize catalog manager.

        Args:
            vector_store: Vector database instance
        """
        self.vector_store = vector_store
        self.settings = get_settings()
        self.pdf_processor = PDFProcessor()

    async def index_catalog_directory(
        self,
        catalog_dir: Optional[Path] = None,
        force_reindex: bool = False
    ) -> Dict[str, int]:
        """
        Index all catalog files in a directory.

        Args:
            catalog_dir: Directory containing catalog files (uses config default if None)
            force_reindex: Whether to force reindexing of existing entries

        Returns:
            Dictionary with indexing statistics
        """
        catalog_dir = catalog_dir or self.settings.catalog_path

        logger.info(f"Starting catalog indexing from {catalog_dir}")

        if not catalog_dir.exists():
            logger.warning(f"Catalog directory not found: {catalog_dir}")
            catalog_dir.mkdir(parents=True, exist_ok=True)
            return {"error": "Catalog directory was empty"}

        stats = {
            "pdf_files": 0,
            "json_files": 0,
            "csv_files": 0,
            "parts_indexed": 0,
            "errors": 0
        }

        # Process PDF catalogs
        for pdf_file in catalog_dir.glob("**/*.pdf"):
            try:
                logger.info(f"Processing PDF catalog: {pdf_file.name}")
                parts = await self._parse_pdf_catalog(pdf_file)
                await self.vector_store.add_parts_batch(parts)
                stats["pdf_files"] += 1
                stats["parts_indexed"] += len(parts)
            except Exception as e:
                logger.error(f"Failed to process {pdf_file.name}: {e}")
                stats["errors"] += 1

        # Process JSON catalogs
        for json_file in catalog_dir.glob("**/*.json"):
            try:
                logger.info(f"Processing JSON catalog: {json_file.name}")
                parts = await self._parse_json_catalog(json_file)
                await self.vector_store.add_parts_batch(parts)
                stats["json_files"] += 1
                stats["parts_indexed"] += len(parts)
            except Exception as e:
                logger.error(f"Failed to process {json_file.name}: {e}")
                stats["errors"] += 1

        # Process CSV catalogs
        for csv_file in catalog_dir.glob("**/*.csv"):
            try:
                logger.info(f"Processing CSV catalog: {csv_file.name}")
                parts = await self._parse_csv_catalog(csv_file)
                await self.vector_store.add_parts_batch(parts)
                stats["csv_files"] += 1
                stats["parts_indexed"] += len(parts)
            except Exception as e:
                logger.error(f"Failed to process {csv_file.name}: {e}")
                stats["errors"] += 1

        logger.info(f"Catalog indexing complete: {stats}")
        return stats

    async def _parse_pdf_catalog(self, pdf_path: Path) -> List[DCSPart]:
        """
        Parse parts from Smart Click PDF catalog.

        Args:
            pdf_path: Path to PDF catalog

        Returns:
            List of DCSPart objects
        """
        # Extract text from PDF
        features = await self.pdf_processor.process(pdf_path)
        text = features.raw_ocr_text

        # Parse parts from structured text
        # This is a simplified parser - production would need more sophisticated parsing
        parts = []

        # Look for part number patterns and associated specifications
        # Format: PART-NUMBER followed by specifications
        part_blocks = self._split_into_part_blocks(text)

        for block in part_blocks:
            try:
                part = self._parse_part_block(block)
                if part:
                    parts.append(part)
            except Exception as e:
                logger.warning(f"Failed to parse part block: {e}")

        logger.info(f"Parsed {len(parts)} parts from PDF catalog")
        return parts

    def _split_into_part_blocks(self, text: str) -> List[str]:
        """
        Split catalog text into individual part blocks.

        Args:
            text: Full catalog text

        Returns:
            List of text blocks, one per part
        """
        # Split on part number patterns
        part_pattern = r'\n([A-Z]{2,4}[-\s]?\d{4,8}[-\s]?[A-Z0-9]{0,6})\s'
        blocks = re.split(part_pattern, text)

        # Combine part numbers with their descriptions
        part_blocks = []
        for i in range(1, len(blocks), 2):
            if i + 1 < len(blocks):
                part_number = blocks[i].strip()
                description = blocks[i + 1].strip()
                part_blocks.append(f"{part_number}\n{description}")

        return part_blocks

    def _parse_part_block(self, block: str) -> Optional[DCSPart]:
        """
        Parse a single part block into DCSPart.

        Args:
            block: Text block for one part

        Returns:
            DCSPart object or None
        """
        lines = block.split('\n')
        if not lines:
            return None

        part_number = lines[0].strip()
        description = lines[1] if len(lines) > 1 else ""

        # Extract specifications from remaining lines
        specifications = []
        full_text = '\n'.join(lines[1:])

        # Extract voltage
        voltage_match = re.search(r'(\d+\.?\d*)\s*V(?:DC|AC)?', full_text, re.IGNORECASE)
        if voltage_match:
            specifications.append(Specification(
                spec_type=SpecificationType.VOLTAGE_RATING,
                name="Voltage Rating",
                value=voltage_match.group(1),
                unit="V",
                is_critical=True
            ))

        # Extract current
        current_match = re.search(r'(\d+\.?\d*)\s*[Aa]mp|(\d+\.?\d*)\s*mA', full_text, re.IGNORECASE)
        if current_match:
            value = current_match.group(1) or current_match.group(2)
            specifications.append(Specification(
                spec_type=SpecificationType.CURRENT_RATING,
                name="Current Rating",
                value=value,
                unit="A" if current_match.group(1) else "mA",
                is_critical=True
            ))

        # Extract temperature range
        temp_match = re.search(r'(-?\d+)°?[CF]\s*to\s*(-?\d+)°?[CF]', full_text, re.IGNORECASE)
        if temp_match:
            specifications.append(Specification(
                spec_type=SpecificationType.TEMPERATURE_RANGE,
                name="Operating Temperature",
                value=f"{temp_match.group(1)} to {temp_match.group(2)}",
                unit="°C",
                is_critical=True
            ))

        # Extract I/O count
        io_match = re.search(r'(\d+)\s*(?:DI|DO|AI|AO|I/O)', full_text, re.IGNORECASE)
        if io_match:
            specifications.append(Specification(
                spec_type=SpecificationType.IO_COUNT,
                name="I/O Count",
                value=io_match.group(1),
                is_critical=False
            ))

        return DCSPart(
            part_number=part_number,
            description=description,
            specifications=specifications,
            category="DCS Component",
            metadata={"source": "pdf_catalog"}
        )

    async def _parse_json_catalog(self, json_path: Path) -> List[DCSPart]:
        """
        Parse parts from JSON catalog.

        Expected format:
        {
            "parts": [
                {
                    "part_number": "...",
                    "description": "...",
                    "specifications": [...],
                    ...
                }
            ]
        }

        Args:
            json_path: Path to JSON file

        Returns:
            List of DCSPart objects
        """
        with open(json_path, 'r') as f:
            data = json.load(f)

        parts = []

        # Support both {"parts": [...]} and direct array format
        parts_data = data.get('parts', data) if isinstance(data, dict) else data

        for part_data in parts_data:
            try:
                # Parse specifications
                specifications = []
                for spec_data in part_data.get('specifications', []):
                    spec = Specification(
                        spec_type=SpecificationType(spec_data.get('spec_type', 'other')),
                        name=spec_data['name'],
                        value=str(spec_data['value']),
                        unit=spec_data.get('unit'),
                        is_critical=spec_data.get('is_critical', False)
                    )
                    specifications.append(spec)

                # Parse dimensions if present
                dimensions = None
                if 'dimensions' in part_data:
                    dim_data = part_data['dimensions']
                    dimensions = DimensionalData(
                        width=dim_data.get('width'),
                        height=dim_data.get('height'),
                        depth=dim_data.get('depth'),
                        diameter=dim_data.get('diameter'),
                        unit=dim_data.get('unit', 'mm')
                    )

                part = DCSPart(
                    part_number=part_data['part_number'],
                    description=part_data.get('description', ''),
                    category=part_data.get('category'),
                    subcategory=part_data.get('subcategory'),
                    specifications=specifications,
                    dimensions=dimensions,
                    compatibility_info=part_data.get('compatibility_info', []),
                    technical_notes=part_data.get('technical_notes'),
                    metadata=part_data.get('metadata', {})
                )
                parts.append(part)

            except Exception as e:
                logger.warning(f"Failed to parse part from JSON: {e}")

        logger.info(f"Parsed {len(parts)} parts from JSON catalog")
        return parts

    async def _parse_csv_catalog(self, csv_path: Path) -> List[DCSPart]:
        """
        Parse parts from CSV catalog.

        Expected columns: part_number, description, category, specifications, ...

        Args:
            csv_path: Path to CSV file

        Returns:
            List of DCSPart objects
        """
        parts = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Parse specifications from comma-separated string or JSON
                    specifications = []
                    spec_str = row.get('specifications', '')

                    if spec_str:
                        # Try JSON first
                        try:
                            spec_list = json.loads(spec_str)
                            for spec_data in spec_list:
                                spec = Specification(
                                    spec_type=SpecificationType(spec_data.get('type', 'other')),
                                    name=spec_data['name'],
                                    value=str(spec_data['value']),
                                    unit=spec_data.get('unit'),
                                    is_critical=spec_data.get('critical', False)
                                )
                                specifications.append(spec)
                        except json.JSONDecodeError:
                            # Parse simple format: "voltage:24V, current:2A"
                            spec_pairs = spec_str.split(',')
                            for pair in spec_pairs:
                                if ':' in pair:
                                    name, value = pair.split(':', 1)
                                    specifications.append(Specification(
                                        spec_type=SpecificationType.OTHER,
                                        name=name.strip(),
                                        value=value.strip(),
                                        is_critical=False
                                    ))

                    part = DCSPart(
                        part_number=row['part_number'],
                        description=row.get('description', ''),
                        category=row.get('category'),
                        subcategory=row.get('subcategory'),
                        specifications=specifications,
                        metadata={"source": "csv_catalog"}
                    )
                    parts.append(part)

                except Exception as e:
                    logger.warning(f"Failed to parse CSV row: {e}")

        logger.info(f"Parsed {len(parts)} parts from CSV catalog")
        return parts

    async def add_single_part(self, part: DCSPart) -> str:
        """
        Add a single part to the catalog.

        Args:
            part: DCSPart to add

        Returns:
            Entry ID
        """
        logger.info(f"Adding part {part.part_number} to catalog")
        return await self.vector_store.add_part(part)

    async def update_part(self, part_number: str, updated_part: DCSPart) -> bool:
        """
        Update an existing part in the catalog.

        Args:
            part_number: Part number to update
            updated_part: Updated DCSPart data

        Returns:
            True if successful
        """
        # Delete old entry and add new one
        # (ChromaDB doesn't have native update, so we delete and re-add)
        try:
            entry_id = f"part_{part_number}"
            await self.vector_store.add_part(updated_part, entry_id)
            logger.info(f"Updated part {part_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to update part {part_number}: {e}")
            return False

    async def get_catalog_stats(self) -> Dict[str, Any]:
        """
        Get catalog statistics.

        Returns:
            Dictionary with statistics
        """
        return self.vector_store.get_stats()
