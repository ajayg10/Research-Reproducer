"""REST API routes for reproduction pipeline."""

import structlog
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path

from backend.models.schemas import (
    ReproductionRequest,
    ReproductionResponse,
    PipelineStatusResponse
)
from backend.models.state import PipelineState
from backend.orchestration.pipeline import pipeline
from backend.services.storage import storage_service


logger = structlog.get_logger()

router = APIRouter()


@router.post("/reproduce", response_model=ReproductionResponse)
async def start_reproduction(request: ReproductionRequest):
    """
    Start a new reproduction pipeline.

    Args:
        request: Reproduction request with paper source

    Returns:
        Pipeline ID and status
    """
    try:
        logger.info("api_start_reproduction", paper_source=request.paper_source)

        pipeline_id = await pipeline.start_reproduction(
            paper_source=request.paper_source,
            paper_title=request.paper_title
        )

        return ReproductionResponse(
            pipeline_id=pipeline_id,
            status="started",
            message=f"Pipeline {pipeline_id} started successfully"
        )

    except Exception as e:
        logger.error("start_reproduction_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reproduce/upload", response_model=ReproductionResponse)
async def upload_and_reproduce(file: UploadFile = File(...)):
    """
    Upload a PDF and start reproduction pipeline.

    Args:
        file: Uploaded PDF file

    Returns:
        Pipeline ID and status
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        logger.info("api_upload_pdf", filename=file.filename)

        # Save uploaded file
        upload_dir = Path("storage/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        content = await file.read()

        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info("pdf_saved", path=str(file_path), size=len(content))

        # Start pipeline
        pipeline_id = await pipeline.start_reproduction(
            paper_source=str(file_path),
            paper_title=file.filename.replace('.pdf', '')
        )

        return ReproductionResponse(
            pipeline_id=pipeline_id,
            status="started",
            message=f"Pipeline {pipeline_id} started with uploaded PDF"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_and_reproduce_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/{pipeline_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(pipeline_id: str):
    """
    Get pipeline status.

    Args:
        pipeline_id: Pipeline identifier

    Returns:
        Pipeline status and details
    """
    try:
        state = await pipeline.get_status(pipeline_id)

        if not state:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        return PipelineStatusResponse(
            pipeline_id=state.pipeline_id,
            status=state.status.value,
            current_stage=state.status.value,
            retry_count=state.retry_count,
            created_at=state.created_at.isoformat(),
            updated_at=state.updated_at.isoformat(),
            error=state.error
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_pipeline_status_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/{pipeline_id}/full")
async def get_pipeline_full(pipeline_id: str):
    """
    Get complete pipeline state including all agent outputs.

    Args:
        pipeline_id: Pipeline identifier

    Returns:
        Full pipeline state
    """
    try:
        state = await pipeline.get_status(pipeline_id)

        if not state:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        return state.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_pipeline_full_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipelines", response_model=List[PipelineStatusResponse])
async def list_pipelines(limit: int = 10):
    """
    List recent pipelines.

    Args:
        limit: Maximum number of pipelines to return

    Returns:
        List of pipeline statuses
    """
    try:
        states = await storage_service.list_pipelines(limit=limit)

        return [
            PipelineStatusResponse(
                pipeline_id=state.pipeline_id,
                status=state.status.value,
                current_stage=state.status.value,
                retry_count=state.retry_count,
                created_at=state.created_at.isoformat(),
                updated_at=state.updated_at.isoformat(),
                error=state.error
            )
            for state in states
        ]

    except Exception as e:
        logger.error("list_pipelines_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/{pipeline_id}/report")
async def get_verification_report(pipeline_id: str):
    """
    Get verification report for completed pipeline.

    Args:
        pipeline_id: Pipeline identifier

    Returns:
        Verification report
    """
    try:
        state = await pipeline.get_status(pipeline_id)

        if not state:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        if not state.verifier_output:
            raise HTTPException(
                status_code=400,
                detail="Pipeline has not completed verification yet"
            )

        return state.verifier_output

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_verification_report_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/{pipeline_id}/code")
async def get_generated_code(pipeline_id: str):
    """
    Get generated code for pipeline.

    Args:
        pipeline_id: Pipeline identifier

    Returns:
        Generated code files
    """
    try:
        state = await pipeline.get_status(pipeline_id)

        if not state:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        if not state.codegen_output:
            raise HTTPException(
                status_code=400,
                detail="Code generation not completed yet"
            )

        return state.codegen_output.get("implementation")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_generated_code_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
