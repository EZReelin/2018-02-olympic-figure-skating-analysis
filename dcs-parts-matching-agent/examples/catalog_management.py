"""
Example: Catalog Management Operations.

This example shows how to manage the DCS parts catalog, including indexing,
adding parts, and creating catalog files.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.catalog_manager import CatalogManager
from src.database.vector_store import VectorStore
from src.core.models import DCSPart, Specification, SpecificationType, DimensionalData


async def create_sample_json_catalog():
    """Create a sample JSON catalog file."""

    catalog_data = {
        "catalog_name": "DCS Sample Catalog 2024",
        "version": "1.0",
        "parts": [
            {
                "part_number": "DCS-DI-1624",
                "description": "24V DC Digital Input Module, 16 channels, isolated",
                "category": "Digital Input",
                "subcategory": "DI Module",
                "specifications": [
                    {
                        "spec_type": "voltage_rating",
                        "name": "Voltage Rating",
                        "value": "24",
                        "unit": "VDC",
                        "is_critical": True
                    },
                    {
                        "spec_type": "io_count",
                        "name": "Input Channels",
                        "value": "16",
                        "is_critical": True
                    },
                    {
                        "spec_type": "temperature_range",
                        "name": "Operating Temperature",
                        "value": "-20 to 60",
                        "unit": "°C",
                        "is_critical": True
                    },
                    {
                        "spec_type": "connection_type",
                        "name": "Connection",
                        "value": "Screw terminals",
                        "is_critical": False
                    }
                ],
                "dimensions": {
                    "width": 100.0,
                    "height": 150.0,
                    "depth": 50.0,
                    "unit": "mm"
                },
                "compatibility_info": [
                    "Siemens S7-1500",
                    "Allen-Bradley ControlLogix"
                ],
                "technical_notes": "Hot-swappable, DIN rail mounting"
            },
            {
                "part_number": "DCS-DO-0824",
                "description": "24V DC Digital Output Module, 8 channels, relay",
                "category": "Digital Output",
                "subcategory": "DO Module",
                "specifications": [
                    {
                        "spec_type": "voltage_rating",
                        "name": "Voltage Rating",
                        "value": "24",
                        "unit": "VDC",
                        "is_critical": True
                    },
                    {
                        "spec_type": "io_count",
                        "name": "Output Channels",
                        "value": "8",
                        "is_critical": True
                    },
                    {
                        "spec_type": "current_rating",
                        "name": "Current per Channel",
                        "value": "2",
                        "unit": "A",
                        "is_critical": True
                    }
                ],
                "dimensions": {
                    "width": 80.0,
                    "height": 150.0,
                    "depth": 50.0,
                    "unit": "mm"
                }
            },
            {
                "part_number": "DCS-AI-0812",
                "description": "Analog Input Module, 8 channels, 12-bit resolution",
                "category": "Analog Input",
                "subcategory": "AI Module",
                "specifications": [
                    {
                        "spec_type": "voltage_rating",
                        "name": "Input Range",
                        "value": "0-10",
                        "unit": "V",
                        "is_critical": True
                    },
                    {
                        "spec_type": "io_count",
                        "name": "Channels",
                        "value": "8",
                        "is_critical": True
                    },
                    {
                        "spec_type": "other",
                        "name": "Resolution",
                        "value": "12",
                        "unit": "bit",
                        "is_critical": True
                    }
                ]
            },
            {
                "part_number": "DCS-PSU-2410",
                "description": "Power Supply Unit, 24VDC, 10A output",
                "category": "Power Supply",
                "subcategory": "PSU",
                "specifications": [
                    {
                        "spec_type": "voltage_rating",
                        "name": "Output Voltage",
                        "value": "24",
                        "unit": "VDC",
                        "is_critical": True
                    },
                    {
                        "spec_type": "current_rating",
                        "name": "Output Current",
                        "value": "10",
                        "unit": "A",
                        "is_critical": True
                    },
                    {
                        "spec_type": "power_consumption",
                        "name": "Output Power",
                        "value": "240",
                        "unit": "W",
                        "is_critical": False
                    }
                ]
            },
            {
                "part_number": "DCS-CPU-3201",
                "description": "PLC CPU Module, 32MB memory, Ethernet",
                "category": "Controller",
                "subcategory": "CPU",
                "specifications": [
                    {
                        "spec_type": "other",
                        "name": "Memory",
                        "value": "32",
                        "unit": "MB",
                        "is_critical": False
                    },
                    {
                        "spec_type": "protocol",
                        "name": "Communication",
                        "value": "Ethernet/IP, Modbus TCP",
                        "is_critical": True
                    }
                ]
            }
        ]
    }

    # Save to catalog directory
    catalog_dir = Path("data/catalog")
    catalog_dir.mkdir(parents=True, exist_ok=True)

    catalog_file = catalog_dir / "sample_catalog.json"
    with open(catalog_file, 'w') as f:
        json.dump(catalog_data, f, indent=2)

    print(f"✓ Created sample catalog: {catalog_file}")
    print(f"  Total parts: {len(catalog_data['parts'])}")

    return catalog_file


async def index_catalog_example():
    """Example: Index catalog from directory."""

    print("\n" + "="*70)
    print("CATALOG INDEXING EXAMPLE")
    print("="*70 + "\n")

    # Initialize vector store and catalog manager
    print("Initializing components...")
    vector_store = VectorStore()
    await vector_store.initialize()

    catalog_manager = CatalogManager(vector_store)
    print("✓ Components initialized\n")

    # Index catalog directory
    print("Indexing catalog directory...")
    stats = await catalog_manager.index_catalog_directory()

    print(f"\n✓ Indexing complete:")
    print(f"  PDF files processed: {stats.get('pdf_files', 0)}")
    print(f"  JSON files processed: {stats.get('json_files', 0)}")
    print(f"  CSV files processed: {stats.get('csv_files', 0)}")
    print(f"  Total parts indexed: {stats.get('parts_indexed', 0)}")
    print(f"  Errors: {stats.get('errors', 0)}")

    # Get catalog statistics
    print("\nCatalog Statistics:")
    catalog_stats = await catalog_manager.get_catalog_stats()
    print(f"  Catalog entries: {catalog_stats.get('catalog_count', 0)}")
    print(f"  Drawing entries: {catalog_stats.get('drawings_count', 0)}")


async def add_single_part_example():
    """Example: Add a single part programmatically."""

    print("\n" + "="*70)
    print("ADD SINGLE PART EXAMPLE")
    print("="*70 + "\n")

    # Initialize
    vector_store = VectorStore()
    await vector_store.initialize()
    catalog_manager = CatalogManager(vector_store)

    # Create a new part
    new_part = DCSPart(
        part_number="DCS-TEST-9999",
        description="Test Ethernet Communication Module",
        category="Communication",
        subcategory="Network Interface",
        specifications=[
            Specification(
                spec_type=SpecificationType.PROTOCOL,
                name="Protocol",
                value="Ethernet/IP, Modbus TCP",
                is_critical=True
            ),
            Specification(
                spec_type=SpecificationType.VOLTAGE_RATING,
                name="Voltage",
                value="24",
                unit="VDC",
                is_critical=True
            ),
            Specification(
                spec_type=SpecificationType.OTHER,
                name="Ports",
                value="2",
                unit="RJ45",
                is_critical=False
            )
        ],
        dimensions=DimensionalData(
            width=90.0,
            height=100.0,
            depth=60.0,
            unit="mm"
        ),
        compatibility_info=[
            "Siemens S7-1200/1500",
            "Rockwell ControlLogix"
        ],
        technical_notes="Dual port, hot-swappable, DIN rail mounting",
        metadata={
            "manufacturer": "Example Corp",
            "warranty_years": 2
        }
    )

    print(f"Adding part: {new_part.part_number}")
    entry_id = await catalog_manager.add_single_part(new_part)
    print(f"✓ Part added successfully")
    print(f"  Entry ID: {entry_id}")
    print(f"  Part Number: {new_part.part_number}")
    print(f"  Description: {new_part.description}")


async def update_part_example():
    """Example: Update an existing part."""

    print("\n" + "="*70)
    print("UPDATE PART EXAMPLE")
    print("="*70 + "\n")

    # Initialize
    vector_store = VectorStore()
    await vector_store.initialize()
    catalog_manager = CatalogManager(vector_store)

    # Update the test part we just added
    updated_part = DCSPart(
        part_number="DCS-TEST-9999",
        description="Test Ethernet Communication Module - UPDATED",
        category="Communication",
        subcategory="Network Interface",
        specifications=[
            Specification(
                spec_type=SpecificationType.PROTOCOL,
                name="Protocol",
                value="Ethernet/IP, Modbus TCP, Profinet",  # Added Profinet
                is_critical=True
            ),
            Specification(
                spec_type=SpecificationType.VOLTAGE_RATING,
                name="Voltage",
                value="24",
                unit="VDC",
                is_critical=True
            ),
            Specification(
                spec_type=SpecificationType.OTHER,
                name="Ports",
                value="4",  # Updated from 2 to 4
                unit="RJ45",
                is_critical=False
            )
        ],
        technical_notes="Quad port, hot-swappable, DIN rail mounting",  # Updated
        metadata={
            "manufacturer": "Example Corp",
            "warranty_years": 3,  # Increased warranty
            "updated": True
        }
    )

    print(f"Updating part: {updated_part.part_number}")
    success = await catalog_manager.update_part("DCS-TEST-9999", updated_part)

    if success:
        print(f"✓ Part updated successfully")
        print(f"  Part Number: {updated_part.part_number}")
        print(f"  New Description: {updated_part.description}")
    else:
        print(f"✗ Failed to update part")


async def main():
    """Main function to run all examples."""

    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "CATALOG MANAGEMENT EXAMPLES" + " "*21 + "║")
    print("╚" + "="*68 + "╝")

    # Create sample catalog file
    print("\nStep 1: Creating sample catalog file...")
    catalog_file = await create_sample_json_catalog()

    # Index the catalog
    print("\nStep 2: Indexing catalog...")
    await index_catalog_example()

    # Add a single part
    print("\nStep 3: Adding a single part...")
    await add_single_part_example()

    # Update a part
    print("\nStep 4: Updating a part...")
    await update_part_example()

    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
