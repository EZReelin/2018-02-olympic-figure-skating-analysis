"""
Simple example: Match DCS parts from text description.

This example shows the simplest way to match parts using just a text description.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.parts_agent import PartsMatchingAgent
from src.core.models import DocumentSubmission, ProcessingRequest, DocumentType


async def main():
    """Main function to demonstrate simple text matching."""

    # Initialize the agent
    print("Initializing Parts Matching Agent...")
    agent = PartsMatchingAgent()
    await agent.initialize()
    print("✓ Agent initialized\n")

    # Example requirements
    text_description = """
    Need a 24V DC digital input module with 16 channels.
    Operating temperature: -20°C to 60°C
    Must be compatible with Siemens S7-1500 PLCs
    Preferred mounting: DIN rail
    """

    print(f"Customer requirements:\n{text_description}\n")
    print("Processing request...")

    # Create submission
    submission = DocumentSubmission(
        document_type=DocumentType.TEXT,
        text_description=text_description,
        additional_context="For industrial automation project"
    )

    # Create processing request
    request = ProcessingRequest(
        submission=submission,
        max_alternatives=3,
        min_confidence_threshold=50.0
    )

    # Process the request
    result = await agent.process_request(request)

    # Display results
    print("\n" + "="*70)
    print("MATCHING RESULTS")
    print("="*70)

    if result.primary_match:
        print(f"\n✓ PRIMARY MATCH FOUND")
        print(f"  Part Number: {result.primary_match.part.part_number}")
        print(f"  Description: {result.primary_match.part.description}")
        print(f"  Confidence: {result.primary_match.confidence_score:.1f}%")
        print(f"  Level: {result.primary_match.confidence_level.value.upper()}")
        print(f"\n  Justification:")
        print(f"  {result.primary_match.justification}")

        # Show matched specifications
        if result.primary_match.matched_specifications:
            print(f"\n  Matched Specifications:")
            for spec in result.primary_match.matched_specifications:
                status = "✓" if spec.is_match else "✗"
                print(f"    {status} {spec.spec_name}: {spec.customer_value} → {spec.part_value}")

        # Show warnings if any
        if result.primary_match.warnings:
            print(f"\n  ⚠️ Warnings:")
            for warning in result.primary_match.warnings:
                print(f"    - {warning}")

        # Show alternatives
        if result.alternative_matches:
            print(f"\n  Alternative Matches:")
            for i, alt in enumerate(result.alternative_matches, 1):
                print(f"    {i}. {alt.part.part_number} - {alt.confidence_score:.1f}%")

    else:
        print("\n✗ No suitable match found")
        if result.review_reason:
            print(f"  Reason: {result.review_reason}")

    # Show if human review is needed
    if result.requires_human_review:
        print(f"\n⚠️ HUMAN REVIEW RECOMMENDED")
        print(f"   Reason: {result.review_reason}")

    print(f"\nProcessing time: {result.processing_time_seconds:.2f} seconds")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
