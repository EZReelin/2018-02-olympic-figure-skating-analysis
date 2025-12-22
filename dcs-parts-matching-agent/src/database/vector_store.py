"""
Vector database integration for similarity search.

Provides abstraction over ChromaDB for storing and searching part embeddings.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from ..core.models import DCSPart, CatalogEntry, ExtractedFeatures
from ..core.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Vector database for DCS parts catalog and drawings."""

    def __init__(self):
        """Initialize vector store."""
        self.settings = get_settings()
        self.client = None
        self.catalog_collection = None
        self.drawings_collection = None
        self.embedding_function = None

    async def initialize(self):
        """Initialize ChromaDB client and collections."""
        logger.info("Initializing vector database")

        # Create persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.settings.vector_db_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Set up embedding function
        self.embedding_function = self._get_embedding_function()

        # Create or get collections
        self.catalog_collection = self.client.get_or_create_collection(
            name=self.settings.collection_name_catalog,
            embedding_function=self.embedding_function,
            metadata={"description": "DCS parts catalog"}
        )

        self.drawings_collection = self.client.get_or_create_collection(
            name=self.settings.collection_name_drawings,
            embedding_function=self.embedding_function,
            metadata={"description": "Technical drawings repository"}
        )

        logger.info(
            f"Vector database initialized - "
            f"Catalog entries: {self.catalog_collection.count()}, "
            f"Drawings: {self.drawings_collection.count()}"
        )

    def _get_embedding_function(self):
        """
        Get embedding function based on configuration.

        Returns:
            Embedding function for ChromaDB
        """
        if self.settings.openai_api_key:
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.settings.openai_api_key,
                model_name=self.settings.use_embedding_model
            )
        else:
            # Fallback to default sentence transformers
            return embedding_functions.DefaultEmbeddingFunction()

    async def add_part(self, part: DCSPart, entry_id: Optional[str] = None) -> str:
        """
        Add a DCS part to the catalog collection.

        Args:
            part: DCSPart to add
            entry_id: Optional custom ID, will generate if not provided

        Returns:
            Entry ID
        """
        if entry_id is None:
            entry_id = f"part_{part.part_number}"

        # Create searchable document from part
        document = self._part_to_document(part)

        # Create metadata
        metadata = {
            "part_number": part.part_number,
            "category": part.category or "",
            "subcategory": part.subcategory or "",
            "description": part.description[:500] if part.description else "",
        }

        # Add critical specifications to metadata
        for spec in part.specifications:
            if spec.is_critical:
                metadata[f"spec_{spec.spec_type}"] = f"{spec.value} {spec.unit or ''}".strip()

        try:
            self.catalog_collection.add(
                documents=[document],
                metadatas=[metadata],
                ids=[entry_id]
            )
            logger.info(f"Added part {part.part_number} to catalog")
            return entry_id
        except Exception as e:
            logger.error(f"Failed to add part {part.part_number}: {e}")
            raise

    async def add_parts_batch(self, parts: List[DCSPart]) -> List[str]:
        """
        Add multiple parts in batch.

        Args:
            parts: List of DCSPart objects

        Returns:
            List of entry IDs
        """
        entry_ids = []
        documents = []
        metadatas = []

        for part in parts:
            entry_id = f"part_{part.part_number}"
            entry_ids.append(entry_id)

            documents.append(self._part_to_document(part))

            metadata = {
                "part_number": part.part_number,
                "category": part.category or "",
                "subcategory": part.subcategory or "",
                "description": part.description[:500] if part.description else "",
            }

            for spec in part.specifications:
                if spec.is_critical:
                    metadata[f"spec_{spec.spec_type}"] = f"{spec.value} {spec.unit or ''}".strip()

            metadatas.append(metadata)

        try:
            self.catalog_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=entry_ids
            )
            logger.info(f"Added {len(parts)} parts to catalog in batch")
            return entry_ids
        except Exception as e:
            logger.error(f"Batch add failed: {e}")
            raise

    def _part_to_document(self, part: DCSPart) -> str:
        """
        Convert DCSPart to searchable document string.

        Args:
            part: DCSPart object

        Returns:
            Document string for embedding
        """
        doc_parts = [
            f"Part Number: {part.part_number}",
            f"Description: {part.description}",
        ]

        if part.category:
            doc_parts.append(f"Category: {part.category}")

        if part.subcategory:
            doc_parts.append(f"Subcategory: {part.subcategory}")

        # Add specifications
        spec_strings = []
        for spec in part.specifications:
            spec_str = f"{spec.name}: {spec.value}"
            if spec.unit:
                spec_str += f" {spec.unit}"
            spec_strings.append(spec_str)

        if spec_strings:
            doc_parts.append("Specifications: " + ", ".join(spec_strings))

        # Add dimensions
        if part.dimensions:
            dim_parts = []
            if part.dimensions.width:
                dim_parts.append(f"width {part.dimensions.width}")
            if part.dimensions.height:
                dim_parts.append(f"height {part.dimensions.height}")
            if part.dimensions.depth:
                dim_parts.append(f"depth {part.dimensions.depth}")
            if dim_parts:
                doc_parts.append(f"Dimensions: {' x '.join(dim_parts)} {part.dimensions.unit}")

        # Add compatibility info
        if part.compatibility_info:
            doc_parts.append("Compatible with: " + ", ".join(part.compatibility_info))

        # Add technical notes
        if part.technical_notes:
            doc_parts.append(f"Notes: {part.technical_notes}")

        return "\n".join(doc_parts)

    async def search_similar_parts(
        self,
        features: ExtractedFeatures,
        top_k: int = 10,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar parts based on extracted features.

        Args:
            features: ExtractedFeatures from customer submission
            top_k: Number of results to return
            where_filter: Optional metadata filter

        Returns:
            List of search results with metadata and scores
        """
        # Build query from features
        query = self._features_to_query(features)

        logger.info(f"Searching for similar parts with query: {query[:200]}...")

        try:
            results = self.catalog_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )

            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, entry_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': entry_id,
                        'part_number': results['metadatas'][0][i].get('part_number', ''),
                        'metadata': results['metadatas'][0][i],
                        'document': results['documents'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                    })

            logger.info(f"Found {len(formatted_results)} similar parts")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _features_to_query(self, features: ExtractedFeatures) -> str:
        """
        Convert ExtractedFeatures to search query string.

        Args:
            features: Extracted features

        Returns:
            Query string
        """
        query_parts = []

        # Add text description
        if features.text_description:
            query_parts.append(features.text_description)

        # Add specifications
        spec_strings = []
        for spec in features.specifications:
            spec_str = f"{spec.name}: {spec.value}"
            if spec.unit:
                spec_str += f" {spec.unit}"
            spec_strings.append(spec_str)

        if spec_strings:
            query_parts.append("Specifications: " + ", ".join(spec_strings))

        # Add dimensions
        if features.dimensions:
            dim_parts = []
            if features.dimensions.width:
                dim_parts.append(f"width {features.dimensions.width}")
            if features.dimensions.height:
                dim_parts.append(f"height {features.dimensions.height}")
            if features.dimensions.depth:
                dim_parts.append(f"depth {features.dimensions.depth}")
            if dim_parts:
                query_parts.append(f"Dimensions: {' x '.join(dim_parts)} {features.dimensions.unit}")

        # Add detected part numbers
        if features.detected_part_numbers:
            query_parts.append("Related parts: " + ", ".join(features.detected_part_numbers))

        return "\n".join(query_parts)

    async def get_part_by_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """
        Get part by exact part number.

        Args:
            part_number: Part number to search for

        Returns:
            Part data or None if not found
        """
        try:
            results = self.catalog_collection.get(
                where={"part_number": part_number}
            )

            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'metadata': results['metadatas'][0],
                    'document': results['documents'][0]
                }
            return None
        except Exception as e:
            logger.error(f"Get part by number failed: {e}")
            return None

    async def clear_catalog(self):
        """Clear all entries from catalog collection."""
        try:
            self.client.delete_collection(self.settings.collection_name_catalog)
            self.catalog_collection = self.client.create_collection(
                name=self.settings.collection_name_catalog,
                embedding_function=self.embedding_function
            )
            logger.info("Catalog collection cleared")
        except Exception as e:
            logger.error(f"Failed to clear catalog: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "catalog_count": self.catalog_collection.count() if self.catalog_collection else 0,
            "drawings_count": self.drawings_collection.count() if self.drawings_collection else 0,
        }
