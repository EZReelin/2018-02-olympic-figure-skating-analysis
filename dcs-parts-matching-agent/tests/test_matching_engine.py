"""
Unit tests for the matching engine.

Tests core matching logic, scoring algorithms, and specification matching.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import (
    ExtractedFeatures, DCSPart, Specification, SpecificationType,
    DimensionalData
)
from src.agents.matching_engine import MatchingEngine
from src.database.vector_store import VectorStore


@pytest.fixture
async def vector_store():
    """Create a test vector store."""
    store = VectorStore()
    await store.initialize()
    yield store
    # Cleanup
    await store.clear_catalog()


@pytest.fixture
def matching_engine(vector_store):
    """Create a matching engine with test vector store."""
    return MatchingEngine(vector_store)


@pytest.fixture
def sample_part():
    """Create a sample DCS part for testing."""
    return DCSPart(
        part_number="DCS-1234-ABC",
        description="24V DC Digital Input Module, 16 channels",
        category="Digital Input",
        subcategory="DI Module",
        specifications=[
            Specification(
                spec_type=SpecificationType.VOLTAGE_RATING,
                name="Voltage Rating",
                value="24",
                unit="V",
                is_critical=True
            ),
            Specification(
                spec_type=SpecificationType.IO_COUNT,
                name="Input Channels",
                value="16",
                unit=None,
                is_critical=True
            ),
            Specification(
                spec_type=SpecificationType.TEMPERATURE_RANGE,
                name="Operating Temperature",
                value="-20 to 60",
                unit="°C",
                is_critical=True
            )
        ],
        dimensions=DimensionalData(
            width=100.0,
            height=150.0,
            depth=50.0,
            unit="mm"
        )
    )


@pytest.fixture
def sample_features():
    """Create sample extracted features for testing."""
    return ExtractedFeatures(
        specifications=[
            Specification(
                spec_type=SpecificationType.VOLTAGE_RATING,
                name="Voltage Rating",
                value="24",
                unit="V",
                is_critical=True,
                confidence=0.9
            ),
            Specification(
                spec_type=SpecificationType.IO_COUNT,
                name="Input Channels",
                value="16",
                unit=None,
                is_critical=True,
                confidence=0.85
            )
        ],
        dimensions=DimensionalData(
            width=100.0,
            height=150.0,
            depth=50.0,
            unit="mm"
        ),
        text_description="Need a 24V digital input module with 16 channels"
    )


class TestMatchingEngine:
    """Test cases for MatchingEngine."""

    @pytest.mark.asyncio
    async def test_exact_specification_match(self, matching_engine):
        """Test exact specification matching."""
        customer_spec = Specification(
            spec_type=SpecificationType.VOLTAGE_RATING,
            name="Voltage",
            value="24",
            unit="V",
            is_critical=True
        )

        part_spec = Specification(
            spec_type=SpecificationType.VOLTAGE_RATING,
            name="Voltage",
            value="24",
            unit="V",
            is_critical=True
        )

        is_match, score, note = matching_engine._compare_spec_values(
            customer_spec, part_spec
        )

        assert is_match is True
        assert score == 1.0
        assert "exact" in note.lower()

    @pytest.mark.asyncio
    async def test_tolerance_specification_match(self, matching_engine):
        """Test specification matching within tolerance."""
        customer_spec = Specification(
            spec_type=SpecificationType.DIMENSION,
            name="Width",
            value="100",
            unit="mm",
            is_critical=False
        )

        part_spec = Specification(
            spec_type=SpecificationType.DIMENSION,
            name="Width",
            value="102",  # 2% difference
            unit="mm",
            is_critical=False
        )

        is_match, score, note = matching_engine._compare_spec_values(
            customer_spec, part_spec
        )

        assert is_match is True
        assert score >= 0.9

    @pytest.mark.asyncio
    async def test_specification_mismatch(self, matching_engine):
        """Test specification mismatch detection."""
        customer_spec = Specification(
            spec_type=SpecificationType.VOLTAGE_RATING,
            name="Voltage",
            value="24",
            unit="V",
            is_critical=True
        )

        part_spec = Specification(
            spec_type=SpecificationType.VOLTAGE_RATING,
            name="Voltage",
            value="12",
            unit="V",
            is_critical=True
        )

        is_match, score, note = matching_engine._compare_spec_values(
            customer_spec, part_spec
        )

        assert is_match is False
        assert score < 0.9

    @pytest.mark.asyncio
    async def test_dimensional_matching(self, matching_engine):
        """Test dimensional matching algorithm."""
        customer_dims = DimensionalData(
            width=100.0,
            height=150.0,
            depth=50.0,
            unit="mm"
        )

        part_dims = DimensionalData(
            width=102.0,  # 2% difference
            height=151.0,  # 0.67% difference
            depth=50.0,   # Exact match
            unit="mm"
        )

        score = matching_engine._match_dimensions(customer_dims, part_dims)

        # All dimensions within 5% tolerance
        assert score >= 0.9

    @pytest.mark.asyncio
    async def test_weighted_score_calculation(self, matching_engine):
        """Test weighted score calculation."""
        scores = {
            "semantic_similarity": 0.8,
            "specification_match": 0.9,
            "dimensional_match": 0.85,
            "visual_similarity": 0.7
        }

        final_score = matching_engine._calculate_weighted_score(scores)

        assert 0 <= final_score <= 100
        # With high individual scores, final should be high
        assert final_score >= 70

    @pytest.mark.asyncio
    async def test_confidence_level_assignment(self, matching_engine):
        """Test confidence level categorization."""
        from src.core.models import ConfidenceLevel

        assert matching_engine._get_confidence_level(95.0) == ConfidenceLevel.HIGH
        assert matching_engine._get_confidence_level(75.0) == ConfidenceLevel.MEDIUM
        assert matching_engine._get_confidence_level(55.0) == ConfidenceLevel.LOW
        assert matching_engine._get_confidence_level(40.0) == ConfidenceLevel.VERY_LOW

    @pytest.mark.asyncio
    async def test_find_matches_with_populated_catalog(
        self, matching_engine, vector_store, sample_part, sample_features
    ):
        """Test finding matches with populated catalog."""
        # Add sample part to catalog
        await vector_store.add_part(sample_part)

        # Find matches
        matches = await matching_engine.find_matches(
            sample_features,
            max_alternatives=3,
            min_confidence=50.0
        )

        # Should find at least one match
        assert len(matches) > 0
        assert matches[0].part.part_number == sample_part.part_number

        # Confidence should be high for good match
        assert matches[0].confidence_score >= 70.0

    @pytest.mark.asyncio
    async def test_missing_specifications_detection(self, matching_engine):
        """Test detection of missing critical specifications."""
        customer_specs = [
            Specification(
                spec_type=SpecificationType.VOLTAGE_RATING,
                name="Voltage",
                value="24",
                unit="V",
                is_critical=True
            ),
            Specification(
                spec_type=SpecificationType.CURRENT_RATING,
                name="Current",
                value="2",
                unit="A",
                is_critical=True
            )
        ]

        part_specs = [
            Specification(
                spec_type=SpecificationType.VOLTAGE_RATING,
                name="Voltage",
                value="24",
                unit="V",
                is_critical=True
            )
            # Missing current rating
        ]

        score, matches, missing, warnings = matching_engine._match_specifications(
            customer_specs, part_specs
        )

        assert "Current" in missing
        assert len(warnings) > 0
        assert any("missing" in w.lower() for w in warnings)

    @pytest.mark.asyncio
    async def test_exact_part_number_match(
        self, matching_engine, vector_store, sample_part
    ):
        """Test exact part number matching."""
        # Add part to catalog
        await vector_store.add_part(sample_part)

        # Create features with detected part number
        features = ExtractedFeatures(
            detected_part_numbers=[sample_part.part_number],
            text_description="Need DCS-1234-ABC"
        )

        matches = await matching_engine._check_exact_part_numbers(features)

        assert len(matches) == 1
        assert matches[0].confidence_score == 100.0
        assert matches[0].part.part_number == sample_part.part_number


class TestSpecificationMatching:
    """Test specification matching logic."""

    def test_normalize_specification_value(self):
        """Test specification value normalization."""
        from src.utils.helpers import normalize_specification_value

        assert normalize_specification_value("24V", "voltage") == "24v"
        assert normalize_specification_value("  ~100  ", "dimension") == "100"
        assert normalize_specification_value("Approx. 50mm", "dimension") == "50mm"

    def test_dimensional_similarity_calculation(self):
        """Test dimensional similarity calculation."""
        from src.utils.helpers import calculate_dimensional_similarity

        dim1 = {"width": 100.0, "height": 150.0}
        dim2 = {"width": 102.0, "height": 151.0}

        similarity = calculate_dimensional_similarity(dim1, dim2, tolerance_percent=5.0)

        assert similarity >= 0.9  # Both within tolerance

        # Test with mismatch
        dim3 = {"width": 120.0, "height": 150.0}
        similarity2 = calculate_dimensional_similarity(dim1, dim3, tolerance_percent=5.0)

        assert similarity2 < similarity  # Width exceeds tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
