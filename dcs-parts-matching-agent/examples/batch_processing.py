"""
Example: Batch Processing Multiple Requests.

This example shows how to process multiple part matching requests efficiently.
"""

import asyncio
import time
from pathlib import Path
import sys
import csv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.parts_agent import PartsMatchingAgent
from src.core.models import DocumentSubmission, ProcessingRequest, DocumentType


async def process_single_request(agent, description, request_id):
    """Process a single matching request."""

    submission = DocumentSubmission(
        document_type=DocumentType.TEXT,
        text_description=description
    )

    request = ProcessingRequest(
        submission=submission,
        max_alternatives=2,
        min_confidence_threshold=50.0
    )

    try:
        result = await agent.process_request(request)
        return {
            "request_id": request_id,
            "description": description,
            "success": True,
            "part_number": result.primary_match.part.part_number if result.primary_match else None,
            "confidence": result.primary_match.confidence_score if result.primary_match else 0,
            "requires_review": result.requires_human_review,
            "processing_time": result.processing_time_seconds
        }
    except Exception as e:
        return {
            "request_id": request_id,
            "description": description,
            "success": False,
            "error": str(e),
            "processing_time": 0
        }


async def batch_process_sequential(agent, requests):
    """Process requests sequentially (one after another)."""

    print("\n" + "="*70)
    print("SEQUENTIAL PROCESSING")
    print("="*70)

    start_time = time.time()
    results = []

    for i, description in enumerate(requests, 1):
        print(f"\nProcessing request {i}/{len(requests)}...")
        result = await process_single_request(agent, description, f"SEQ-{i}")
        results.append(result)

        if result["success"]:
            print(f"  ✓ Matched: {result['part_number']} ({result['confidence']:.1f}%)")
        else:
            print(f"  ✗ Failed: {result.get('error', 'No match')}")

    total_time = time.time() - start_time
    print(f"\n✓ Sequential processing complete in {total_time:.2f}s")

    return results, total_time


async def batch_process_concurrent(agent, requests):
    """Process requests concurrently (parallel)."""

    print("\n" + "="*70)
    print("CONCURRENT PROCESSING")
    print("="*70)

    start_time = time.time()

    # Create tasks for all requests
    tasks = [
        process_single_request(agent, description, f"CON-{i}")
        for i, description in enumerate(requests, 1)
    ]

    # Run all tasks concurrently
    print(f"\nProcessing {len(tasks)} requests in parallel...")
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # Print results
    for result in results:
        if result["success"]:
            print(f"  ✓ {result['request_id']}: {result['part_number']} ({result['confidence']:.1f}%)")
        else:
            print(f"  ✗ {result['request_id']}: Failed")

    print(f"\n✓ Concurrent processing complete in {total_time:.2f}s")

    return results, total_time


def print_performance_summary(seq_results, seq_time, con_results, con_time):
    """Print performance comparison summary."""

    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)

    # Calculate statistics
    seq_success = sum(1 for r in seq_results if r["success"])
    con_success = sum(1 for r in con_results if r["success"])

    seq_avg_time = sum(r["processing_time"] for r in seq_results) / len(seq_results)
    con_avg_time = sum(r["processing_time"] for r in con_results) / len(con_results)

    speedup = seq_time / con_time if con_time > 0 else 0

    print(f"\nSequential Processing:")
    print(f"  Total time: {seq_time:.2f}s")
    print(f"  Successful: {seq_success}/{len(seq_results)}")
    print(f"  Avg per request: {seq_avg_time:.2f}s")

    print(f"\nConcurrent Processing:")
    print(f"  Total time: {con_time:.2f}s")
    print(f"  Successful: {con_success}/{len(con_results)}")
    print(f"  Avg per request: {con_avg_time:.2f}s")

    print(f"\nPerformance Gain:")
    print(f"  Speedup: {speedup:.2f}x faster")
    print(f"  Time saved: {seq_time - con_time:.2f}s")

    return {
        "sequential": {
            "total_time": seq_time,
            "successful": seq_success,
            "avg_time": seq_avg_time
        },
        "concurrent": {
            "total_time": con_time,
            "successful": con_success,
            "avg_time": con_avg_time
        },
        "speedup": speedup
    }


def export_results_to_csv(results, filename):
    """Export results to CSV file."""

    csv_path = Path(filename)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, 'w', newline='') as f:
        fieldnames = [
            'request_id', 'description', 'success', 'part_number',
            'confidence', 'requires_review', 'processing_time', 'error'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow({
                'request_id': result['request_id'],
                'description': result['description'],
                'success': result['success'],
                'part_number': result.get('part_number', ''),
                'confidence': result.get('confidence', 0),
                'requires_review': result.get('requires_review', False),
                'processing_time': result.get('processing_time', 0),
                'error': result.get('error', '')
            })

    print(f"\n✓ Results exported to: {csv_path}")


async def main():
    """Main function for batch processing example."""

    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "BATCH PROCESSING EXAMPLE" + " "*23 + "║")
    print("╚" + "="*68 + "╝")

    # Initialize agent
    print("\nInitializing Parts Matching Agent...")
    agent = PartsMatchingAgent()
    await agent.initialize()
    print("✓ Agent initialized\n")

    # Sample batch of requests
    batch_requests = [
        "24V DC digital input module with 16 channels",
        "Analog output module, 8 channels, 12-bit resolution",
        "Power supply unit 24VDC 10A output",
        "PLC CPU module with Ethernet communication",
        "Digital output module 8 channels relay type",
        "Analog input module 4-20mA current input",
        "Communication module Modbus TCP",
        "Temperature sensor module RTD type",
    ]

    print(f"Batch size: {len(batch_requests)} requests\n")

    # Process sequentially
    seq_results, seq_time = await batch_process_sequential(agent, batch_requests)

    # Wait a moment between modes
    await asyncio.sleep(1)

    # Process concurrently
    con_results, con_time = await batch_process_concurrent(agent, batch_requests)

    # Print performance summary
    summary = print_performance_summary(seq_results, seq_time, con_results, con_time)

    # Export results
    export_results_to_csv(
        con_results,
        "examples/output/batch_results.csv"
    )

    print("\n" + "="*70)
    print("Batch processing example completed!")
    print("="*70 + "\n")

    # Recommendations
    print("💡 RECOMMENDATIONS:")
    print(f"  - For {len(batch_requests)} requests, concurrent is {summary['speedup']:.1f}x faster")
    print(f"  - Use concurrent processing for batches of 3+ requests")
    print(f"  - Monitor API rate limits when processing large batches")
    print(f"  - Consider implementing a queue system for production")


if __name__ == "__main__":
    asyncio.run(main())
