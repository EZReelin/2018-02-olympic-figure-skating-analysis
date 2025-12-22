"""
FastAPI REST API for DCS Parts Matching Agent.

Provides HTTP endpoints for parts matching, catalog management,
and system administration.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
import uvicorn

from ..core.models import (
    ProcessingRequest, MatchingResult, DocumentSubmission,
    DocumentType, SystemHealth
)
from ..core.config import get_settings, ensure_directories
from ..agents.parts_agent import PartsMatchingAgent
from ..agents.catalog_manager import CatalogManager
from ..database.vector_store import VectorStore
from ..utils.logger import setup_logging, get_logger
from ..utils.helpers import sanitize_filename, validate_file_size

# Initialize settings and logging
settings = get_settings()
ensure_directories()
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered DCS parts matching system for industrial automation",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global agent instance
agent: Optional[PartsMatchingAgent] = None
catalog_manager: Optional[CatalogManager] = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup."""
    global agent, catalog_manager

    logger.info("Starting DCS Parts Matching Agent API")

    # Initialize agent
    agent = PartsMatchingAgent()
    await agent.initialize()

    # Initialize catalog manager
    vector_store = agent.vector_store
    catalog_manager = CatalogManager(vector_store)

    # Auto-index catalog if configured
    if settings.auto_index_on_startup:
        logger.info("Auto-indexing catalog on startup")
        try:
            stats = await catalog_manager.index_catalog_directory()
            logger.info(f"Catalog indexed: {stats}")
        except Exception as e:
            logger.error(f"Auto-indexing failed: {e}")

    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down DCS Parts Matching Agent API")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health", response_model=SystemHealth)
async def health_check():
    """
    Check system health and status.

    Returns system health information including database status
    and catalog statistics.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    health = await agent.get_system_health()

    return SystemHealth(
        status=health.get("status", "unknown"),
        vector_db_status=health.get("vector_db_status", "unknown"),
        catalog_entries_count=health.get("catalog_entries_count", 0),
        drawing_repository_count=health.get("drawing_repository_count", 0),
        last_index_update=None,
        uptime_seconds=0.0,  # Would track actual uptime in production
        version=settings.version
    )


@app.post("/api/match", response_model=MatchingResult)
async def match_parts(
    file: Optional[UploadFile] = File(None),
    text_description: Optional[str] = Form(None),
    additional_context: Optional[str] = Form(None),
    max_alternatives: int = Form(3),
    min_confidence: float = Form(50.0),
    enable_visual_comparison: bool = Form(True)
):
    """
    Match customer requirements to DCS parts.

    Submit either a file (PDF, image, CAD) or text description.
    Returns matched parts with confidence scores and justification.

    Args:
        file: Optional file upload (PDF, image, DWG, DXF)
        text_description: Optional text description of requirements
        additional_context: Optional additional context
        max_alternatives: Maximum number of alternative matches (default: 3)
        min_confidence: Minimum confidence threshold 0-100 (default: 50)
        enable_visual_comparison: Enable visual comparison (default: true)

    Returns:
        MatchingResult with primary match and alternatives
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    if not file and not text_description:
        raise HTTPException(
            status_code=400,
            detail="Either file or text_description must be provided"
        )

    try:
        # Handle file upload
        file_path = None
        doc_type = DocumentType.TEXT

        if file:
            # Validate file
            if file.size and file.size > settings.max_upload_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum ({settings.max_upload_size_mb}MB)"
                )

            # Save uploaded file
            filename = sanitize_filename(file.filename)
            file_path = settings.upload_dir / filename

            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)

            # Detect document type
            extension = Path(filename).suffix.lower()
            if extension == '.pdf':
                doc_type = DocumentType.PDF
            elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                doc_type = DocumentType.IMAGE
            elif extension == '.dwg':
                doc_type = DocumentType.CAD_DWG
            elif extension == '.dxf':
                doc_type = DocumentType.CAD_DXF
            else:
                doc_type = DocumentType.UNKNOWN

        # Create submission
        submission = DocumentSubmission(
            file_path=str(file_path) if file_path else None,
            document_type=doc_type,
            text_description=text_description,
            additional_context=additional_context
        )

        # Create processing request
        request = ProcessingRequest(
            submission=submission,
            enable_visual_comparison=enable_visual_comparison,
            max_alternatives=max_alternatives,
            min_confidence_threshold=min_confidence
        )

        # Process request
        result = await agent.process_request(request)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parts matching failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/catalog/index")
async def index_catalog(background_tasks: BackgroundTasks):
    """
    Reindex the parts catalog.

    Scans the catalog directory and indexes all parts into the vector database.
    This operation runs in the background.

    Returns:
        Acknowledgment that indexing has started
    """
    if not catalog_manager:
        raise HTTPException(status_code=503, detail="Catalog manager not initialized")

    async def run_indexing():
        try:
            stats = await catalog_manager.index_catalog_directory(force_reindex=True)
            logger.info(f"Catalog reindexing complete: {stats}")
        except Exception as e:
            logger.error(f"Catalog reindexing failed: {e}")

    background_tasks.add_task(run_indexing)

    return {
        "status": "started",
        "message": "Catalog indexing started in background"
    }


@app.get("/api/catalog/stats")
async def get_catalog_stats():
    """
    Get catalog statistics.

    Returns:
        Dictionary with catalog statistics including part counts
    """
    if not catalog_manager:
        raise HTTPException(status_code=503, detail="Catalog manager not initialized")

    stats = await catalog_manager.get_catalog_stats()
    return stats


@app.post("/api/catalog/parts")
async def add_part(part_data: dict):
    """
    Add a new part to the catalog.

    Args:
        part_data: DCSPart data as JSON

    Returns:
        Confirmation with entry ID
    """
    if not catalog_manager:
        raise HTTPException(status_code=503, detail="Catalog manager not initialized")

    try:
        from ..core.models import DCSPart

        # Parse part data
        part = DCSPart(**part_data)

        # Add to catalog
        entry_id = await catalog_manager.add_single_part(part)

        return {
            "status": "success",
            "entry_id": entry_id,
            "part_number": part.part_number
        }

    except Exception as e:
        logger.error(f"Failed to add part: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to add part: {str(e)}")


@app.get("/api/catalog/parts/{part_number}")
async def get_part(part_number: str):
    """
    Get part information by part number.

    Args:
        part_number: DCS part number

    Returns:
        Part information if found
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    result = await agent.vector_store.get_part_by_number(part_number)

    if not result:
        raise HTTPException(status_code=404, detail=f"Part {part_number} not found")

    return result


@app.get("/api/version")
async def get_version():
    """Get API version information."""
    return {
        "version": settings.version,
        "app_name": settings.app_name
    }


def start_server():
    """Start the API server."""
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )


if __name__ == "__main__":
    start_server()
