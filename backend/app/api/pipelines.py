"""
# Architect: Meet Kumar
# InsightAI - Cleaning Pipeline Endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.user import User
from app.models.dataset import Dataset
from app.models.cleaning_pipeline import CleaningPipeline
from app.api.auth import get_current_active_user
from app.api.schemas import (
    PipelineCreate,
    PipelineUpdate,
    PipelineResponse
)

router = APIRouter()


@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(
    dataset_id: Optional[str] = None,
    is_template: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's cleaning pipelines."""
    query = select(CleaningPipeline).where(CleaningPipeline.user_id == current_user.id)
    
    if dataset_id:
        query = query.where(CleaningPipeline.dataset_id == dataset_id)
    
    if is_template is not None:
        query = query.where(CleaningPipeline.is_template == is_template)
    
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # Get paginated results
    query = query.order_by(desc(CleaningPipeline.updated_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    pipelines = result.scalars().all()
    
    return {
        "items": [PipelineResponse.model_validate(p) for p in pipelines],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/templates", response_model=List[PipelineResponse])
async def list_public_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List public pipeline templates."""
    query = select(CleaningPipeline).where(
        CleaningPipeline.is_template == True,
        CleaningPipeline.is_public == True
    )
    
    query = query.order_by(desc(CleaningPipeline.usage_count))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    pipelines = result.scalars().all()
    
    return [PipelineResponse.model_validate(p) for p in pipelines]


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific pipeline."""
    result = await db.execute(
        select(CleaningPipeline).where(
            CleaningPipeline.id == pipeline_id,
            CleaningPipeline.user_id == current_user.id
        )
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    return PipelineResponse.model_validate(pipeline)


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline_data: PipelineCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new cleaning pipeline."""
    # Verify dataset if provided
    if pipeline_data.dataset_id:
        result = await db.execute(
            select(Dataset).where(
                Dataset.id == pipeline_data.dataset_id,
                Dataset.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
    
    # Create pipeline
    pipeline = CleaningPipeline(
        user_id=current_user.id,
        dataset_id=pipeline_data.dataset_id,
        name=pipeline_data.name,
        description=pipeline_data.description,
        steps=pipeline_data.steps,
        is_template=pipeline_data.is_template,
    )
    
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    
    return PipelineResponse.model_validate(pipeline)


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: str,
    pipeline_data: PipelineUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a pipeline."""
    result = await db.execute(
        select(CleaningPipeline).where(
            CleaningPipeline.id == pipeline_id,
            CleaningPipeline.user_id == current_user.id
        )
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    # Update fields
    if pipeline_data.name is not None:
        pipeline.name = pipeline_data.name
    
    if pipeline_data.description is not None:
        pipeline.description = pipeline_data.description
    
    if pipeline_data.steps is not None:
        pipeline.steps = pipeline_data.steps
    
    await db.commit()
    await db.refresh(pipeline)
    
    return PipelineResponse.model_validate(pipeline)


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a pipeline."""
    result = await db.execute(
        select(CleaningPipeline).where(
            CleaningPipeline.id == pipeline_id,
            CleaningPipeline.user_id == current_user.id
        )
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    await db.delete(pipeline)
    await db.commit()
    
    return None


@router.post("/{pipeline_id}/apply")
async def apply_pipeline(
    pipeline_id: str,
    target_dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply a pipeline to a dataset."""
    # Get pipeline
    result = await db.execute(
        select(CleaningPipeline).where(
            CleaningPipeline.id == pipeline_id,
            CleaningPipeline.user_id == current_user.id
        )
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    # Get target dataset
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == target_dataset_id,
            Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target dataset not found"
        )
    
    # Increment usage count
    pipeline.usage_count += 1
    await db.commit()
    
    # TODO: Trigger async task to apply pipeline
    # For now, return success
    return {
        "message": "Pipeline applied successfully",
        "pipeline_id": pipeline_id,
        "dataset_id": target_dataset_id,
        "steps_applied": len(pipeline.steps or [])
    }


@router.post("/{pipeline_id}/duplicate", response_model=PipelineResponse)
async def duplicate_pipeline(
    pipeline_id: str,
    new_name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing pipeline."""
    result = await db.execute(
        select(CleaningPipeline).where(
            CleaningPipeline.id == pipeline_id,
            CleaningPipeline.user_id == current_user.id
        )
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    # Create duplicate
    new_pipeline = CleaningPipeline(
        user_id=current_user.id,
        dataset_id=original.dataset_id,
        name=new_name or f"{original.name} (Copy)",
        description=original.description,
        steps=original.steps,
        is_template=False,
    )
    
    db.add(new_pipeline)
    await db.commit()
    await db.refresh(new_pipeline)
    
    return PipelineResponse.model_validate(new_pipeline)


@router.post("/{pipeline_id}/steps")
async def add_pipeline_step(
    pipeline_id: str,
    operation: str,
    params: dict,
    order: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a step to a pipeline."""
    result = await db.execute(
        select(CleaningPipeline).where(
            CleaningPipeline.id == pipeline_id,
            CleaningPipeline.user_id == current_user.id
        )
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    step = pipeline.add_step(operation, params, order)
    await db.commit()
    
    return {
        "message": "Step added successfully",
        "step": step
    }


@router.delete("/{pipeline_id}/steps/{step_id}")
async def remove_pipeline_step(
    pipeline_id: str,
    step_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a step from a pipeline."""
    result = await db.execute(
        select(CleaningPipeline).where(
            CleaningPipeline.id == pipeline_id,
            CleaningPipeline.user_id == current_user.id
        )
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    pipeline.remove_step(step_id)
    await db.commit()
    
    return {"message": "Step removed successfully"}
