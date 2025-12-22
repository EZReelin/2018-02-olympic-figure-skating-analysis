"""
Example: Using the REST API to match parts.

This example shows how to interact with the DCS Parts Matching Agent via HTTP API.
"""

import requests
import json
from pathlib import Path


class DCSPartsClient:
    """Simple client for DCS Parts Matching API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url

    def health_check(self):
        """Check if API is healthy."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def match_from_text(
        self,
        text_description: str,
        additional_context: str = None,
        max_alternatives: int = 3,
        min_confidence: float = 50.0
    ):
        """
        Match parts from text description.

        Args:
            text_description: Text description of requirements
            additional_context: Optional additional context
            max_alternatives: Maximum number of alternatives
            min_confidence: Minimum confidence threshold

        Returns:
            Matching result dictionary
        """
        data = {
            "text_description": text_description,
            "max_alternatives": max_alternatives,
            "min_confidence": min_confidence
        }

        if additional_context:
            data["additional_context"] = additional_context

        response = requests.post(
            f"{self.base_url}/api/match",
            data=data
        )

        response.raise_for_status()
        return response.json()

    def match_from_file(
        self,
        file_path: Path,
        text_description: str = None,
        max_alternatives: int = 3,
        min_confidence: float = 50.0
    ):
        """
        Match parts from uploaded file.

        Args:
            file_path: Path to file (PDF, image, etc.)
            text_description: Optional text description
            max_alternatives: Maximum number of alternatives
            min_confidence: Minimum confidence threshold

        Returns:
            Matching result dictionary
        """
        data = {
            "max_alternatives": max_alternatives,
            "min_confidence": min_confidence
        }

        if text_description:
            data["text_description"] = text_description

        with open(file_path, 'rb') as f:
            files = {"file": (file_path.name, f)}
            response = requests.post(
                f"{self.base_url}/api/match",
                files=files,
                data=data
            )

        response.raise_for_status()
        return response.json()

    def get_catalog_stats(self):
        """Get catalog statistics."""
        response = requests.get(f"{self.base_url}/api/catalog/stats")
        response.raise_for_status()
        return response.json()

    def index_catalog(self):
        """Trigger catalog reindexing."""
        response = requests.post(f"{self.base_url}/api/catalog/index")
        response.raise_for_status()
        return response.json()

    def add_part(self, part_data: dict):
        """
        Add a new part to catalog.

        Args:
            part_data: Part data dictionary

        Returns:
            Response with entry ID
        """
        response = requests.post(
            f"{self.base_url}/api/catalog/parts",
            json=part_data
        )
        response.raise_for_status()
        return response.json()


def print_match_result(result: dict):
    """Pretty print match result."""
    print("\n" + "="*70)
    print("MATCHING RESULTS")
    print("="*70)

    if result.get("primary_match"):
        match = result["primary_match"]
        part = match["part"]

        print(f"\n✓ PRIMARY MATCH")
        print(f"  Part Number: {part['part_number']}")
        print(f"  Description: {part['description']}")
        print(f"  Confidence: {match['confidence_score']:.1f}%")
        print(f"  Level: {match['confidence_level'].upper()}")
        print(f"\n  Justification:")
        print(f"  {match['justification']}")

        # Show matched specs
        if match.get("matched_specifications"):
            print(f"\n  Matched Specifications:")
            for spec in match["matched_specifications"]:
                status = "✓" if spec["is_match"] else "✗"
                print(f"    {status} {spec['spec_name']}: {spec['customer_value']} → {spec['part_value']}")

        # Show warnings
        if match.get("warnings"):
            print(f"\n  ⚠️ Warnings:")
            for warning in match["warnings"]:
                print(f"    - {warning}")

        # Show alternatives
        if result.get("alternative_matches"):
            print(f"\n  Alternatives:")
            for i, alt in enumerate(result["alternative_matches"], 1):
                print(f"    {i}. {alt['part']['part_number']} - {alt['confidence_score']:.1f}%")

    else:
        print("\n✗ No suitable match found")

    if result.get("requires_human_review"):
        print(f"\n⚠️ HUMAN REVIEW RECOMMENDED: {result['review_reason']}")

    print(f"\nProcessing time: {result['processing_time_seconds']:.2f}s")
    print("="*70)


def main():
    """Main example function."""

    # Initialize client
    client = DCSPartsClient("http://localhost:8000")

    # Check API health
    print("Checking API health...")
    try:
        health = client.health_check()
        print(f"✓ API is {health['status']}")
        print(f"  Catalog entries: {health.get('catalog_entries_count', 0)}")
    except Exception as e:
        print(f"✗ API not available: {e}")
        print("  Make sure the server is running: python -m src.api.main")
        return

    # Example 1: Match from text
    print("\n" + "-"*70)
    print("EXAMPLE 1: Text Description Matching")
    print("-"*70)

    text_desc = "24V DC digital input module with 16 channels, DIN rail mounting"

    try:
        result = client.match_from_text(
            text_description=text_desc,
            additional_context="Industrial automation project",
            max_alternatives=3,
            min_confidence=50.0
        )
        print_match_result(result)
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Match from file (if file exists)
    print("\n" + "-"*70)
    print("EXAMPLE 2: File Upload Matching")
    print("-"*70)

    test_file = Path("examples/sample_drawing.pdf")
    if test_file.exists():
        try:
            result = client.match_from_file(
                file_path=test_file,
                text_description="Looking for equivalent part",
                max_alternatives=3
            )
            print_match_result(result)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Sample file not found: {test_file}")
        print("Create a sample file to test file upload")

    # Example 3: Get catalog stats
    print("\n" + "-"*70)
    print("EXAMPLE 3: Catalog Statistics")
    print("-"*70)

    try:
        stats = client.get_catalog_stats()
        print(f"Catalog Statistics:")
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    # Example 4: Add a new part
    print("\n" + "-"*70)
    print("EXAMPLE 4: Adding New Part to Catalog")
    print("-"*70)

    new_part = {
        "part_number": "TEST-9999-XYZ",
        "description": "Test 24V DC Digital Input Module",
        "category": "Digital Input",
        "specifications": [
            {
                "spec_type": "voltage_rating",
                "name": "Voltage Rating",
                "value": "24",
                "unit": "V",
                "is_critical": True
            },
            {
                "spec_type": "io_count",
                "name": "Input Channels",
                "value": "16",
                "is_critical": True
            }
        ]
    }

    try:
        result = client.add_part(new_part)
        print(f"✓ Part added successfully: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
