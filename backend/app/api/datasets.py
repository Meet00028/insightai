"""
# Architect: Meet Kumar
# InsightAI - Dataset Endpoints
"""

import os
import uuid
import aiofiles
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.dataset import Dataset, DatasetStatus
from app.api.auth import get_current_active_user
from app.api.schemas import (
    DatasetResponse,
    DatasetListResponse,
    DatasetPreviewResponse,
    UploadResponse
)
from app.core.celery_config import celery_app

router = APIRouter()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's datasets with pagination."""
    # Build query
    query = select(Dataset).where(Dataset.user_id == current_user.id)
    
    if status:
        try:
            status_enum = DatasetStatus(status)
            query = query.where(Dataset.status == status_enum)
        except ValueError:
            pass
    
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # Get paginated results
    query = query.order_by(desc(Dataset.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    datasets = result.scalars().all()
    
    return DatasetListResponse(
        items=[DatasetResponse.model_validate(d) for d in datasets],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific dataset."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return DatasetResponse.model_validate(dataset)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new dataset file."""
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}.csv"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    try:
        # Save file
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / 1024 / 1024:.1f} MB"
            )
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create dataset record
        dataset = Dataset(
            user_id=current_user.id,
            name=name or file.filename.replace('.csv', ''),
            file_path=file_path,
            original_filename=file.filename,
            file_size=file_size,
            status=DatasetStatus.PENDING,
        )
        
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        
        # Update user's dataset count
        current_user.datasets_count += 1
        current_user.storage_used_bytes += file_size
        await db.commit()
        
        # Enqueue processing task
        task = celery_app.send_task(
            "app.services.tasks.process_dataset",
            args=[str(dataset.id), file_path],
            queue="data_processing"
        )
        
        # Update dataset with task ID
        dataset.status = DatasetStatus.PROCESSING
        await db.commit()
        
        return UploadResponse(
            task_id=task.id,
            dataset_id=str(dataset.id),
            message="File uploaded successfully. Processing started.",
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if it was created
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def preview_dataset(
    dataset_id: str,
    rows: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a preview of dataset data."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
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
    
    try:
        import pandas as pd
        
        # Read CSV
        df = pd.read_csv(dataset.file_path, nrows=rows)
        
        # Convert to dict
        data = df.fillna('').to_dict('records')
        
        return DatasetPreviewResponse(
            columns=list(df.columns),
            data=data,
            total_rows=dataset.row_count or 0,
            preview_rows=len(data)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview dataset: {str(e)}"
        )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a dataset."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Delete file
    try:
        if os.path.exists(dataset.file_path):
            os.remove(dataset.file_path)
        if dataset.cleaned_file_path and os.path.exists(dataset.cleaned_file_path):
            os.remove(dataset.cleaned_file_path)
    except Exception:
        pass  # Continue even if file deletion fails
    
    # Update user stats
    current_user.datasets_count -= 1
    current_user.storage_used_bytes -= dataset.file_size
    if current_user.storage_used_bytes < 0:
        current_user.storage_used_bytes = 0
    
    # Delete record
    await db.delete(dataset)
    await db.commit()
    
    return None


@router.get("/{dataset_id}/status")
async def get_dataset_status(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dataset processing status."""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return {
        "dataset_id": str(dataset.id),
        "status": dataset.status.value,
        "progress": 100 if dataset.status == DatasetStatus.COMPLETED else None,
        "error_message": dataset.error_message,
        "health_score": dataset.data_health_score,
    }
