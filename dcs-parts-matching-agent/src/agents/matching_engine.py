"""
Intelligent matching engine for DCS parts.

Matches customer requirements against catalog using multi-factor scoring:
- Exact specification matching
- Dimensional similarity
- Semantic similarity
- Visual feature matching
"""

from typing import List, Dict, Any, Optional, Tuple
import math

from ..core.models import (
    ExtractedFeatures, DCSPart, PartMatch, SpecificationMatch,
    MatchingResult, Specification, ConfidenceLevel
)
from ..core.config import get_settings
from ..database.vector_store import VectorStore
from ..utils.logger import get_logger
from ..utils.helpers import calculate_dimensional_similarity, normalize_specification_value

logger = get_logger(__name__)


class MatchingEngine:
    """
    Intelligent matching engine for DCS parts.

    Uses weighted multi-factor scoring to match customer requirements
    against the catalog.
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize matching engine.

        Args:
            vector_store: Vector database instance
        """
        self.vector_store = vector_store
        self.settings = get_settings()
        self.weights = self.settings.confidence_weights

    async def find_matches(
        self,
        features: ExtractedFeatures,
        max_alternatives: int = 3,
        min_confidence: float = 50.0
    ) -> List[PartMatch]:
        """
        Find matching parts for extracted features.

        Args:
            features: ExtractedFeatures from customer submission
            max_alternatives: Maximum number of alternatives to return
            min_confidence: Minimum confidence score threshold

        Returns:
            List of PartMatch objects sorted by confidence
        """
        logger.info("Starting intelligent part matching")

        # Step 1: Check for exact part number matches
        exact_matches = await self._check_exact_part_numbers(features)
        if exact_matches:
            logger.info(f"Found {len(exact_matches)} exact part number matches")
            return exact_matches[:max_alternatives + 1]

        # Step 2: Semantic search using vector similarity
        candidates = await self.vector_store.search_similar_parts(
            features,
            top_k=20  # Get more candidates for detailed scoring
        )

        if not candidates:
            logger.warning("No candidate parts found in vector search")
            return []

        # Step 3: Score each candidate with detailed matching
        scored_matches = []
        for candidate in candidates:
            part = await self._reconstruct_part_from_candidate(candidate)
            if part:
                match = await self._score_match(features, part, candidate)
                if match.confidence_score >= min_confidence:
                    scored_matches.append(match)

        # Step 4: Sort by confidence and return top matches
        scored_matches.sort(key=lambda x: x.confidence_score, reverse=True)

        logger.info(
            f"Found {len(scored_matches)} matches above threshold "
            f"(min confidence: {min_confidence})"
        )

        return scored_matches[:max_alternatives + 1]

    async def _check_exact_part_numbers(
        self,
        features: ExtractedFeatures
    ) -> List[PartMatch]:
        """
        Check for exact part number matches.

        Args:
            features: Extracted features

        Returns:
            List of exact matches with high confidence
        """
        exact_matches = []

        for part_number in features.detected_part_numbers:
            result = await self.vector_store.get_part_by_number(part_number)
            if result:
                part = await self._reconstruct_part_from_candidate(result)
                if part:
                    match = PartMatch(
                        part=part,
                        confidence_score=100.0,
                        confidence_level=ConfidenceLevel.HIGH,
                        matched_specifications=[],
                        justification=f"Exact part number match: {part_number}",
                        warnings=[]
                    )
                    exact_matches.append(match)

        return exact_matches

    async def _score_match(
        self,
        features: ExtractedFeatures,
        part: DCSPart,
        candidate: Dict[str, Any]
    ) -> PartMatch:
        """
        Calculate detailed match score for a candidate part.

        Args:
            features: Customer requirements
            part: Candidate DCS part
            candidate: Raw candidate data from vector search

        Returns:
            PartMatch with detailed scoring
        """
        scores = {}
        matched_specs = []
        missing_specs = []
        warnings = []

        # 1. Semantic similarity score (from vector search)
        if candidate.get('distance') is not None:
            # Convert distance to similarity (assuming cosine distance)
            semantic_score = max(0, 1 - candidate['distance'])
            scores['semantic_similarity'] = semantic_score
        else:
            scores['semantic_similarity'] = 0.5

        # 2. Specification matching score
        spec_score, spec_matches, spec_missing, spec_warnings = self._match_specifications(
            features.specifications,
            part.specifications
        )
        scores['specification_match'] = spec_score
        matched_specs = spec_matches
        missing_specs = spec_missing
        warnings.extend(spec_warnings)

        # 3. Dimensional similarity score
        if features.dimensions and part.dimensions:
            dim_score = self._match_dimensions(features.dimensions, part.dimensions)
            scores['dimensional_match'] = dim_score
        else:
            scores['dimensional_match'] = 0.5  # Neutral if no dimensions

        # 4. Visual feature matching (if available)
        if features.visual_features and part.metadata.get('visual_features'):
            visual_score = self._match_visual_features(
                features.visual_features,
                part.metadata['visual_features']
            )
            scores['visual_similarity'] = visual_score
        else:
            scores['visual_similarity'] = 0.5

        # Calculate weighted final score
        final_score = self._calculate_weighted_score(scores)

        # Build justification
        justification = self._build_justification(scores, matched_specs, part)

        return PartMatch(
            part=part,
            confidence_score=final_score,
            confidence_level=self._get_confidence_level(final_score),
            matched_specifications=matched_specs,
            missing_specifications=missing_specs,
            justification=justification,
            warnings=warnings
        )

    def _match_specifications(
        self,
        customer_specs: List[Specification],
        part_specs: List[Specification]
    ) -> Tuple[float, List[SpecificationMatch], List[str], List[str]]:
        """
        Match specifications between customer requirements and part.

        Args:
            customer_specs: Customer's required specifications
            part_specs: Part's specifications

        Returns:
            Tuple of (score, matches, missing_specs, warnings)
        """
        if not customer_specs:
            return 0.5, [], [], []

        matches = []
        missing = []
        warnings = []
        total_weight = 0
        matched_weight = 0

        # Create lookup dict for part specs
        part_spec_dict = {
            (spec.spec_type, spec.name.lower()): spec
            for spec in part_specs
        }

        for customer_spec in customer_specs:
            weight = self.settings.critical_specs_weight if customer_spec.is_critical else 1.0
            total_weight += weight

            # Try to find matching spec
            key = (customer_spec.spec_type, customer_spec.name.lower())
            part_spec = part_spec_dict.get(key)

            if part_spec:
                # Compare values
                is_match, match_score, note = self._compare_spec_values(
                    customer_spec,
                    part_spec
                )

                matches.append(SpecificationMatch(
                    spec_name=customer_spec.name,
                    customer_value=f"{customer_spec.value} {customer_spec.unit or ''}".strip(),
                    part_value=f"{part_spec.value} {part_spec.unit or ''}".strip(),
                    is_match=is_match,
                    match_score=match_score,
                    notes=note
                ))

                if is_match:
                    matched_weight += weight * match_score
                else:
                    warnings.append(
                        f"Specification mismatch: {customer_spec.name} "
                        f"(required: {customer_spec.value}, part: {part_spec.value})"
                    )
            else:
                # Spec not found in part
                missing.append(customer_spec.name)
                matches.append(SpecificationMatch(
                    spec_name=customer_spec.name,
                    customer_value=f"{customer_spec.value} {customer_spec.unit or ''}".strip(),
                    part_value="Not specified",
                    is_match=False,
                    match_score=0.0,
                    notes="Specification not found in part datasheet"
                ))

                if customer_spec.is_critical:
                    warnings.append(
                        f"Critical specification missing: {customer_spec.name}"
                    )

        score = matched_weight / total_weight if total_weight > 0 else 0.0
        return score, matches, missing, warnings

    def _compare_spec_values(
        self,
        customer_spec: Specification,
        part_spec: Specification
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Compare two specification values.

        Args:
            customer_spec: Customer specification
            part_spec: Part specification

        Returns:
            Tuple of (is_match, match_score, notes)
        """
        customer_val = normalize_specification_value(
            customer_spec.value,
            customer_spec.spec_type
        )
        part_val = normalize_specification_value(
            part_spec.value,
            part_spec.spec_type
        )

        # Exact string match
        if customer_val == part_val:
            return True, 1.0, "Exact match"

        # Try numeric comparison for numeric specs
        try:
            customer_num = float(customer_val.split()[0])
            part_num = float(part_val.split()[0])

            # Check if within tolerance
            tolerance = self.settings.dimensional_tolerance_percent / 100
            diff_percent = abs(customer_num - part_num) / max(customer_num, part_num)

            if diff_percent <= tolerance:
                return True, 1.0 - diff_percent, f"Within tolerance ({diff_percent*100:.1f}%)"
            elif diff_percent <= tolerance * 2:
                return False, 0.7, f"Close but outside tolerance ({diff_percent*100:.1f}%)"
            else:
                return False, 0.3, f"Significant difference ({diff_percent*100:.1f}%)"

        except (ValueError, IndexError):
            # Not numeric, do fuzzy string matching
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, customer_val, part_val).ratio()

            if similarity > 0.8:
                return True, similarity, "High similarity"
            elif similarity > 0.6:
                return False, similarity, "Partial match"
            else:
                return False, similarity, "Low similarity"

    def _match_dimensions(self, customer_dims, part_dims) -> float:
        """
        Calculate dimensional matching score.

        Args:
            customer_dims: Customer dimensional requirements
            part_dims: Part dimensions

        Returns:
            Match score 0.0-1.0
        """
        customer_dict = {
            'width': customer_dims.width,
            'height': customer_dims.height,
            'depth': customer_dims.depth,
            'diameter': customer_dims.diameter
        }

        part_dict = {
            'width': part_dims.width,
            'height': part_dims.height,
            'depth': part_dims.depth,
            'diameter': part_dims.diameter
        }

        # Filter out None values
        customer_dict = {k: v for k, v in customer_dict.items() if v is not None}
        part_dict = {k: v for k, v in part_dict.items() if v is not None}

        return calculate_dimensional_similarity(
            customer_dict,
            part_dict,
            self.settings.dimensional_tolerance_percent
        )

    def _match_visual_features(
        self,
        customer_features: Dict[str, Any],
        part_features: Dict[str, Any]
    ) -> float:
        """
        Match visual features.

        Args:
            customer_features: Customer visual features
            part_features: Part visual features

        Returns:
            Match score 0.0-1.0
        """
        # Simple key-based matching
        common_keys = set(customer_features.keys()) & set(part_features.keys())
        if not common_keys:
            return 0.5

        matches = 0
        for key in common_keys:
            if customer_features[key] == part_features[key]:
                matches += 1

        return matches / len(common_keys)

    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted final confidence score.

        Args:
            scores: Dictionary of individual scores

        Returns:
            Final confidence score 0-100
        """
        total_weight = 0
        weighted_sum = 0

        for score_name, score_value in scores.items():
            weight = self.weights.get(score_name, 0.5)
            total_weight += weight
            weighted_sum += score_value * weight

        final_score = (weighted_sum / total_weight) * 100 if total_weight > 0 else 0
        return min(100.0, max(0.0, final_score))

    def _build_justification(
        self,
        scores: Dict[str, float],
        matched_specs: List[SpecificationMatch],
        part: DCSPart
    ) -> str:
        """
        Build human-readable justification for match.

        Args:
            scores: Individual scores
            matched_specs: Matched specifications
            part: Matched part

        Returns:
            Justification string
        """
        justification_parts = [
            f"Matched {part.part_number} - {part.description}"
        ]

        # Summarize matched specs
        exact_matches = sum(1 for spec in matched_specs if spec.is_match and spec.match_score >= 0.9)
        partial_matches = sum(1 for spec in matched_specs if spec.is_match and spec.match_score < 0.9)

        if exact_matches > 0:
            justification_parts.append(
                f"{exact_matches} exact specification match(es)"
            )

        if partial_matches > 0:
            justification_parts.append(
                f"{partial_matches} partial specification match(es)"
            )

        # Add score breakdown
        score_desc = []
        for name, score in scores.items():
            if score >= 0.8:
                score_desc.append(f"high {name.replace('_', ' ')}")
            elif score >= 0.6:
                score_desc.append(f"moderate {name.replace('_', ' ')}")

        if score_desc:
            justification_parts.append(f"Strong match based on {', '.join(score_desc)}")

        return ". ".join(justification_parts) + "."

    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """
        Convert numeric score to confidence level.

        Args:
            score: Confidence score 0-100

        Returns:
            ConfidenceLevel enum
        """
        if score >= 90:
            return ConfidenceLevel.HIGH
        elif score >= 70:
            return ConfidenceLevel.MEDIUM
        elif score >= 50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    async def _reconstruct_part_from_candidate(
        self,
        candidate: Dict[str, Any]
    ) -> Optional[DCSPart]:
        """
        Reconstruct DCSPart from search candidate.

        Args:
            candidate: Candidate from vector search

        Returns:
            DCSPart object or None
        """
        try:
            metadata = candidate.get('metadata', {})

            # Parse specifications from metadata
            specifications = []
            for key, value in metadata.items():
                if key.startswith('spec_'):
                    spec_type = key.replace('spec_', '')
                    # Parse value and unit
                    parts = str(value).split()
                    spec_value = parts[0] if parts else value
                    spec_unit = parts[1] if len(parts) > 1 else None

                    specifications.append(Specification(
                        spec_type=spec_type,
                        name=spec_type.replace('_', ' ').title(),
                        value=spec_value,
                        unit=spec_unit,
                        is_critical=True
                    ))

            return DCSPart(
                part_number=metadata.get('part_number', ''),
                description=metadata.get('description', ''),
                category=metadata.get('category'),
                subcategory=metadata.get('subcategory'),
                specifications=specifications,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to reconstruct part from candidate: {e}")
            return None
