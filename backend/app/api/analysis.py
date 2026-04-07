"""
# Architect: Meet Kumar
# InsightAI - Analysis Endpoints
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.dataset import Dataset, DatasetStatus
from app.models.analysis_session import AnalysisSession, AnalysisStatus
from app.api.auth import get_current_active_user
from app.api.schemas import (
    StartAnalysisRequest,
    AnalysisResponse,
    AnalysisStreamEvent
)
from app.services.tasks import run_analysis, process_data_task

router = APIRouter()


@router.get("/sessions")
async def list_analysis_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dataset_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's analysis sessions."""
    query = select(AnalysisSession).where(AnalysisSession.user_id == current_user.id)
    
    if dataset_id:
        query = query.where(AnalysisSession.dataset_id == dataset_id)
    
    # Get total count
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # Get paginated results
    query = query.order_by(desc(AnalysisSession.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return {
        "items": [AnalysisResponse.model_validate(s) for s in sessions],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/sessions/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_session(
    analysis_id: str,
    include_thoughts: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific analysis session."""
    result = await db.execute(
        select(AnalysisSession)
        .options(joinedload(AnalysisSession.dataset))
        .where(
            AnalysisSession.id == analysis_id,
            AnalysisSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found"
        )
    
    return AnalysisResponse.model_validate(session)


@router.post("/start", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    request: StartAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a new analysis session."""
    # Verify dataset exists and belongs to user
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == request.dataset_id,
            Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    if dataset.status != DatasetStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset is not ready. Current status: {dataset.status.value}"
        )
    
    # Create analysis session
    analysis = AnalysisSession(
        user_id=current_user.id,
        dataset_id=dataset.id,
        query=request.query,
        analysis_type=request.analysis_type.value,
        status=AnalysisStatus.QUEUED,
    )
    
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    # Enqueue analysis task with FastAPI BackgroundTasks
    background_tasks.add_task(
        process_data_task,
        dataset.file_path,
        request.query or "Analyze this data and provide insights.",
        str(analysis.id)
    )
    
    # Update user's analysis count
    current_user.analyses_count += 1
    await db.commit()
    
    return AnalysisResponse.model_validate(analysis)


@router.get("/sessions/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analysis session status."""
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == analysis_id,
            AnalysisSession.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found"
        )
    
    return {
        "analysis_id": analysis_id,
        "status": analysis.status,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at,
    }


@router.delete("/sessions/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an analysis session."""
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == analysis_id,
            AnalysisSession.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found"
        )
    
    # Note: Cannot easily "cancel" a FastAPI BackgroundTask once it starts
    # We just update the status in the database
    if analysis.status in [AnalysisStatus.QUEUED, AnalysisStatus.RUNNING]:
        analysis.status = AnalysisStatus.CANCELLED
        await db.commit()
    
    return None


# ============== SSE Streaming Endpoint ==============

async def generate_analysis_stream(
    analysis_id: str,
    user_id: str,
    db: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for analysis progress.
    
    Yields SSE formatted events with agent thoughts and progress updates.
    """
    # Get analysis session
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == analysis_id,
            AnalysisSession.user_id == user_id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        yield f"event: error\ndata: {json.dumps({'message': 'Analysis session not found'})}\n\n"
        return
    
    # Send initial event
    yield f"event: connected\ndata: {json.dumps({'analysis_id': analysis_id, 'status': analysis.status.value})}\n\n"
    
    # Track last thought count to detect new thoughts
    last_thought_count = len(analysis.thought_process or [])
    
    # Stream for up to 10 minutes or until completion
    max_iterations = 600  # 10 minutes at 1 second intervals
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Refresh analysis from database
        await db.refresh(analysis)
        
        # Check for new thoughts
        current_thoughts = analysis.thought_process or []
        if len(current_thoughts) > last_thought_count:
            # Send new thoughts
            for i in range(last_thought_count, len(current_thoughts)):
                thought = current_thoughts[i]
                event_data = {
                    "type": thought.get("type"),
                    "content": thought.get("content"),
                    "timestamp": thought.get("timestamp"),
                    "metadata": thought.get("metadata"),
                }
                yield f"event: thought\ndata: {json.dumps(event_data)}\n\n"
            
            last_thought_count = len(current_thoughts)
        
        # Check task status via Celery
        if analysis.task_id:
            task_result = AsyncResult(analysis.task_id, app=celery_app)
            
            if task_result.info and isinstance(task_result.info, dict):
                progress = task_result.info.get("progress", 0)
                message = task_result.info.get("message", "")
                
                yield f"event: progress\ndata: {json.dumps({'progress': progress, 'message': message})}\n\n"
        
        # Check if analysis is complete
        if analysis.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            # Send final result
            result_data = {
                "status": analysis.status.value,
                "result_summary": analysis.result_summary,
                "insights": analysis.insights,
                "duration_seconds": analysis.duration_seconds,
            }
            
            if analysis.status == AnalysisStatus.FAILED:
                result_data["error"] = analysis.error_message
                yield f"event: error\ndata: {json.dumps(result_data)}\n\n"
            else:
                yield f"event: complete\ndata: {json.dumps(result_data)}\n\n"
            
            break
        
        # Wait before next check
        await asyncio.sleep(1)
    
    # Send close event
    yield f"event: close\ndata: {json.dumps({'message': 'Stream closed'})}\n\n"


@router.get("/stream/{analysis_id}")
async def stream_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream analysis progress via Server-Sent Events (SSE).
    
    This endpoint provides real-time updates on the agent's thought process,
    progress indicators, and final results.
    """
    return StreamingResponse(
        generate_analysis_stream(analysis_id, str(current_user.id), db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# ============== WebSocket Alternative (for future enhancement) ==============

@router.post("/sessions/{analysis_id}/retry", response_model=AnalysisResponse)
async def retry_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed analysis."""
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == analysis_id,
            AnalysisSession.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found"
        )
    
    if analysis.status != AnalysisStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed analyses can be retried"
        )
    
    # Reset status
    analysis.status = AnalysisStatus.QUEUED
    analysis.error_message = None
    analysis.thought_process = []
    analysis.result_summary = None
    analysis.generated_code = None
    analysis.output_files = None
    analysis.insights = None
    analysis.started_at = None
    analysis.completed_at = None
    analysis.duration_seconds = None
    
    await db.commit()
    
    # Enqueue new task
    task = celery_app.send_task(
        "app.services.tasks.run_analysis",
        args=[str(analysis.id), str(analysis.dataset_id), analysis.query],
        queue="analysis"
    )
    
    analysis.task_id = task.id
    await db.commit()
    
    return AnalysisResponse.model_validate(analysis)
