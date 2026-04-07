"""
# Architect: Meet Kumar
# InsightAI - Analyze Data Endpoint (LangChain Gemini Integration)
"""

import os
import traceback
import uuid
import asyncio
from uuid import UUID
from typing import Any, Dict, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse, FileResponse
from celery.result import AsyncResult
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.worker import process_data_task, celery_app
from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.analysis_session import AnalysisSession
from app.api.schemas import ChatRequest, ChatResponse, SessionListResponse, SessionResponse, AnalysisResponse, AnalysisCreateResponse
from sqlalchemy import select, desc
from langchain_groq import ChatGroq
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import pandas as pd

from app.api.auth import get_current_active_user
from app.models.user import User

router = APIRouter()

PROMPT_TEMPLATE = """
You are an expert Data Scientist. Analyze the following dataset metadata and first 5 rows.

Metadata: {metadata}
First 5 rows: {df_head}

Provide a structured JSON response containing:
1. 3 key actionable business insights.
2. Identification of any anomalies or dirty data.
3. A suggested strategy for further analysis.

Response format must be exactly:
{{
    "insights": ["insight 1", "insight 2", "insight 3"],
    "anomalies": ["anomaly 1", "anomaly 2"],
    "strategy": "Your detailed strategy here"
}}
"""

@router.post("/analyze-data", response_model=AnalysisCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle data upload and analysis request.
    """
    try:
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        job_uuid = UUID(job_id)
        
        # Save uploaded file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{job_id}.csv")
        
        contents = await file.read()
        file_size = len(contents)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)

        # 1. Create Dataset record
        new_dataset = Dataset(
            id=job_uuid,
            user_id=current_user.id,
            name=file.filename,
            file_path=file_path,
            original_filename=file.filename,
            file_size=file_size,
            status="processing"
        )
        db.add(new_dataset)

        # 2. Create AnalysisSession record
        new_session = AnalysisSession(
            id=job_uuid,
            user_id=current_user.id,
            dataset_id=job_uuid,
            task_id=job_id,
            status="running"
        )
        db.add(new_session)
        
        await db.commit()

        task = process_data_task.apply_async(
            args=[file_path, PROMPT_TEMPLATE, str(job_uuid)],
            task_id=job_id
        )
        
        return {
            "id": str(job_uuid),
            "status": "processing",
            "message": "Analysis started successfully"
        }

    except Exception as e:
        traceback.print_exc()
        error_message = "An unexpected error occurred during file upload."
        if settings.DEBUG:
            error_message = str(e)
            
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": error_message,
                "error_type": type(e).__name__ if settings.DEBUG else "InternalServerError"
            }
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all analysis sessions for current user ordered by creation date.
    """
    try:
        # Join AnalysisSession with Dataset to get the original filename
        query = (
            select(
                AnalysisSession.id,
                Dataset.original_filename,
                AnalysisSession.created_at
            )
            .join(Dataset, AnalysisSession.dataset_id == Dataset.id)
            .where(AnalysisSession.user_id == current_user.id)
            .order_by(desc(AnalysisSession.created_at))
        )
        
        result = await db.execute(query)
        sessions_data = result.all()
        
        sessions = [
            SessionResponse(
                id=row.id,
                filename=row.original_filename,
                created_at=row.created_at
            )
            for row in sessions_data
        ]
        
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch sessions: {str(e)}"
        )


@router.get("/job-status/{job_id}")
async def job_status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)

    if result.state == "PENDING":
        status = "PENDING"
        return {"job_id": job_id, "status": status}

    if result.state in {"STARTED", "PROGRESS", "RETRY"}:
        status = "PROCESSING"
        meta: Optional[dict] = None
        try:
            meta = dict(result.info) if isinstance(result.info, dict) else None
        except Exception:
            meta = None
        payload: Dict[str, Any] = {"job_id": job_id, "status": status}
        if meta:
            payload["meta"] = meta
        return payload

    if result.state == "SUCCESS":
        return {"job_id": job_id, "status": "SUCCESS", "result": result.result}

    error_message = str(result.result)
    return {"job_id": job_id, "status": "FAILED", "error": error_message}


@router.get("/download/{session_id}")
async def download_cleaned_data(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Download the cleaned version of the dataset if it exists, otherwise the original.
    """
    cleaned_file_path = os.path.join(settings.UPLOAD_DIR, f"{session_id}_cleaned.csv")
    
    if os.path.exists(cleaned_file_path):
        return FileResponse(
            path=cleaned_file_path,
            filename=f"cleaned_{session_id}.csv",
            media_type="text/csv"
        )
    
    # Fallback to original
    try:
        session_uuid = UUID(session_id)
        result = await db.execute(select(Dataset).where(Dataset.id == session_uuid))
        dataset = result.scalar_one_or_none()
        
        if dataset and os.path.exists(dataset.file_path):
            return FileResponse(
                path=dataset.file_path,
                filename=dataset.original_filename,
                media_type="text/csv"
            )
    except ValueError:
        pass # Not a UUID, check temp_data for original {session_id}.csv
    
    original_file_path = os.path.join(settings.UPLOAD_DIR, f"{session_id}.csv")
    if os.path.exists(original_file_path):
        return FileResponse(
            path=original_file_path,
            filename=f"original_{session_id}.csv",
            media_type="text/csv"
        )
    
    raise HTTPException(status_code=404, detail="Dataset file not found.")
